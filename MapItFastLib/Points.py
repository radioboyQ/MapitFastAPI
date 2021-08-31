from datetime import datetime


class Points(object):
    """
    Class to hold all of the Point objects
    """
    def __init__(self, raw_data):
        self.raw_point_data = raw_data

    @property
    def CanDelete(self):
        return self.raw_point_data.get("CanDelete")

    @property
    def CanEdit(self):
        return self.raw_point_data.get("CanEdit")

    @property
    def Creator(self):
        return self.raw_point_data.get("Creator")

    @property
    def CreatorResolved(self):
        return self.raw_point_data.get("CreatorResolved")

    @property
    def Description(self):
        return self.raw_point_data.get("Description")

    @property
    def DispatchCases(self):
        return self.raw_point_data.get("DispatchCases")

    @property
    def Elevation(self):
        return self.raw_point_data.get("Elevation")

    @property
    def Forms(self):
        return self.raw_point_data.get("Forms")

    @property
    def IconHttpLocation(self):
        return self.raw_point_data.get("IconHttpLocation")

    @property
    def IconId(self):
        return self.raw_point_data.get("IconId")

    @property
    def ItemTime(self):
        try:
            # Not all timestamps are represented in this way. This is bullshit.
            return datetime.strptime(self.raw_point_data.get("ItemTime"), "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            return datetime.strptime(self.raw_point_data.get("ItemTime"), "%Y-%m-%dT%H:%M:%S")
        # return self.raw_point_data.get("ItemTime")

    @property
    def Latitude(self):
        return self.raw_point_data.get("Latitude")

    @property
    def Longitude(self):
        return self.raw_point_data.get("Longitude")

    @property
    def PointId(self):
        return self.raw_point_data.get("PointId")

    @property
    def ProjectId(self):
        return self.raw_point_data.get("ProjectId")

    @property
    def Title(self):
        return self.raw_point_data.get("Title")