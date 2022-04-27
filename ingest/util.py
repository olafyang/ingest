from .media.image.photo import Photo


def convert_to_mime(obj_format: str):
    obj_format = obj_format.lower()
    if obj_format == "png":
        return "image/png"
    if obj_format == "jpg" or obj_format == "jpeg":
        return "image/jpeg"


def get_endpoint(obj):
    if isinstance(obj, Photo):
        return "https://olafyang.com"
