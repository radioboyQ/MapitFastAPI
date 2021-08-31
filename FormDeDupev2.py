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
    Deduplicate forms on Strider
    - Get Forms from website
    - Store in pickle
    - Compare every entry against every other entry
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

    duplicate_record_counter_dict = dict()

    # Pickle Path
    pickle_path_strider = Path("/tmp/agterra_strider_form.pickle.py")

    if pickle_path_strider.exists():
        console.log(f"Pickle found at {pickle_path_strider}")
        raw_forms_resp = pickle.load(open(pickle_path_strider, "rb"))
    else:
        # Get projects and save to pickle
        with requests.Session() as sess:
            sess.auth = (username, password)
            console.log(f"Requesting Forms From Server to Populate Pickle")
            if show_off_mode:
                sleep(0.7)
            raw_forms_resp = get_forms(console=console, sess=sess)
        if show_off_mode:
            sleep(0.5)
        console.log(f"Pickle dumped to {pickle_path_strider}")
        pickle.dump(raw_forms_resp, open(pickle_path_strider, "wb"))


    # Set up ProgressBar
    with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}",
                  console=console, transient=False) as progress:

        # BEGIN DEDUPE PROCESS #
        for form_name, form_data_list in raw_forms_resp.items():
            overall_task = progress.add_task(f"[green]DeDupe Progress", total=len(form_data_list))
            # Start with the general form, for sanity
            if form_name == "General_Record_2020v2.0":
                progress.update(overall_task, advance=1)
                for golden_form_submitted in form_data_list:
                    check_against_all_others(progress_bar=progress, golden_form=golden_form_submitted,
                                             form_data_list=form_data_list, prog_bar_task=overall_task)
            #         break
            # break


def check_against_all_others(progress_bar: Progress, prog_bar_task: int, golden_form: dict, form_data_list: list):
    """
    Function to check if golden_form is duplicated anywhere else
    - EXCLUDE SOME FIELDS LIKE _ID
    - Maintain list of duplicated form IDs for quick look ups
    :return: A dictionary with the golden form as a key, value is a list of forms which are duplicated against the golden one
    """
    duplicate_form_ids = list()
    final_dict = dict() # {GoldenFormID: ListOfDuplicateForms}
    field_skip_list = ["_ID"]

    # single_form_dedupe_task = progress_bar.add_task(f"[magenta]Single Form DeDupe", total=len(form_data_list))

    for count, test_form in enumerate(form_data_list):
        # Reset if the form is a Match or not each loop
        match = True
        if test_form.get("_ID") == golden_form.get("_ID"):
            # The golden form, we can skip deduplicating this one
            pass # progress_bar.console.log(f"Golden Form")
        else:
            # Not the golden form
            for form_field_key, form_field_value in test_form.items():
                if form_field_key in field_skip_list:
                    pass
                else:
                    if golden_form.get(form_field_key) == test_form.get(form_field_key):
                        # Match!
                        pass
                    else:
                        # No match!
                        match = False
                        break

    progress_bar.update(prog_bar_task, advance=1)



def get_forms(console: Console, sess: requests.Session, form_id: str = "General_Record_2020v2.0"):
    """
    Method to get every form for a given FormID
    """
    raw_resp = get_url(url=f"https://forms.agterra.com/api/{form_id}/GetAll/0", sess=sess)

    if raw_resp.status_code != 200:
        console.log(f"[red] Something went wrong, we got status [white]{raw_resp.status_code}")
        json_data = raw_resp.json()
        console.log(f"Message Data: {json_data}")

    json_data = raw_resp.json()

    return json_data


def get_url(sess: requests.Session, url: str):
    """
    Basic function to make getting various URLs easier
    """
    return sess.get(url=url)


if __name__ == "__main__":
    main()