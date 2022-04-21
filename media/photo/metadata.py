import re
from datetime import datetime


_property_name_pattern = re.compile(r"(.*:.+?)(?=(\b))")


def read_xmp(src: dict):
    """
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
            if k == "http://ns.adobe.com/xap/1.0/":
                if "Date" in property_name:
                    property_value = datetime.fromisoformat(
                        property_value[0:19])
            if k == "http://ns.adobe.com/camera-raw-settings/1.0/":
                if property_name == "crs:AutoBrightness":
                    property_value = bool(property_value)
                if property_name == "crs:AutoContrast":
                    property_value = bool(property_value)
                if property_name == "crs:AutoExposure":
                    property_value = bool(property_value)
                if property_name == "crs:AutoShadows":
                    property_value = bool(property_value)
                if property_name == "crs:BlueHue":
                    property_value = int(property_value)
                if property_name == "crs:BlueSaturation":
                    property_value = int(property_value)
                if property_name == "crs:Brightness":
                    property_value = int(property_value)
                if property_name == "crs:ChromaticAberrationB":
                    property_value = int(property_value)
                if property_name == "crs:ChromaticAberrationR":
                    property_value = int(property_value)
                if property_name == "crs:ColorNoiseReduction":
                    property_value = int(property_value)
                if property_name == "crs:Contrast":
                    property_value = int(property_value)
                if property_name == "crs:CropTop":
                    property_value = float(property_value)
                if property_name == "crs:CropLeft":
                    property_value = float(property_value)
                if property_name == "crs:CropBottom":
                    property_value = float(property_value)
                if property_name == "crs:CropRight":
                    property_value = float(property_value)
                if property_name == "crs:CropAngle":
                    property_value = float(property_value)
                if property_name == "crs:CropWidth":
                    property_value = float(property_value)
                if property_name == "crs:CropHeight":
                    property_value = float(property_value)
                if property_name == "crs:CropUnits":
                    property_value = int(property_value)
                if property_name == "crs:Exposure":
                    property_value = float(property_value)
                if property_name == "crs:GreenHue":
                    property_value = int(property_value)
                if property_name == "crs:GreenSaturation":
                    property_value = int(property_value)
                if property_name == "crs:HasCrop":
                    property_value = bool(property_value)
                if property_name == "crs:HasSettings":
                    property_value = bool(property_value)
                if property_name == "crs:LuminanceSmoothing":
                    property_value = int(property_value)
                if property_name == "crs:RedHue":
                    property_value = int(property_value)
                if property_name == "crs:RedSaturation":
                    property_value = int(property_value)
                if property_name == "crs:Saturation":
                    property_value = int(property_value)
                if property_name == "crs:Shadows":
                    property_value = int(property_value)
                if property_name == "crs:ShadowTint":
                    property_value = int(property_value)
                if property_name == "crs:Sharpness":
                    property_value = int(property_value)
                if property_name == "crs:Temperature":
                    property_value = int(property_value)
                if property_name == "crs:Tint":
                    property_value = int(property_value)
                if property_name == "crs:VignetteAmount":
                    property_value = int(property_value)
                if property_name == "crs:VignetteMidpoint":
                    property_value = int(property_value)
                # ToneCurve: int array
                # ToneCurveName: int array
            if k == "http://ns.adobe.com/exif/1.0/":
                if property_name == "exif:Contrast":
                    property_value = int(property_value)
                if property_name == "exif:CustomRendered":
                    property_value = int(property_value)
                if property_name == "exif:CustomRendered":
                    property_value = int(property_value)
                if property_name == "exif:DateTimeDigitized":
                    property_value = datetime.fromisoformat(
                        property_value[0:19])
                if property_name == "exif:DateTimeOriginal":
                    property_value = datetime.fromisoformat(
                        property_value[0:19])
                if property_name == "exif:ExposureMode":
                    property_value = int(property_value)
                if property_name == "exif:ExposureProgram":
                    property_value = int(property_value)
                if property_name == "exif:FileSource":
                    property_value = int(property_value)
                if property_name == "exif:FileSource":
                    property_value = int(property_value)
                if property_name == "exif:FocalLengthIn35mmFilm":
                    property_value = int(property_value)
                if property_name == "exif:FocalPlaneResolutionUnit":
                    property_value = int(property_value)
                if property_name == "exif:GainControl":
                    property_value = int(property_value)
                if property_name == "exif:ISOSpeedRatings":
                    property_value = int(property_value)
                if property_name == "exif:LightSource":
                    property_value = int(property_value)
                if property_name == "exif:MeteringMode":
                    property_value = int(property_value)
                if property_name == "exif:PixelXDimension":
                    property_value = int(property_value)
                if property_name == "exif:Saturation":
                    property_value = int(property_value)
                if property_name == "exif:SceneCaptureType":
                    property_value = int(property_value)
                if property_name == "exif:SceneType":
                    property_value = int(property_value)
                if property_name == "exif:SensingMethod":
                    property_value = int(property_value)
                if property_name == "exif:Sharpness":
                    property_value = int(property_value)
                if property_name == "exif:Sharpness":
                    property_value = int(property_value)
                if property_name == "exif:SubjectArea":
                    property_value = int(property_value)
                if property_name == "exif:SubjectDistanceRange":
                    property_value = int(property_value)
                if property_name == "exif:SubjectLocation":
                    property_value = int(property_value)
                if property_name == "exif:WhiteBalance":
                    property_value = int(property_value)
                if property_name == "exif:GPSAltitudeRef":
                    property_value = int(property_value)
                if property_name == "exif:GPSDifferential":
                    property_value = int(property_value)
                if property_name == "exif:GPSDifferential":
                    property_value = int(property_value)

            out[property_name] = property_value
    return out
