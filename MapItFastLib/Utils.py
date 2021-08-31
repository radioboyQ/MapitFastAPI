from datetime import datetime
import os
from pathlib import Path
import pickle
from time import sleep
import sys

import requests
from rich.console import Console
from rich.status import Status

from .Projects import Project, ProjectFolder
from .Points import Points

def validate_cache_folder(ctx, param, value):
    """
    Validate the incoming folder name exists, if not, create it.
    """
    # Create folder if it doesn't exist
    Path(value).mkdir(parents=True, exist_ok=True)

    return Path(value)

class AgTerraAPI(object):
    """
    Lower level abstractions
    """
    @staticmethod
    def get_projects(sess: requests.Session, console: Console, url: str = f"https://mapitfast.agterra.com/api/Projects"):
        """
        Helper function to get projects list
        """
        # Get the folder listusername
        raw_resp = AgTerraAPI.get_url(sess=sess, url=url)

        json_data = raw_resp.json()
        output_obj_list = list()

        if "ProjectFolders" in url:
            # Convert to project folders object
            for raw_project_folder in json_data:
                output_obj_list.append(ProjectFolder(raw_data=raw_project_folder))
        else:
            # Turn each project from JSON into an object we can actually use
            for raw_proj_dict in json_data:
                output_obj_list.append(Project(raw_data=raw_proj_dict))

        return output_obj_list
    @staticmethod
    def get_points(sess: requests.Session, console: Console, projectID: int,
                   url: str = f"https://mapitfast.agterra.com/api/Points"):
        """
        Get all exisiting points in a project
        """
        raw_resp = AgTerraAPI.get_url(sess=sess, url=url, params={"projectId": projectID})
        try:
            json_resp = raw_resp.json()
        except:
            console.log(f"Error converting Project {projectID} to a dictionary")
            sys.exit(1)

        points_obj_list = list()
        for raw_resp in json_resp:
            points_obj_list.append(Points(raw_data=raw_resp))

        return points_obj_list

    @staticmethod
    def get_url(sess: requests.Session, url: str, params: dict = None):
        """
        Basic function to make getting various URLs easier
        """
        if params is None:
            try:
                resp = sess.get(url=url)
                resp.raise_for_status()
            except:
                resp = AgTerraAPI.get_url(sess=sess, url=url, params=params)
            return resp
        else:
            try:
                resp = sess.get(url=url, params=params)
                resp.raise_for_status()
            except:
                resp = AgTerraAPI.get_url(sess=sess, url=url, params=params)
            return resp

    @staticmethod
    def get_project_folders(sess: requests.Session):
        """
        Just get the JSON blob of folders and convert them into objects in a dict
        Dict should looks like this:
        {folder_id: folder_obj}
        """
        url = "https://mapitfast.agterra.com/api/ProjectFolders"
        return_list = list()


        raw_resp = sess.get(url).json()
        for raw_proj_folder in raw_resp:
            project_folder_obj = ProjectFolder(raw_data=raw_proj_folder)
            return_list.append(project_folder_obj)
        return return_list

    @staticmethod
    def post_points(sess: requests.Session, console: Console, point_dict: dict,
                    url: str = f"https://mapitfast.agterra.com/api/Points"):
        """
        Function to post points data to a project
        """
        return sess.post(url=url, data=point_dict)


class AgTerraWrapper(object):
    """
    Higher level abstractions for 'public' facing API calls
    """

    @staticmethod
    def post_points(username: str, password: str, console: Console, project_id: int, data_dict: dict, title: str,
                    description: str, longitude: float, latitude: float,
                    itemtime: datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), elevation: int = 0,
                    icon_id: int = 3):
        """
        Post point to AgTerra.
        One point at a time for this function
        """
        data_dict = {"ProjectID": project_id, "IconID": icon_id, "Title": title,
                     "Description": description, "Longitude": longitude, "Latitude": latitude,
                     "ItemTime": itemtime, "Elevation": elevation}
        with requests.Session() as sess:
            sess.auth = (username, password)
            point_response = AgTerraAPI.post_points(sess=sess, console=console,
                                                    point_dict=data_dict)
            return point_response


    @staticmethod
    def get_points(username: str, password: str, console: Console, project_id: int, cache_path: Path,
                   show_off_mode: bool = True, url: str = f"https://mapitfast.agterra.com/api/Points",
                   use_pickle_cache: bool = True, refresh_cache: bool = False):
        """
        Wrapper for get_points with caching
        """
        cache_path = Path(os.path.join(cache_path, f"points_cache_{project_id}"))
        # console.log(cache_path)
        if refresh_cache:
            point_obj_list = AgTerraWrapper.load_points_cache_pickles(username=username, password=password,
                                                                      console=console, cache_path=cache_path,
                                                                      show_off_mode=show_off_mode, url=url,
                                                                      use_pickle_cache=use_pickle_cache,
                                                                      project_id=project_id)
        elif cache_path.exists():
            # Cache exists, pulling from the cache
            with open(cache_path, 'rb') as f:
                point_obj_list = pickle.load(f)
        else:
            # Cache doesn't exist, user didn't force a refresh
            console.log(f"[bold][green]Warming up the cache for project {project_id}")
            point_obj_list = AgTerraWrapper.load_points_cache_pickles(username=username, password=password, console=console,
                                                                       cache_path=cache_path, show_off_mode=show_off_mode,
                                                                       use_pickle_cache=use_pickle_cache, url=url,
                                                                      project_id=project_id)

        return point_obj_list

    @staticmethod
    def load_points_cache_pickles(username: str, password: str, console: Console, cache_path: Path, project_id: int,
                                  show_off_mode: bool = True, url: str = f"https://mapitfast.agterra.com/api/Projects",
                                  use_pickle_cache: bool = True):
        """
        Wrapper for get_points with caching
        """
        with requests.Session() as sess:
            sess.auth = (username, password)
            # console.log(f"[bold]Requesting Object List From Server")
            obj_list = AgTerraAPI.get_points(sess=sess, console=console, url=url, projectID=project_id)
            if show_off_mode:
                sleep(0.9)
            if use_pickle_cache:
                with open(cache_path, 'wb') as f:
                    # console.log(f"[bold][green]Writing objects to local cache")
                    if show_off_mode:
                        sleep(1.2)
                    pickle.dump(obj_list, f)
        return obj_list

    @staticmethod
    def load_project_cache_pickles(username: str, password: str, console: Console, cache_path: Path, show_off_mode: bool = True,
                                   url: str = f"https://mapitfast.agterra.com/api/Projects", use_pickle_cache: bool = True):
        """
        Wrapper for get_projects with caching
        """
        with requests.Session() as sess:
            sess.auth = (username, password)

            with Status("[magenta]Connecting", console=console, spinner='arrow3') as status:
                if show_off_mode:
                    sleep(0.7)
                status.update(f"[bold]Requesting Object List From Server")
                obj_list = AgTerraAPI.get_projects(sess=sess, console=status.console, url=url)
                if show_off_mode:
                    sleep(0.9)
                if use_pickle_cache:
                    with open(cache_path, 'wb') as f:
                        status.update(f"[bold][green]Writing objects to local cache")
                        if show_off_mode:
                            sleep(1.2)
                        pickle.dump(obj_list, f)
        return obj_list

    @staticmethod
    def get_projects(username: str, password: str, console: Console, cache_path: Path, show_off_mode: bool = True,
                        url: str = f"https://mapitfast.agterra.com/api/Projects", use_pickle_cache: bool = True,
                     refresh_cache: bool = False):
        """
        Wrapper to figure out caching or if projects needs to be gotten from the server
        """
        if refresh_cache:
            proj_obj_list = AgTerraWrapper.load_project_cache_pickles(username=username, password=password, console=console,
                                                                      cache_path=cache_path,
                                                                      show_off_mode=show_off_mode,
                                                                      use_pickle_cache=use_pickle_cache)

        elif cache_path.exists():
            # Cache exists, pulling from the cache
            with Status("[bold][blue]Reading local cache", console=console, spinner='arrow3') as status:
                if show_off_mode:
                    sleep(1.2)
                with open(cache_path, 'rb') as f:
                    proj_obj_list = pickle.load(f)

        else:
            # Cache doesn't exist, user didn't force a refresh
            console.log(f"[bold][green]Warming up the cache")
            proj_obj_list = AgTerraWrapper.load_project_cache_pickles(username=username, password=password, console=console,
                                                                      cache_path=cache_path,
                                                                      show_off_mode=show_off_mode,
                                                                      use_pickle_cache=use_pickle_cache)
        return proj_obj_list

    @staticmethod
    def get_project_folders(username: str, password: str, console: Console, cache_path: Path, show_off_mode: bool = True,
                            url: str = f"https://mapitfast.agterra.com/api/ProjectFolders", use_pickle_cache: bool = True,
                            refresh_cache: bool = False):
        """
        Wrapper for getting the project folders and caching them
        """
        proj_folder_obj_dict = dict()
        # if refresh_cache:
        #     proj_folder_obj_list = AgTerraWrapper.load_cache_pickles(username=username, password=password,
        #                                                              console=console, cache_path=cache_path,
        #                                                              show_off_mode=show_off_mode,
        #                                                              use_pickle_cache=use_pickle_cache, url=url)
        # elif cache_path.exists():
        #     # Cache exists, pulling from the cache
        #     with Status("[bold][blue]Reading local cache", console=console, spinner='arrow3') as status:
        #         if show_off_mode:
        #             sleep(1.2)
        #         with open(cache_path, 'rb') as f:
        #             proj_obj_list = pickle.load(f)
        # else:

        # Cache doesn't exist, user didn't force a refresh
        console.log(f"[bold][green]Warming up the cache")
        with requests.Session() as sess:
            sess.auth = (username, password)
            proj_folder_obj_list = AgTerraAPI.get_project_folders(sess=sess)

        # Make a dictionary of project folder IDs with ProjectFolder objects as value
        # {project_folder_id: project_folder_object}
        for proj_folder in proj_folder_obj_list:
            proj_folder_obj_dict.update({proj_folder.ProjectFolderId: proj_folder})

        return proj_folder_obj_dict