from io import BytesIO, TextIOWrapper
from PIL import Image, ExifTags
from typing import Union
from datetime import date, time, datetime
import re
import logging
import os
from .image import StaticImage
import sys


_date_pattern = re.compile(r"^(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)")
_logger = logging.getLogger(__name__)


def read_xmp(src: dict) -> dict:
    """
    Read a dictionary of xmp data and return parsed, type casted data

    :param src dictionary of xmp data


    Overview of namespaces and value types in exif_raw if using 
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
    _dateparse = ["DateTimeDigitized", "DateTimeOriginal",
                  "CreateDate", "MetadataDate", "ModifyDate"]
    _intparse = ["BlueHue",
                 "BlueSaturation",
                 "Brightness",
                 "ChromaticAberrationB",
                 "ChromaticAberrationR",
                 "ColorNoiseReduction",
                 "Contrast",
                 "CropUnits",
                 "GreenHue",
                 "GreenSaturation",
                 "LuminanceSmoothing",
                 "RedHue",
                 "RedSaturation",
                 "Saturation",
                 "Shadows",
                 "ShadowTint",
                 "Sharpness",
                 "Temperature",
                 "Tint",
                 "VignetteAmount",
                 "VignetteMidpoint",
                 "Contrast",
                 "CustomRendered",
                 "ExposureMode",
                 "ExposureProgram",
                 "FileSource",
                 "FocalLengthIn35mmFilm",
                 "FocalPlaneResolutionUnit",
                 "GainControl",
                 "LightSource",
                 "SceneCaptureType",
                 "SceneType",
                 "SensingMethod",
                 "Sharpness",
                 "SubjectArea",
                 "SubjectDistanceRange",
                 "SubjectLocation",
                 "WhiteBalance",
                 "GPSAltitudeRef",
                 "GPSDifferential"
                 ]
    _floatparse = ["CropTop",
                   "CropLeft",
                   "CropBottom",
                   "CropRight",
                   "CropAngle",
                   "CropWidth",
                   "CropHeight",
                   "Exposure"
                   ]
    _boolparse = ["AutoBrightness",
                  "AutoContrast",
                  "AutoExposure",
                  "AutoShadows",
                  "HasCrop",
                  "HasSettings"
                  ]

    out = {}

    for k, v in src.items():
        if v == "" or v is None:
            continue

        # Cast string to corrisponding type
        if k in _dateparse:
            match = _date_pattern.match(v)
            if not match:
                continue
            v = datetime.fromisoformat(match.group(1))
        elif k in _intparse:
            v = int(v)
        elif k in _floatparse:
            v = float(v)
        elif k in _boolparse:
            v = bool(v)
        elif k == "ISOSpeedRatings":
            v = int(v["Seq"]["li"])
        elif k == "creator":
            v = v["Seq"]["li"]

        out[k] = v
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

    def __init__(self, data: Union[str, Image.Image, BytesIO], title: str = None, filename: str = None, xmp_file: TextIOWrapper = None):
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

        if "XML:com.adobe.xmp" in self.data.info:
            metadata = read_xmp(self.data.getxmp()[
                                "xmpmeta"]["RDF"]["Description"])
            metadata_keys = metadata.keys()

            _logger.debug("Setting attributes to available metadata")
            if "CreateDate" in metadata_keys:
                self.date_capture = metadata["CreateDate"].date()
                self.time_capture = metadata["CreateDate"].time()
            if "ModifyDate" in metadata_keys:
                self.date_export = metadata["ModifyDate"].date()
                self.time_export = metadata["ModifyDate"].time()
            if "ExposureTime" in metadata_keys:
                self.shutter = metadata["ExposureTime"]
            if "FNumber" in metadata_keys:
                self.aperture = metadata["FNumber"].split("/")[0]
            if "FocalLength" in metadata_keys:
                fl = metadata["FocalLength"].split("/")
                self.focal_length = int(int(fl[0]) / int(fl[1]))
            if "FocalLengthIn35mmFilm" in metadata_keys:
                self.focal_length_35 = int(metadata["FocalLengthIn35mmFilm"])
            if "ISOSpeedRatings" in metadata_keys:
                self.iso = int(metadata["ISOSpeedRatings"])
            if "Make" in metadata_keys:
                self.camera_maker = metadata["Make"]
            if "Model" in metadata_keys:
                self.camera_model = metadata["Model"]
            if "creator" in metadata_keys:
                self.artist = metadata["creator"]
            if "CreatorTool" in metadata_keys:
                self.software = metadata["CreatorTool"]
            if "format" in metadata_keys:
                self.content_type = metadata["format"]
            if "RawFileName" in metadata_keys:
                self.raw_filename = metadata["RawFileName"]
            if "ExposureMode" in metadata_keys:
                self.exposure_mode = metadata["ExposureMode"]
            if "ExposureProgram" in metadata_keys:
                self.exposure_program = metadata["ExposureProgram"]
            if "MeteringMode" in metadata_keys:
                self.metering_mode = metadata["MeteringMode"]
