from io import BytesIO
from PIL import Image, ExifTags
from typing import Union
from datetime import date, time, datetime
from libxmp.utils import object_to_dict
from libxmp.core import XMPMeta
import re
import logging
import os
from .image import StaticImage
import sys


_property_name_pattern = re.compile(r"(.*:.+?)(?=(\b))")
_date_pattern = re.compile(r"^(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)")
_logger = logging.getLogger(f"INGEST.{__name__}")


def read_xmp(src: dict) -> dict:
    """
    Read a dictionary of xmp data and return parsed, type casted data

    :param src dictionary of xmp data


    Overview of namespaces and value types in exif_raw if using xmp:
        Documentations:
            https://developer.adobe.com/xmp/docs/XMPNamespaces/ for XMP
            https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ for DCMI Metadata Terms
        Namespaces
            'http://ns.adobe.com/xap/1.0/': Adobe XMP Basic namespace (Software, export datetime)
            'http://purl.org/dc/elements/1.1/': DCMI Metadata Terms (MIME type, creator)
            'http://ns.adobe.com/exif/1.0/aux/': XMP Media Management namespace
            'http://ns.adobe.com/photoshop/1.0/': Photoshop namespace
            'http://ns.adobe.com/xap/1.0/mm/: XMP Media Management namespace (Document ID, Filename)
            'http://ns.adobe.com/camera-raw-settings/1.0/': Camera Raw namespace (RawFileName, Edits (camera raw version, white balance, contrast, curve...))
            'http://ns.adobe.com/tiff/1.0/': TIFF namespace (camera name, camera model)
            'http://ns.adobe.com/exif/1.0/': EXIF namespace (exif data, exposure time, aperature, exposure program, metering mode...)
    """
    _dateparse = ["exif:DateTimeDigitized", "exif:DateTimeOriginal",
                  "xmp:CreateDate", "xmp:MetadataDate", "xmp:ModifyDate"]
    _intparse = ["crs:BlueHue",
                 "crs:BlueSaturation",
                 "crs:Brightness",
                 "crs:ChromaticAberrationB",
                 "crs:ChromaticAberrationR",
                 "crs:ColorNoiseReduction",
                 "crs:Contrast",
                 "crs:CropUnits",
                 "crs:GreenHue",
                 "crs:GreenSaturation",
                 "crs:LuminanceSmoothing",
                 "crs:RedHue",
                 "crs:RedSaturation",
                 "crs:Saturation",
                 "crs:Shadows",
                 "crs:ShadowTint",
                 "crs:Sharpness",
                 "crs:Temperature",
                 "crs:Tint",
                 "crs:VignetteAmount",
                 "crs:VignetteMidpoint",
                 "exif:Contrast",
                 "exif:CustomRendered",
                 "exif:ExposureMode",
                 "exif:ExposureProgram",
                 "exif:FileSource",
                 "exif:FocalLengthIn35mmFilm",
                 "exif:FocalPlaneResolutionUnit",
                 "exif:GainControl",
                 "exif:ISOSpeedRatings",
                 "exif:LightSource",
                 "exif:SceneCaptureType",
                 "exif:SceneType",
                 "exif:SensingMethod",
                 "exif:Sharpness",
                 "exif:SubjectArea",
                 "exif:SubjectDistanceRange",
                 "exif:SubjectLocation",
                 "exif:WhiteBalance",
                 "exif:GPSAltitudeRef",
                 "exif:GPSDifferential"]
    _floatparse = ["crs:CropTop",
                   "crs:CropLeft",
                   "crs:CropBottom",
                   "crs:CropRight",
                   "crs:CropAngle",
                   "crs:CropWidth",
                   "crs:CropHeight",
                   "crs:Exposure",
                   ""]
    _boolparse = ["crs:AutoBrightness",
                  "crs:AutoContrast",
                  "crs:AutoExposure",
                  "crs:AutoShadows",
                  "crs:HasCrop",
                  "crs:HasSettings",
                  ""]

    out = {}

    for k, v in src.items():
        for element in v:
            # property_name = element[0]
            property_name = _property_name_pattern.match(element[0]).group(1)
            property_value = element[1]

            # TODO perserve entry with multiple values: e.g. History[1]
            if property_value == "" or property_value is None:
                continue

            # Cast string to corrisponding type
            if property_name in _dateparse:
                match = _date_pattern.match(property_value)
                if not match:
                    continue
                property_value = datetime.fromisoformat(match.group(1))
            elif property_name in _intparse:
                property_value = int(property_value)
            elif property_name in _floatparse:
                property_value = float(property_value)
            elif property_name in _boolparse:
                property_value = bool(property_value)

            out[property_name] = property_value
    return out


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

    def __init__(self, data: Union[str, Image.Image, BytesIO], title: str = None, filename: str = None):
        """Initialize a Photo class, metadata such as exif will be read from the data

        :param d Data of the photo, other metadata will be read from this
        :param title Optional Title of the photo
        """
        if isinstance(data, str) or isinstance(data, BytesIO):
            _logger.debug(
                f"data is of type {type(data)}, attempting to open as PIL.Image.Image")

            if isinstance(data, str):
                self.filename = os.path.basename(data)

            data = Image.open(data)
        else:
            if not filename:
                _logger.critical("Filename required")
                sys.exit(1)

        super(Photo, self).__init__(data, title)

        if filename:
            self.filename = filename

        exif = {}

        # TODO Implement reading exif directly from PIL
        # Using XMP
        _logger.debug("Metadata in XMP format")
        xmp_meta = XMPMeta(xmp_str=str(self.data.info["XML:com.adobe.xmp"]))
        metadata = read_xmp(object_to_dict(xmp_meta))

        _logger.debug("Setting attributes to available metadata")
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
            self.camera_model = metadata["tiff:Model"]
        if "dc:creator" in metadata_keys:
            self.artist = metadata["dc:creator"]
        if "xmp:CreatorTool" in metadata_keys:
            self.software = metadata["xmp:CreatorTool"]
        if "dc:format" in metadata_keys:
            self.content_type = metadata["dc:format"]
        if "crs:RawFileName" in metadata_keys:
            self.raw_filename = metadata["crs:RawFileName"]
        if "exif:ExposureMode" in metadata_keys:
            self.exposure_mode = metadata["exif:ExposureMode"]
        if "exif:ExposureProgram" in metadata_keys:
            self.exposure_program = metadata["exif:ExposureProgram"]
        if "exif:MeteringMode" in metadata_keys:
            self.metering_mode = metadata["exif:MeteringMode"]

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