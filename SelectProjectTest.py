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


@click.command("SelectProject", context_settings=CONTEXT_SETTINGS, help=f"Easy user interface for selecting a specifc "
                                                                        f"AgTerra project")
@click.option("--refresh-cache", "-r", type=click.BOOL, default=False, help="Force a cache refresh", is_flag=True)
@click.option("--username", default=lambda: os.environ.get("AGTERRAUSER", ""))
@click.option("--password", hide_input=True, default=lambda: os.environ.get("AGTERRAPASS", ""), show_default=False)
@click.option("--cache-path", type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True,
                                              readable=True, resolve_path=True), callback=Utils.validate_cache_folder,
              default="/tmp/agterra/cache/")
@click.option("--picture-path", type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True,
                                                readable=True, resolve_path=True), callback=Utils.validate_cache_folder,
              default="/tmp/agterra/pictures/")
@click.pass_context
def main(ctx, refresh_cache, password, username, cache_path, picture_path):
    """
    Test for Rich to select an AgTerra project
    """
    # Create the console
    console = Console()
    # Should we show off the good code that's been written
    show_off_mode = True
    project_pickle_path = Path(os.path.join(cache_path, "project_cache.pickle.py"))
    picture_pickle_path = Path(os.path.join(cache_path, "picture_cache.pickle.py"))
    project_folder_pickle_path = Path(os.path.join(cache_path, "project_folder_cache.pickle.py"))
    use_cache = True

    # proj_obj_list = Utils.AgTerraWrapper.get_projects(username=username, password=password, console=console,
    #                                       cache_path=project_pickle_path, show_off_mode=show_off_mode,
    #                                       use_pickle_cache=use_cache, refresh_cache=refresh_cache)
    #
    # table = Table(title="AgTerra Projects")
    #
    # table.add_column("Project Folder", justify="right", style="cyan", no_wrap=True)
    # table.add_column("Project Name", style="magenta")
    # table.add_column("Project Number", justify="right", style="green")
    #
    # for proj_obj in proj_obj_list:
    #     if not proj_obj.Title.startswith("Archive"):
    #         table.add_row(str(proj_obj.ProjectFolderId), str(proj_obj.Title), str(proj_obj.ProjectId))

    # console.print(table)

    # console.log(Utils.AgTerraWrapper.get_project_folders(username=username, password=password, console=console,
    #                                       cache_path=project_pickle_path, show_off_mode=show_off_mode,
    #                                       use_pickle_cache=use_cache, refresh_cache=refresh_cache))
    #
    # proj_folder_obj = Utils.AgTerraWrapper.get_project_folders(username=username, password=password, console=console,
    #                                       cache_path=project_pickle_path, show_off_mode=show_off_mode,
    #                                       use_pickle_cache=use_cache, refresh_cache=refresh_cache)
    #
    # for i in proj_folder_obj:
    #     print(type(i))









if __name__ == "__main__":
    main()
