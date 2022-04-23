from media.image.photo import Photo
from db.db import DB
from get_config import get_config, ConfigScope
from typing import Union
from pyhandle.handleclient import PyHandleClient
import logging

_logger = logging.getLogger(f"INGEST.{__name__}")
_config = get_config(ConfigScope.HANDLE)


def _get_endpoint(obj):
    if isinstance(obj, Photo):
        return "https://olafyang.com"


def _make_handle(obj: Photo):
    """Make a handle string using default definition based on requirement

    :param obj
    """
    if isinstance(obj, Photo):
        db = DB()

        # Format "P<DATE>.I<ID>"
        date = obj.date_capture
        prefix = _config["prefix"]
        handle = f"{prefix}/P{date.isoformat()}.I{db.get_photo_count_by_date(date) + 1}"
        return handle


def register(obj: Photo, name: str = None) -> tuple:
    """
    Register a new handle using an object and it's corrisponding suffix schema.
    The default schema can be overwritten using the name argument.

    :param: obj
    :param: name If the name argument is given, it replaces the default schema
    :rtype: (string, string) (Handle, Location)
    """
    if name:
        _logger.debug("Using custom name for suffix")
        handle = f'{_config["prefix"]}/{name}'
    else:
        _logger.debug("Making suffix from object")
        handle = _make_handle(obj)

    _logger.info(f'Creating Handle "{handle}"')
    handle_client: PyHandleClient = PyHandleClient(
        "rest").instantiate_with_username_and_password(_config["host"],
                                                       _config["username"],
                                                       _config["password"],
                                                       HTTPS_verify=_config.getboolean("httpsverify"))

    location_base = _get_endpoint(obj)
    location = f"{location_base}/{handle}"

    if location_base is not None:
        # TODO check if handle exists
        handle_client.register_handle(handle, location)

    # TODO Error handling

    return (handle, location)
