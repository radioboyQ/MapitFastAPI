import base64
import json.decoder
import os
from csv import DictReader
from datetime import datetime
import io
import logging
from pathlib import Path
import pickle
from pprint import pprint
import sys
from time import sleep

import click
import requests
import rich.status
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.status import Status
from rich.table import Table

from MapItFastLib.Projects import Project
from MapItFastLib.Points import Points
from MapItFastLib.Pictures import Picture
from MapItFastLib import Utils


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command("SearchPoints", context_settings=CONTEXT_SETTINGS, help=f"")
@click.option("--refresh-cache", "-r", type=click.BOOL, default=False, help="Force a cache refresh", is_flag=True)
@click.option("--username", default=lambda: os.environ.get("AGTERRAUSER", ""))
@click.option("--password", hide_input=True, default=lambda: os.environ.get("AGTERRAPASS", ""), show_default=False)
@click.option("--cache-path", type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True,
                                              readable=True, resolve_path=True), callback=Utils.validate_cache_folder,
              default="/tmp/agterra/cache/")
@click.option("--picture-path", type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True,
                                                readable=True, resolve_path=True), callback=Utils.validate_cache_folder,
              default="/tmp/agterra/pictures/")
@click.option("--all-years", "-a", type=click.BOOL, is_flag=True, default=False,
              help="Search of all years, not just the current year")
@click.option("--search-term", "-s", help="Search term for pin in a project", prompt=True, type=click.STRING)
@click.pass_context
def main(ctx, refresh_cache, password, username, cache_path, picture_path, all_years, search_term):
    """
    Application to search all points in every project
    """
    # Create the console
    console = Console()
    # Should we show off the good code that's been written
    show_off_mode = True
    project_pickle_path = Path(os.path.join(cache_path, "project_cache.pickle.py"))
    picture_pickle_path = Path(os.path.join(picture_path, "picture_cache.pickle.py"))
    point_pickle_path = Path(os.path.join(cache_path, "")) # point_cache.pickle.py
    project_folder_pickle_path = Path(os.path.join(cache_path, "project_folder_cache.pickle.py"))
    use_cache = True
    project_id_search_list = list()
    proj_obj_dict = dict()

    # proj_folder_obj_dict = Utils.AgTerraWrapper.get_project_folders(username=username, password=password, console=console,
    #                                                          cache_path=cache_path, show_off_mode=show_off_mode)

    # for proj_folder in proj_folder_list:
    #     # Filter by year. If folder doesn't include current year in title, skip it unless specifically asked for
    #     if not all_years and "2021" in proj_folder.FolderName:
    #         console.log(proj_folder.FolderName)

    # points_obj_list = Utils.AgTerraWrapper.get_points(username=username, password=password, console=console,
    #                                                   project_id=project_id)

    # Create output Table
    table = Table(title="Pins in Projects", show_lines=True)
    table.add_column("Pin Name", justify="left", style="cyan", no_wrap=True)
    table.add_column("Project Name", style="magenta", justify="center")
    table.add_column("Last Updated Time", justify="right", style="green")

    proj_obj_list = Utils.AgTerraWrapper.get_projects(username=username, password=password, console=console,
                                                      cache_path=project_pickle_path, show_off_mode=show_off_mode)
    # Get all projects and conduct any filtering
    for proj_obj in proj_obj_list:
        # Make a dict of IDs and objects
        # {project_id: project_object
        proj_obj_dict.update({proj_obj.ProjectId: proj_obj})
        # Search for projects with 2021 in the title
        if not all_years and "2021" in proj_obj.Title:
            # console.log(proj_obj.Title)
            project_id_search_list.append(proj_obj.ProjectId)
        elif all_years:
            project_id_search_list.append(proj_obj.ProjectId)
    with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}",
                  console=console, transient=True) as progress:
        overall_task = progress.add_task(f"[green]Project Points Loaded", total=len(project_id_search_list))

        for proj_id in project_id_search_list:
            progress.update(overall_task, advance=1)
            proj_points = Utils.AgTerraWrapper.get_points(username=username, password=password, console=progress.console,
                                                          cache_path=point_pickle_path, show_off_mode=show_off_mode,
                                                          project_id=proj_id, refresh_cache=refresh_cache)

            for point in proj_points:
                try:
                    if point.Title is not None and search_term in point.Title:
                        proj_obj = proj_obj_dict.get(point.ProjectId)
                        if point.ItemTime.date() == datetime.today().date():
                            table.add_row(point.Title, proj_obj.Title,
                                          f"Today at {point.ItemTime.time().strftime('%H:%M:%S')}")
                        else:
                            table.add_row(point.Title, proj_obj.Title,
                                          point.ItemTime.strftime("%m/%d/%Y, %H:%M:%S"))
                except AttributeError:
                    console.log(f"Project ID that failed: {point.ProjectId}")
                    console.log(vars(point))
                    sys.exit(1)

    console.log(table)







if __name__ == "__main__":
    main()