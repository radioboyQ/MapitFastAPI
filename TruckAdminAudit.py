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
from rich.progress import Progress, BarColumn
from rich.status import Status
from tabulate import tabulate

from MapItFastLib.Projects import Project
from MapItFastLib.Points import Points

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command("CompareTrucks", context_settings=CONTEXT_SETTINGS, help=f"CSV Importer for AgTerra")
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
    # Final dictionary
    final_dict = dict()

    # Create the console
    console = Console()

    debug = False
    show_off_mode = True

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

    # with Status("[magenta]Connecting", console=console, spinner='arrow3') as status:
    #     if show_off_mode:
    #         sleep(0.6)
    with requests.Session() as admin_sess:
        admin_sess.auth = (username, password)
        console.log(f"[magenta]Requesting Admin's project list")
        # admin_proj_obj_list = get_projects(console=console, sess=admin_sess)
        # with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}", console=console) as progress:
        #     task = progress.add_task("[green]Downloading Admin User's Projects", total=len(admin_proj_obj_list))
        #     for proj in admin_proj_obj_list:
        #         proj_points = get_points(admin_sess, console=console, projectID=proj.ProjectId)
        #         progress.update(task, advance=1)
        #
        #         point_dict_temp = dict()
        #         project_dict_temp = dict()
        #         for point in proj_points:
        #             point_dict_temp.update({point.PointId: point})
        #         project_dict_temp.update({proj.ProjectId: point_dict_temp})
        #     final_dict.update({"admin": project_dict_temp})


        # Open username list CSV
        with open("/CSV_Files/User List - AgTerra User Admin.csv", "r") as truck_list_f:
            truck_csv_dict = DictReader(truck_list_f)
            for row in truck_csv_dict:
                if row.get("User Name").startswith("Truck #"):
                    console.log(f"[blue]Attempting to log in as [green]{row.get('User Name')}")
                    truck_username = row.get("User Name")
                    # Don't judge me, I didn't make this password
                    truck_password = "Reliable1!"

                    with requests.Session() as truck_sess:
                        truck_sess.auth = (truck_username, truck_password)
                        truck_proj_obj_list = get_projects(console=console, sess=truck_sess)
                        # print('------------')
                        # print(truck_proj_obj_list)
                        # with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}", console=console) as progress:
                        #     task = progress.add_task(f"[green]Downloading {truck_username}'s Projects", total=len(truck_proj_obj_list))
                            # for proj in truck_proj_obj_list:
                            #     proj_points = get_points(truck_sess, console=console, projectID=proj.ProjectId)
                            #     progress.update(task, advance=1)
                            #
                            #     point_dict_temp = dict()
                            #     project_dict_temp = dict()
                            #     for point in proj_points:
                            #         point_dict_temp.update({point.PointId: point})
                            #     project_dict_temp.update({proj.ProjectId: point_dict_temp})
                            # final_dict.update({truck_username: project_dict_temp})

        # Write everything to a pickle



        # Compare the trucks interface to Admin's interface
        # for proj in truck_proj_obj_list:
        #     console.log(proj.Title)



def get_points(sess: requests.Session, console: Console, projectID: int, includePoints: bool = True,
               status: Status = None):
    """
    Get all exisiting points in a project
    """
    base_url = f"https://mapitfast.agterra.com/api/Points"
    resp = sess.get(base_url, params={"projectId": projectID, "includePoints": includePoints})

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
        for row in csv_dict_tmp:
            csv_dict.update(row)

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

def get_projects(console: Console, sess: requests.Session, url: str = f"https://mapitfast.agterra.com/api/Projects", status: Status = None):
    """
    Helper function to get projects list
    """
    # Get the folder list
    raw_resp = get_url(sess=sess, url=url)
    if raw_resp.status_code != 200 and raw_resp.status_code != 201:
        console.log(f"[red][!] Log in failed")
        json_data = raw_resp.json()
        console.log(f"Message: [red]{json_data.get('Message')}")

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