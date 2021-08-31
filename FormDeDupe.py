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

    for k, v in raw_forms_resp.items():
        # For each App record, check all other app records
        if k == "General_Record_2020v2.0":
            with Progress("[progress.description]{task.description}", BarColumn(), "{task.completed} of {task.total}",
                          console=console, transient=True) as progress:
                overall_task = progress.add_task(f"[green]Overall Progress", total=len(v))
                print(type(overall_task))
                # check_against_other_forms_task = progress.add_task(f"[white]Checking Against Other Projects",
                #                                                    total=len(v))
                # for test_app_record in v:
                #     progress.update(overall_task, advance=1)
                #     for other_app_record in v:
                #         duplicate_record = True
                #         # progress.update(check_against_other_forms_task, advance=1)
                #         # The record matchs another name. Check all fields
                #         if test_app_record.get("Cust_Name") == other_app_record.get("Cust_Name"):
                #             # progress.console.print(f"Duplicate with name with {test_app_record.get('Cust_Name')}")
                #             for key, value in test_app_record.items():
                #                 if key in other_app_record:
                #                     if value == other_app_record.get(key):
                #                         # Values match, continue
                #                         pass
                #                     else:
                #                         # Break loop on first failure and move on. It's not duplicate at that point
                #                         duplicate_record = False
                #                         break

                        # if duplicate_record:
                        #     # progress.console.log(f"Record {test_app_record.get('_ID')} is duplicate")
                        #     if test_app_record.get("Cust_Name") in duplicate_record_counter_dict:
                        #         count = duplicate_record_counter_dict.get(test_app_record.get("Cust_Name"))
                        #         count += 1
                        #         duplicate_record_counter_dict.update({test_app_record.get("Cust_Name"): count})
                        #     else:
                        #         duplicate_record_counter_dict.update({test_app_record.get("Cust_Name"): 1})

    console.log(f"Duplicates:")
    console.log(duplicate_record_counter_dict)








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