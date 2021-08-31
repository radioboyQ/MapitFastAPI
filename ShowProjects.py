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


@click.command("Show Projects", context_settings=CONTEXT_SETTINGS, help=f"Easy user interface for selecting a specifc "
                                                                        f"AgTerra project")
@click.option("--refresh-cache", "-r", type=click.BOOL, default=False, help="Force a cache refresh", is_flag=True)
@click.option("--username", default=lambda: os.environ.get("AGTERRAUSER", ""))
@click.option("--password", hide_input=True, default=lambda: os.environ.get("AGTERRAPASS", ""), show_default=False)
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
    project_id_dst = 641

    # Each element in the list will have dictionary like this:
    # {Title, Desc, Lat, Long, IconID}
    final_points_list = list()
    # Set duplicate_point flag
    duplicate_point = False

    icon_id_dict = {71: "tractor_marker", 3: "point", 60: "red_point"}

    project_list = Utils.AgTerraWrapper.get_projects(username=username, password=password, console=console,
                                                     cache_path=project_pickle_path, show_off_mode=show_off_mode)

    table = Table(title="Porjects With ID", show_lines=True)
    table.add_column("Project Title", justify="left", style="cyan", no_wrap=True)
    table.add_column("Project ID", style="magenta", justify="center")

    for i in project_list:
        if "scott" in i.Title.lower():
            table.add_row(i.Title, str(i.ProjectId))

    console.log(table)


if __name__ == "__main__":
    main()