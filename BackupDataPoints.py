from csv import DictReader
from datetime import datetime
import logging
from pathlib import Path
import pickle
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


def main():
    """
    Get last changed time for projects

    - Check if Pickle exists
    - - If not, get projects and save to Pickle
    - Determine if Projects hold a 'last modified' time
    - - If not, get points, sort them by last modified time, check for the newest point
    - Check if the project has been modified in the last 6 months
    """

    # Create the console
    console = Console()

    # Should we show off the good code that's been written
    show_off_mode = True

    # Create the console for making fancy graphics
    console = Console()

    # Creds
    username = lambda: os.environ.get("AGTERRAUSER", "")
    password = lambda: os.environ.get("AGTERRAPASS", "")

    # Pickle Path
    pickle_path_project = Path("/tmp/agterra_project.pickle.py")
    pickle_path_points = Path("/tmp/agerra_project_points.pickle.py")
    if pickle_path_project.exists():
        console.log(f"Pickle found at {pickle_path_project}")
        projects_list = pickle.load(open(pickle_path_project, "rb"))
    else:
        # Get projects and save to pickle
        with requests.Session() as sess:
            sess.auth = (username, password)
            console.log(f"Requesting Project List From Server to Populate Pickle")
            if show_off_mode:
                sleep(0.7)
            projects_list = get_projects(console=console, sess=sess)
        if show_off_mode:
            sleep(0.5)
        console.log(f"Pickle dumped to {pickle_path_project}")
        pickle.dump(projects_list, open(pickle_path_project, "wb"))


    if pickle_path_points.exists():
        console.log(f"Points Pickle Found at {pickle_path_points}")
        points_by_project_id = pickle.load(open(pickle_path_points, "rb"))

    else:
        # Get points for each project and cache them too
        with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}",
                      console=console) as progress:

            task = progress.add_task(f"[green]Downloading Points For Existing Projects", total=len(projects_list))
            points_by_project_id = dict()
            for project in projects_list:
                # Get projects and save to pickle
                with requests.Session() as sess:
                    sess.auth = (username, password)

                    # Get all points
                    points_for_project = get_points(sess=sess, console=console, projectID=project.ProjectId)

                    # Append points by project ID to dict
                    points_by_project_id.update({project.ProjectId: points_for_project})

                    progress.update(task, advance=1)

                    pickle.dump(points_by_project_id, open(pickle_path_points, "wb"))

                    # sleep(2)

    pprint(points_by_project_id)
    # for proj_id, points in points_by_project_id.items():
    #     pprint(points)





















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