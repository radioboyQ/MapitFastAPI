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


@click.command("Creststone Copy Points To New Map", context_settings=CONTEXT_SETTINGS,
               help=f"Easy user interface for selecting a specifc "
                    f"AgTerra project")
@click.option("--refresh-cache", "-r", type=click.BOOL, default=False, help="Force a cache refresh", is_flag=True)
@click.option("--username", default=lambda: os.environ.get("AGTERRAUSER", ""), show_default=True)
@click.option("--password", hide_input=True, default=lambda: os.environ.get("AGTERRAPASS", ""), show_default=True)
@click.option("--cache-path", type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True,
                                              readable=True, resolve_path=True), callback=Utils.validate_cache_folder,
              default="/tmp/agterra/cache/")
@click.pass_context
def main(ctx, refresh_cache, password, username, cache_path):
    """
    Application to copy pictures to a new project OR copy points to a new project
    """
    console = Console()
    project_pickle_path = Path(os.path.join(cache_path, "project_cache.pickle.py"))
    show_off_mode = True

    project_id_src_list = [463, 501, 504, 509, 510, 643, 630]
    project_id_dst = 634 # ScottWorkbench 634 Prod Project: 641

    # Each element in the list will have dictionary like this:
    # {Title, Desc, Lat, Long, IconID}
    final_points_list = list()
    intermediate_list = list()
    # Set duplicate_point flag
    duplicate_point = False
    count = 0
    time_sleep = 60

    icon_id_dict = {71: "tractor_marker", 3: "point", 60: "red_point"}

    # project_list = Utils.AgTerraWrapper.get_projects(username=username, password=password, console=console,
    #                                                  cache_path=project_pickle_path, show_off_mode=show_off_mode)

    table = Table(title="Porjects With ID", show_lines=True)
    table.add_column("Project Title", justify="left", style="cyan", no_wrap=True)
    table.add_column("Project ID", style="magenta", justify="center")

    # Get the destination project's points

    dest_point_obj_list = Utils.AgTerraWrapper.get_points(username=username, password=password, console=console,
                                                          project_id=project_id_dst, cache_path=cache_path)
    for proj_id in project_id_src_list:
        points_obj_list = Utils.AgTerraWrapper.get_points(username=username, password=password, console=console,
                                                          project_id=proj_id, cache_path=cache_path)
        for point in points_obj_list:
            intermediate_list.append(point)

    console.log(len(intermediate_list))
    if len(intermediate_list) > 0 and len(dest_point_obj_list) == 0:
        # Only enter this block if the dest list is empty and the src list has at least one item it in
        dest_point_obj_list.append(intermediate_list[0])

    for src_point in intermediate_list:
        duplicate = True
        for dest_point in dest_point_obj_list:
            if dest_point.Title == src_point.Title and dest_point.Latitude == src_point.Latitude and \
                    dest_point.Longitude == src_point.Longitude:
                duplicate = True
            else:
                duplicate = False
        if not duplicate:
            dest_point_obj_list.append(src_point)

    with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}",
                  console=console) as progress:
        task = progress.add_task(f"[green]Uploading deduplicated points", total=len(dest_point_obj_list))
        for point in dest_point_obj_list:
            count += 1
            if point.IconId == 71 or point.IconId == 3:
                # Only post data if it's unchanged
                data_dict = {"ProjectID": project_id_dst, "IconID": point.IconId, "Title": point.Title,
                             "Description": point.Description, "Longitude": point.Longitude, "Latitude": point.Latitude,
                             "ItemTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "Elevation": 0}
            else:
                data_dict = {"ProjectID": project_id_dst, "IconID": 3, "Title": point.Title,
                             "Description": point.Description, "Longitude": point.Longitude, "Latitude": point.Latitude,
                             "ItemTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "Elevation": 0}

            # console.log(type(point.Latitude))
            # response_obj = Utils.AgTerraWrapper.post_points(username=username, password=password, console=console,
            #                                                 project_id=project_id_dst, data_dict=data_dict)
            # progress.update(task, advance=1)
            # if count % 100 == 0:
            #     console.log(f"Sleeping for {time_sleep} seconds so the server can catch up")
            #     sleep(time_sleep)



if __name__ == "__main__":
    main()
