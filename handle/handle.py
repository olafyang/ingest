from media.image.photo import Photo
from db.db import get_photo_count_by_date
from get_config import get_config, ConfigScope
import pyhandle


_config = get_config(ConfigScope.HANDLE)

def _make_handle(obj: Photo):
    """Make a handle string using default definition based on requirement

    :param obj
    """
    if isinstance(obj, Photo):
        # Format "P<DATE>.I<ID>"
        date = obj.date_capture
        prefix = _config["prefix"]
        handle = f"{prefix}/P{date.isoformat()}.I{get_photo_count_by_date(date) + 1}"
        return handle
