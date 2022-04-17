from ast import Bytes
from io import BytesIO
from PIL import Image, ExifTags
from typing import Union
from datetime import date, time, datetime
from libxmp.utils import object_to_dict
from libxmp.core import XMPMeta


def _read_xmp_xap(src: list) -> dict:
    pass


def _read_xmp_dcmi_elements(src: list) -> dict:
    pass


def _ead_xmp_exif_aux(src: list) -> dict:
    pass


def _read_xmp_xap_mm(src: list) -> dict:
    pass


def _read_xmp_tiff(src: list) -> dict:
    pass


def _read_xmp_exif(src: list) -> dict:
    pass


def read_xmp(src):
    """

    Overview of namespaces and value types in exif_raw if using xmp:
        Documentations:
            https://developer.adobe.com/xmp/docs/XMPNamespaces/ for XMP
            https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ for DCMI Metadata Terms
        Namespaces
            'http://ns.adobe.com/xap/1.0/': Adobe XMP Basic namespace (Software, export datetime)
            'http://purl.org/dc/elements/1.1/': DCMI Metadata Terms (MIME type, creator)
            'http://ns.adobe.com/exif/1.0/aux/': XMP Media Management namespace (camera serial number, lens information)
            'http://ns.adobe.com/photoshop/1.0/': Photoshop namespace 
            'http://ns.adobe.com/xap/1.0/mm/: XMP Media Management namespace (Document ID, Filename)
            'http://ns.adobe.com/camera-raw-settings/1.0/': Camera Raw namespace (RawFileName, Edits (camera raw version, white balance, contrast, curve...))
            'http://ns.adobe.com/tiff/1.0/': TIFF namespace (camera name, camera model)
            'http://ns.adobe.com/exif/1.0/': EXIF namespace (exif data, exposure time, aperature, exposure program, metering mode...)
    """
    pass


class Photo(object):
    photo = None
    title = None
    date_capture = None
    time_capture = None
    date_export = None
    time_export = None
    exposure = None
    aperture = None
    focal_length = None
    camera_maker = None
    camera_model = None
    software = None
    artist = None

    def __init__(self, d: Union[str, Image.Image, BytesIO], title: str = None):
        """Initialize a Photo class, metadata such as exif will be read from the data

        :param d Data of the photo, other metadata will be read from this
        :param title Optional Title of the photo
        """
        if isinstance(d, str) or isinstance(d, BytesIO):
            self.photo = Image.open(d)
        else:
            self.photo = d

        exif = {}
        xmp_meta = XMPMeta(xmp_str=str(self.photo.info["XML:com.adobe.xmp"]))

        exif_raw = object_to_dict(xmp_meta)

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
