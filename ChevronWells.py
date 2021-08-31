from csv import DictReader
from datetime import datetime
import logging
from pprint import pprint
import random
import sys
from time import sleep

import click
import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, BarColumn
from rich.status import Status
from rich.table import Table

from MapItFastLib.Projects import Project
from MapItFastLib.Points import Points

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command("AgTerraImport", context_settings=CONTEXT_SETTINGS, help=f"CSV Importer for AgTerra")
@click.option("--csv", "csv_file", type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True,
                                                   allow_dash=True), required=True)
@click.option("--username", default=lambda: os.environ.get("AGTERRAUSER", ""))
@click.option("--password", hide_input=True, default=lambda: os.environ.get("AGTERRAPASS", ""), show_default=False)
@click.option("--no-testing", is_flag=True, default=False, help="Use the testing project names")
@click.pass_context
def main(ctx, csv_file, username, password, no_testing):
    """
    Special one off case for Cheveron
    Report center starts with a 4, add to project priority 3
    Report center starts with 8, add to project Batteries in Progress
    """
    latitude_col_name = "LATN83"
    longitude_col_name = "LONGN83"
    title_col_name = "LEASE NAME"

    # Create the console
    console = Console()
    # Add several time delays to show off how great my code is. 10/10 ego
    show_off_mode = True

    if no_testing:
        confirm_response = click.confirm(f"Using the real project, are you SURE?", abort=True)
        console.log(f"Alright, using the real deal")
        priority_3_proj_name = "2021 - Noble/Chevron - Priority 3"
        batteries_in_prog_proj_name = "2021 - Noble/Chevron Batteries In Progress"
    else:
        console.log(f"We're using the testing projects")
        priority_3_proj_name = "2021 - Noble/Chevron - Priority 3 - ScottTesting"
        batteries_in_prog_proj_name = "2021 - Noble/Chevron Batteries In Progress - ScottTesting"

    priority_3_row_list = list()
    battery_in_prog_row_list = list()

    # Load CSV
    csv_row_list = load_csv(console=console, csv_path=csv_file)
    # Parse the data
    for row in csv_row_list:
        # Only allow jobs that need to be scheduled or are awaiting scheduling
        if row.get("JOB STATUS") == "SCHEDULED" or row.get("JOB STATUS") == "AWAITING SCHEDULE":
            # Split jobs based on REPORT CENTER number
            # 4 is priority_3_proj_name
            if row.get("REPORT CENTER").startswith("4"):
                priority_3_row_list.append(row)
            elif row.get("REPORT CENTER").startswith("8"):
                battery_in_prog_row_list.append(row)
            else:
                console.log(f'Report Center {row.get("REPORT CENTER")} is a weird number I don\'t know how to deal '
                            f'with')

    table = Table(title="Well & Battery Counts", title_justify="center")
    table.add_column("Location Type", justify="center", style="white")
    table.add_column("Count", justify="center", style="green")

    table.add_row("Priority 3 Well Count", str(len(priority_3_row_list)))
    table.add_row("Battery Count", str(len(battery_in_prog_row_list)))
    console.print(table)

    # Check the points in a given project
    with requests.Session() as sess:
        sess.auth = (username, password)
        with Status("[magenta]Requesting Project List From Server", console=console, spinner='arrow3') as status:
            if show_off_mode:
                sleep(0.7)

            projects_list = get_projects(sess=sess)

            # Look for project by title
            for proj in projects_list:
                if proj.Title == priority_3_proj_name:
                    # Project found, we can move on
                    # Save the object for later
                    priority_3_project_by_name = proj
                    console.log(f"Project '{priority_3_proj_name}' has been found")

                if proj.Title == batteries_in_prog_proj_name:
                    # Project found, we can move on
                    # Save the object for later
                    batteries_project_by_name = proj
                    console.log(f"Project '{batteries_in_prog_proj_name}' has been found")

            # console.log(priority_3_project_by_name.ProjectId)
            # console.log(batteries_project_by_name.ProjectId)

        # ToDo: Get existing points for project
        # Start with Pri3 points
        with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}",
                      console=console) as progress:
            points_pri_3_obj_list = get_points(sess=sess, console=console, status=status,
                                         projectID=priority_3_project_by_name.ProjectId)
            pri_3_post_list = list()
            task = progress.add_task(f"[green]Deduplicating Points For Priority 3 Wells", total=len(priority_3_row_list))
            for new_row in priority_3_row_list:
                new_lat = float(new_row.get(latitude_col_name))
                new_long = float(new_row.get(longitude_col_name))

                skip_point = False
                for existing_coords in points_pri_3_obj_list:
                    if new_lat == existing_coords.Latitude and new_long == existing_coords.Longitude:
                        # The point exists, don't add it
                        progress.console.log(f"{new_row.get(title_col_name)} already exists.")
                        skip_point = True
                        break
                progress.update(task, advance=1)
                if show_off_mode:
                    sleep(0.1)
                # If the point isn't a duplicate, add it
                if not skip_point:
                    title = new_row.get(title_col_name)
                    # console.log(f"Adding Lat: {new_lat} and Long: {new_long} with Title {title}")
                    #ToDo: Add to map
                    pri_3_post_list.append({"lat": new_lat, "long": new_long, "title":title})

            points_battery_obj_list = get_points(sess=sess, console=console, status=status,
                                               projectID=batteries_project_by_name.ProjectId)

            battery_post_list = list()
            task = progress.add_task(f"[green]Deduplicating Points For Batteries", total=len(battery_in_prog_row_list))
            for new_row in battery_in_prog_row_list:
                new_lat = float(new_row.get(latitude_col_name))
                new_long = float(new_row.get(longitude_col_name))

                skip_point = False
                for existing_coords in points_battery_obj_list:
                    if new_lat == existing_coords.Latitude and new_long == existing_coords.Longitude:
                        # The point exists, don't add it
                        progress.console.log(f"{new_row.get(title_col_name)} already exists.")
                        skip_point = True
                        break
                progress.update(task, advance=1)
                if show_off_mode:
                    sleep(0.1)
                # If the point isn't a duplicate, add it
                if not skip_point:
                    title = new_row.get(title_col_name)
                    battery_post_list.append({"lat": new_lat, "long": new_long, "title": title})

            # Upload all the Pri3 Points
            task = progress.add_task(f"[green]Uploading points for Priority 3 Wells", total=len(pri_3_post_list))
            for point_dict in pri_3_post_list:
                progress.update(task_id=task, advance=1)
                post_coordinates(sess=sess, console=console, lat=point_dict.get("lat"), long=point_dict.get("long"),
                                 projectID=priority_3_project_by_name.ProjectId, title=point_dict.get("title"))

            # Upload all Batteries Points
            task = progress.add_task(f"[green]Uploading points for Batteries",
                                     total=len(battery_post_list))
            for battery_dict in battery_post_list:
                progress.update(task_id=task, advance=1)
                post_coordinates(sess=sess, console=console, lat=battery_dict.get("lat"), long=battery_dict.get("long"),
                                 projectID=batteries_project_by_name.ProjectId, title=battery_dict.get("title"))









def post_coordinates(sess: requests.Session, console: Console, lat: float, long: float, projectID: int, title: str, description: str = "",
                     elevation: int = 0, iconid: int = 3):
    """
    Function to post the variables to the API
    """
    base_url = f"https://mapitfast.agterra.com/api/Points"
    post_data_dict = {"ProjectID": projectID,
                      "IconId": iconid,
                      "Title": title,
                      "Description": description,
                      "ItemTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                      "Latitude": lat,
                      "Longitude": long,
                      "Elevation": elevation}

    resp = sess.post(base_url, data=post_data_dict)

    if resp.status_code == 201:
        # console.log(f"Added coordinates to project")
        pass # console.log(f"It worked!")
    else:
        console.log(f"{resp.json()}")
        console.log(f"Something went wrong, check error code {resp.status_code}")

def get_points(sess: requests.Session, console: Console, status: Status, projectID: int):
    """
    Get all exisiting points in a project
    """
    base_url = f"https://mapitfast.agterra.com/api/Points"
    resp = sess.get(base_url, params={"projectId": projectID})

    points_obj_list = list()
    for raw_resp in resp.json():
        points_obj_list.append(Points(raw_data=raw_resp))
    return points_obj_list

def load_csv(console:Console, csv_path: str):
    """
    Generic function to load CSV files into a list of dictionaries
    """
    csv_row_list = list()
    with open(csv_path, 'r', encoding = "utf-8-sig") as csv_f:
        dict_reader = DictReader(csv_f)
        for row in dict_reader:
            csv_row_list.append(row)
    return csv_row_list

def get_projects(sess: requests.Session, url: str = f"https://mapitfast.agterra.com/api/Projects"):
    """
    Helper function to get projects list
    """
    proj_obj_list = list()
    # Get the folder list
    raw_resp = get_url(sess=sess, url=url)

    json_data = raw_resp.json()

    # Turn each project from JSON into an object we can actually use
    for raw_proj_dict in json_data:
        proj_obj_list.append(Project(raw_data=raw_proj_dict))
    return proj_obj_list

def get_url(sess: requests.Session, url: str):
    """
    Basic function to make getting various URLs easier
    """
    return sess.get(url=url)

if __name__ == "__main__":
    main()