from io import BytesIO, TextIOWrapper
from PIL import Image, ExifTags
from typing import Union
from datetime import date, time, datetime
import re
import logging
import os
from .image import StaticImage
import sys


_property_name_pattern = re.compile(r"(.*:.+?)(?=(\b))")
_date_pattern = re.compile(r"^(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d).*")
_logger = logging.getLogger(__name__)


class Photo(StaticImage):
    """ The Photo class represents a photo alongside with some of it's metadate.

    Attributes:
        date_capture (date): (class attribute) The capture date of the photo
        time_capture (time): (class attribute) The capture time of the photo
        date_export (date): (class attribute) The export date of the photo
        time_export (time): (class attribute) The export time of the photo
        shutter (str): (class attribute) The shutter speed presented in string format of rational number
        aperture (str): (class attribute) The F-Stop value
        focal_length (int): (class attribute) The focal length at the time of capture
        focal_length_35 (int): (class attribute) The 35mm equivalent of the focal length at the time of capture
        camera_maker (str): (class attribute) The camera maker, usually the brand of the camera
        camera_model (str): (class attribute) The camera model
        iso (str): The ISO speed rating setting of the camera at the time of capture
        exposure_mode (int): The exposure mode used to capture the photo, See `ExposureMode`_
        exposure_program (int): The exposure mode used to capture the photo, See `ExposureProgram`_
        metering_mode (int): The metering mode used to capture the photo , See `MeteringMode`_
        artist (str): (class attribute) The name of the creator of the photo
        software (str): (class attribute) Software used to output the image
        content_type (str): The media type of the photo in the format of the MIME type
        raw_filename (str): The original filename from the camera
        filename (str): The filename at the time of ingest

    .. _ExposureMode https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/exposuremode.html
    .. _ExposureProgram https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/exposureprogram.html
    .. _MeteringMode https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/meteringmode.html

    Args:
        StaticImage (_type_): _description_
    """
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
    iso: int = None
    exposure_mode: int = None
    exposure_program: int = None
    metering_mode: int = None
    artist: str = None

    software: str = None
    content_type: str = None
    raw_filename: str = None
    filename: str = None

    def __init__(self, data: Union[str, Image.Image, BytesIO], title: str = None, filename: str = None, xmp_file: TextIOWrapper = None):
        """Constructor of a Photo class

        Args:
            data (Union[str, Image.Image, BytesIO]): Either the location of the file, A PIL Image Class or data in BytesIO
            title (str, optional): The optional title for the photo. Defaults to None.
            filename (str, optional): Filename of the photo, required for duplication check if data is of type BytesIO or Image. Defaults to None.
            xmp_file (TextIOWrapper, optional): Custom XMP file to read metadata from. Defaults to None.
        """

        if isinstance(data, str) or isinstance(data, BytesIO):
            _logger.debug(
                f"data is of type {type(data)}, attempting to open as PIL.Image.Image")

            if isinstance(data, str):
                self.filename = os.path.basename(data)
                self.filepath = os.path.abspath(data)

            data = Image.open(data)
        else:
            if not filename:
                _logger.critical("Filename required")
                sys.exit(1)
            self.filename = filename

        super(Photo, self).__init__(data, title)

        exif = {}

        self.content_type = self.data.get_format_mimetype()

        xmp = self.data.getxmp()
        if xmp:
            # from pprint import pprint

            tags = xmp["xmpmeta"]["RDF"]["Description"]
            # pprint(tags)
            for tag in tags:
                val = tags[tag]
                if tag == "CreatorTool":
                    self.software = val
                elif tag == "CreateDate":
                    dt = _date_pattern.match(val).group(1)
                    if not dt:
                        continue
                    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                    self.date_capture = dt.date()
                    self.time_capture = dt.time()
                elif tag == "ModifyDate":
                    dt = _date_pattern.match(val).group(1)
                    if not dt:
                        continue
                    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                    self.date_export = dt.date()
                    self.time_export = dt.time()
                elif tag == "ExposureMode":
                    self.exposure_mode = int(val)
                elif tag == "ExposureProgram":
                    self.exposure_program = int(val)
                elif tag == "ExposureTime":
                    self.shutter = val
                elif tag == "FNumber":
                    self.aperture = val.split("/")[0]
                elif tag == "FocalLength":
                    fl = val.split("/")
                    self.focal_length = int(int(fl[0]) / int(fl[1]))
                elif tag == "FocalLengthIn35mmFilm":
                    self.focal_length_35 = int(val)
                elif tag == "ISOSpeedRatings":
                    if isinstance(val, dict):
                        self.iso = int(val["Seq"]["li"])
                        continue
                    self.iso = int(val)
                elif tag == "Make:":
                    self.camera_maker = val
                elif tag == "Model":
                    self.camera_model = val
                elif tag == "RawFileName":
                    self.raw_filename = val
                elif tag == "creator":
                    if isinstance(val, dict):
                        self.artist = val["Seq"]["li"]
                        continue
                    self.artist = val
                elif tag == "MeteringMode":
                    self.metering_mode = val

        img_exif = self.data.getexif()
        if img_exif:
            for k, v in img_exif.items():
                if k in ExifTags.TAGS:
                    tag = ExifTags.TAGS[k]
                    if tag == "Make":
                        self.camera_maker = v
                    elif tag == "Model":
                        self.camera_model = v
                    elif tag == "Software":
                        self.software = v
                    elif tag == "DateTime":
                        dt = datetime.strptime(v, "%Y:%m:%d %H:%M:%S")
                        self.date_export = dt.date()
                        self.time_export = dt.time()
                    exif[ExifTags.TAGS[k]] = v

            for k, v in img_exif.get_ifd(0x8769).items():
                if k in ExifTags.TAGS:
                    tag = ExifTags.TAGS[k]
                    if tag == "DateTimeOriginal":
                        self.date_capture = datetime.strptime(
                            v, "%Y:%m:%d %H:%M:%S").date()
                        self.time_capture = datetime.strptime(
                            v, "%Y:%m:%d %H:%M:%S").time()
                    elif tag == "ExposureTime":
                        self.shutter = f"1/{1 / v}" if v < 1 else str(int(v))
                    elif tag == "FNumber":
                        self.aperture = f"{v}"
                    elif tag == "ISOSpeedRatings":
                        self.iso = v
                    elif tag == "FocalLength":
                        self.focal_length = int(v)
                    elif tag == "ExposureMode":
                        self.exposure_mode = v
                    elif tag == "ExposureProgram":
                        self.exposure_program = int(v)
                    elif tag == "MeteringMode":
                        self.metering_mode = int(v)
                    elif tag == "Artist":
                        self.artist = v

        _logger.debug(self.__dict__)
