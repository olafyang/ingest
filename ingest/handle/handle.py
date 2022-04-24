import sys
from ..media.image.photo import Photo
from ..db.db import DB
from ..get_config import get_config, ConfigScope
from typing import Union
from pyhandle.handleclient import PyHandleClient
import logging
from datetime import date
from .. import util, exceptions

_logger = logging.getLogger(f"INGEST.{__name__}")
_config = get_config(ConfigScope.HANDLE)


class Handle():

    db: DB = None

    def __init__(self, db: DB):
        self.db = db

    def _make_handle(self, obj: Photo, check_duplicates: bool = True):
        """Make a handle string using default definition based on requirement

        :param obj
        """
        if isinstance(obj, Photo):
            onj: Photo
            db = DB()

            # Format "P<DATE>.I<ID>"
            if obj.date_capture:
                obj_date = obj.date_capture
            elif obj.date_export:
                obj_date = obj.date_export
            else:
                obj_date = date.today()

            if db.photo_has_duplicate(obj):
                _logger.warn(f'Possibe duplicates for "{obj.filename}"')
                if check_duplicates:
                    raise exceptions.ObjectDuplicateException

            prefix = _config["prefix"]
            handle = f"{prefix}/P{obj_date.isoformat()}.I{db.count_photo(obj_date) + 1}"
            return handle

    def register(self, obj: Photo, location: str = None, name: str = None, check_duplicates: bool = True) -> tuple:
        """Register a new handle using an object and it's corrisponding suffix schema.
        The default schema can be overwritten using the name argument.

        Args:
            obj (Photo): Photo Object
            location (str, optional): The target location the handle will point to. A location will be created based on the specificationif is None. Defaults to None
            name (str, optional): Custom Name. Defaults to None.
            check_duplicates (bool, optional): Skip handle creation if possible duplicates exist. Defaults to True.

        Returns:
            tuple: A tuple containing two values, First element is the newly created handle,
            Second element is the location of which the handle is pointing to
        """
        if name:
            _logger.debug("Using custom name for suffix")
            handle = f'{_config["prefix"]}/{name}'
        else:
            _logger.debug("Making suffix from object")
            handle = self._make_handle(obj, check_duplicates)

        if handle is None:
            return

        _logger.info(f'Creating Handle "{handle}"')
        handle_client: PyHandleClient = PyHandleClient(
            "rest").instantiate_with_username_and_password(_config["host"],
                                                           _config["username"],
                                                           _config["password"],
                                                           HTTPS_verify=_config.getboolean("httpsverify"))

        if location is None:
            location = f"{util.get_endpoint(obj)}/{handle}"

        handle_client.register_handle(handle, location)
        _logger.info(f'Handle "{handle}" created! Pointing to "{location}"')
        # TODO Error handling

        return (handle, location)
