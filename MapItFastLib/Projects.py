class Project(object):
    """
    Class to hold all of the Project objects
    """

    def __init__(self, raw_data):
        self.raw_project_data = raw_data

    @property
    def ProjectId(self):
        return self.raw_project_data.get("ProjectId")

    @property
    def ProjectTypeId(self):
        return self.raw_project_data.get("ProjectTypeId")

    @property
    def Title(self):
        return self.raw_project_data.get("Title")

    @property
    def Description(self):
        return self.raw_project_data.get("Description")

    @property
    def LastChildUpdate(self):
        return self.raw_project_data.get("LastChildUpdate")

    @property
    def Creator(self):
        return self.raw_project_data.get("Creator")

    @property
    def ProjectFolderId(self):
        return self.raw_project_data.get("ProjectFolderId")

    @property
    def ProjectUserLocations(self):
        return self.raw_project_data.get("ProjectUserLocations")

    @property
    def GeoLines(self):
        return self.raw_project_data.get("GeoLines")

    @property
    def GeoPolygons(self):
        return self.raw_project_data.get("GeoPolygons")

    @property
    def Pictures(self):
        return self.raw_project_data.get("Pictures")

    @property
    def Points(self):
        return self.raw_project_data.get("Points")

    @property
    def CanEdit(self):
        return self.raw_project_data.get("CanEdit")

    @property
    def CanDelete(self):
        return self.raw_project_data.get("CanDelete")

    @property
    def CanContribute(self):
        return self.raw_project_data.get("CanContribute")

    @property
    def ActiveUsers(self):
        return self.raw_project_data.get("ActiveUsers")

    @property
    def CreatorName(self):
        return self.raw_project_data.get("CreatorName")

    @property
    def UserPermission(self):
        return self.raw_project_data.get("UserPermission")

class ProjectFolder(object):
    """
    Class for holding ProjectFolder objects
    """
    def __init__(self, raw_data):
        self.raw_project_folder_data = raw_data

    @property
    def ProjectFolderId(self):
        """
        Method for defining ProjectFolderId
        """
        return self.raw_project_folder_data.get("ProjectFolderId")

    @property
    def ParentFolderId(self):
        """
        Method for defining ParentFolderId
        """
        return self.raw_project_folder_data.get("ParentFolderId")

    @property
    def FolderName(self):
        """
        Method for defining FolderName
        """
        return self.raw_project_folder_data.get("FolderName")

    @property
    def Projects(self):
        """
        Method for defining Projects
        """
        return self.raw_project_folder_data.get("Projects")

    @property
    def ChildFolders(self):
        """
        Method for defining ChildFolders
        """
        return self.raw_project_folder_data.get("ChildFolders")
