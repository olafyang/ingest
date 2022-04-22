from io import BytesIO
from PIL import Image, ExifTags
from typing import Union
from datetime import date, time, datetime
from libxmp.utils import object_to_dict
from libxmp.core import XMPMeta
from .metadata import read_xmp


class Photo:
    data: Image.Image = None
    title: str = None
    date_capture: date = None
    time_capture: time = None
    date_export: date = None
    time_export: time = None
    shutter: str = None
    aperture: str = None
    focal_length: int = None
    focal_length_35: int = None
    camera_maker: str = None
    camera_model: str = None
    software: str = None
    artist: str = None
    iso: int = None
    content_type: str = None

    def __init__(self, d: Union[str, Image.Image, BytesIO], title: str = None):
        """Initialize a Photo class, metadata such as exif will be read from the data

        :param d Data of the photo, other metadata will be read from this
        :param title Optional Title of the photo
        """
        if isinstance(d, str) or isinstance(d, BytesIO):
            self.data = Image.open(d)
        else:
            self.data = d

        exif = {}

        # Using XMP
        xmp_meta = XMPMeta(xmp_str=str(self.data.info["XML:com.adobe.xmp"]))

        metadata_raw = object_to_dict(xmp_meta)
        metadata = read_xmp(metadata_raw)

        metadata_keys = metadata.keys()
        if "xmp:CreateDate" in metadata_keys:
            self.date_capture = metadata["xmp:CreateDate"].date()
            self.time_capture = metadata["xmp:CreateDate"].time()
        if "xmp:ModifyDate" in metadata_keys:
            self.date_export = metadata["xmp:ModifyDate"].date()
            self.time_export = metadata["xmp:ModifyDate"].time()
        if "exif:ExposureTime" in metadata_keys:
            self.shutter = metadata["exif:ExposureTime"]
        if "exif:FNumber" in metadata_keys:
            self.aperture = metadata["exif:FNumber"].split("/")[0]
        if "exif:FocalLength" in metadata_keys:
            fl = metadata["exif:FocalLength"].split("/")
            self.focal_length = int(int(fl[0]) / int(fl[1]))
        if "exif:FocalLengthIn35mmFilm":
            self.focal_length_35 = int(metadata["exif:FocalLengthIn35mmFilm"])
        if "exif:ISOSpeedRatings" in metadata_keys:
            self.iso = int(metadata["exif:ISOSpeedRatings"])
        if "tiff:Make" in metadata_keys:
            self.camera_maker = metadata["tiff:Make"]
        if "tiff:Model" in metadata_keys:
            self.camera_maker = metadata["tiff:Model"]
        if "dc:creator" in metadata_keys:
            self.artist = metadata["dc:creator"]
        if "xmp:CreatorTool" in metadata_keys:
            self.software = metadata["xmp:CreatorTool"]
        if "dc:format" in metadata_keys:
            self.content_type = metadata["dc:format"]

        # with open("metadata.json", "w") as file:
        #     json.dump(metadata, file)

        # Using PIL
        # img_exif = self.photo.getexif()
        # for k, v in img_exif.items():
        #     print(k)
        #     if k in ExifTags.TAGS:
        #         tag = ExifTags.TAGS[k]
        #         if tag == "Make":
        #             self.camera_maker = v
        #         if tag == "Model":
        #             self.camera_model = v
        #         if tag == "Software":
        #             self.software = v
        #         if tag == "DateTime":
        #             dt = datetime.strptime(v, "%Y:%m:%d %H:%M:%S")
        #             self.date_capture = dt.date()
        #             self.time_capture = dt.time()
        #         exif[ExifTags.TAGS[k]] = v
        #
        # print(exif)

    def save_io(self):
        b = BytesIO()
        self.data.save(b)
        b.seek(0)
        return b
