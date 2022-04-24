from .media.image.photo import Photo


def get_endpoint(obj):
    if isinstance(obj, Photo):
        return "https://olafyang.com"
