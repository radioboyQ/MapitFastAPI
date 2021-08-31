from csv import DictReader
from datetime import datetime
import logging
from pprint import pprint
import sys
from time import sleep

import click
import requests
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Confirm, Prompt
from rich.progress import Progress
from rich.status import Status
from tabulate import tabulate

from MapItFastLib.Projects import Project
from MapItFastLib.Points import Points

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command("AgTerraImport", context_settings=CONTEXT_SETTINGS, help=f"CSV Importer for AgTerra")
@click.option("--csv", "csv_file", type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True,
                                                   allow_dash=True), required=True)
@click.option("--project-name", type=click.STRING, required=True)
@click.option("--username", default=lambda: os.environ.get("AGTERRAUSER", ""))
@click.option("--password", hide_input=True, default=lambda: os.environ.get("AGTERRAPASS", ""), show_default=False)
@click.option("--project-name", required=True, type=click.STRING)
@click.pass_context
def main(ctx, csv_file, project_name, username, password):
    """
    Same as last script, but this time check if the points exist first, and skip it if there is an exact LAT & LONG
    match
    """

    # List of projects
    proj_obj_list = list()
    # If the given project is found, set to True
    proj_title_found = False

    # Create the console
    console = Console()

    debug = False
    show_off_mode = False

    FORMAT = "%(message)s"
    if debug:
        # noinspection PyArgumentList
        logging.basicConfig(level="DEBUG", format=FORMAT, datefmt="[%X]",
                            handlers=[RichHandler(console=console, rich_tracebacks=True)])

    else:
        # noinspection PyArgumentList
        logging.basicConfig(level="WARNING", format=FORMAT, datefmt="[%X]",
                            handlers=[RichHandler(console=console, rich_tracebacks=True)])

    # csv_dict = get_csv_coordinates(csv_file)

    with requests.Session() as sess:
        sess.auth = (username, password)
        with Status("[magenta]Connecting", console=console, spinner='arrow3') as status:
            status.update(f"Requesting Project List From Server")
            if show_off_mode:
                sleep(0.7)

            proj_obj_list = get_projects(sess=sess)

            # Look for project by title
            for proj in proj_obj_list:
                if proj.Title == project_name:
                    # Project found, we can move on
                    # Save the object for later
                    project_by_name = proj
                    console.log(f"Project {project_name} has been found")
                    proj_title_found = True

            # If project not found, print error and exit
            if not proj_title_found:
                console.log(f"Project '{project_name}' wasn't found as an option")
                for proj in proj_obj_list:
                    console.log(f"{proj.Title}")
                sys.exit(1)

            # Get existing points
            points_obj_list = get_points(sess=sess, console=console, status=status,
                                         projectID=project_by_name.ProjectId)

            status.update(f"Opening CSV File")
            if show_off_mode:
                sleep(2)
            with open(csv_file, 'r') as f:
                csv_dict = DictReader(f)

                for row_dict in csv_dict:
                    new_lat = float(row_dict.get("Latitude"))
                    new_long = float(row_dict.get("Longitude"))

                    # Loop over every existing point for each row in the CSV
                    skip_point = False
                    for point in points_obj_list:
                        # If both coords match, error out, otherwise continue to posting the new points
                        if new_lat == point.Latitude and new_long == point.Longitude:
                            console.log(f"Looks like the points at Latitude {point.Latitude} and Longitude "
                                        f"{point.Longitude} already exists")
                            skip_point = True
                            break

                    if not skip_point:
                        if "Title" in row_dict:
                            # If the title column exists, append it to the request
                            # console.log(f"Found Title!")
                            title = row_dict.get("Title")
                        else:
                            title = ""

                        if "Description" in row_dict:
                            description = row_dict.get("Description")
                        else:
                            description = ""

                        console.log(f"Adding Lat: {new_lat} and Long: {new_long}")
                        # post_coordinates(sess=sess, console=console, status=status, lat=new_lat, long=new_long,
                        #                  projectID=project_by_name.ProjectId, title=title, description=description)
                        if show_off_mode:
                            sleep(1)




            # for point in points_obj_list:
            #     console.log(f"Latitude: {point.Latitude}\nLongitude: {point.Longitude}")


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


def post_coordinates(sess: requests.Session, console: Console, status: Status, lat: float, long: float, projectID: int,
                     title: str, description: str,
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


def get_csv_coordinates(path: str):
    """
    Quick function to validate the lat,long,title columns of the CSV
    Also return the CSV to the user
    """
    csv_dict = dict()
    with open(path, 'r') as f:
        csv_dict_tmp = DictReader(f)
        for i in csv_dict_tmp:
            csv_dict.update(i)

        # ToDo: Error trap for the correct column names
        # if "Longitude" not in csv_dict:
        #     logging.error(f"CSV Error! Longitude column not found!")
        #     sys.exit(1)
        # if "Latitude" not in csv_dict:
        #     logging.error(f"CSV Error! Latitude column not found!")
        #     sys.exit(1)
        # if "Title" not in csv_dict:
        #     logging.warning(f"CSV Warning! Title not found! ")
    return csv_dict


def get_projects(sess: requests.Session, url: str = f"https://mapitfast.agterra.com/api/Projects"):
    """
    Helper function to get projects list
    """
    # Get the folder list
    raw_resp = get_url(sess=sess, url=url)

    json_data = raw_resp.json()

    # Turn each project from JSON into an object we can actually use
    proj_obj_list = list()
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