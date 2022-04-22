from typing import Union
from get_config import get_config, ConfigScope
from media.image.photo import Photo

_config = get_config(ConfigScope.HANDLE)

def get_handle(object: Photo):
    if isinstance(object, Photo):
        pass
    pass
