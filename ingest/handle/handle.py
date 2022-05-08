import re
from ..media.image.photo import Photo
from ..db.db import DB
from ..get_config import get_config, ConfigScope
from typing import Union
from pyhandle.handleclient import PyHandleClient
import logging
from datetime import date
from .. import util, exceptions

_logger = logging.getLogger(__name__)
_config = get_config(ConfigScope.HANDLE)


class Handle():

    _db: DB = None
    _handle_client: PyHandleClient = None

    def __init__(self, db: DB):
        self._db = db
        https_verify = _config.get("httpsverify")
        try:
            https_verify = bool(https_verify)
        except ValueError:
            pass

        self._handle_client: PyHandleClient = PyHandleClient(
            "rest").instantiate_with_username_and_password(_config["host"],
                                                           _config["username"],
                                                           _config["password"],
                                                           HTTPS_verify=https_verify)

    def _make_handle(self, obj: Photo, check_duplicates: bool = True) -> str:
        """Make a handle string using default definition based on requirement

        Args:
            obj (Photo): The object to create handle from
            check_duplicates (bool, optional): Check for potential duplicates. Defaults to True.

        Raises:
            exceptions.ObjectDuplicateException: If check_duplicates is True and a potential duplicate exists

        Returns:
            str: Handle str in the format of prefix/suffix
        """
        if isinstance(obj, Photo):
            obj: Photo
            db = DB()

            # Format "P<DATE>.I<ID>"
            if obj.date_capture:
                obj_date = obj.date_capture
            elif obj.date_export:
                obj_date = obj.date_export
            elif hasattr(obj, "filepath"):
                date_regex = r"(\d\d\d\d)-(\d\d)-(\d\d)"
                res = re.search(date_regex, obj.filepath)
                if res:
                    try:
                        obj_date = date(
                            int(res.group(1)), int(res.group(2)), int(res.group(3)))
                    except ValueError:
                        obj_date = date.today()
            else:
                obj_date = date.today()

            if db.photo_has_duplicate(obj):
                _logger.warn(f'Possibe duplicates for "{obj.filename}"')
                if check_duplicates:
                    raise exceptions.ObjectDuplicateException

            prefix = _config["prefix"]
            handle = f"{prefix}/P{obj_date.isoformat()}.I{db.count_handle(obj_date, prefix) + 1}"
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
        if location is None:
            location = "{}/view/{}".format(util.get_endpoint(obj),
                                           handle.split("/")[1])

        self._handle_client.register_handle(handle, location)
        _logger.info(f'Handle "{handle}" created! Pointing to "{location}"')
        # TODO Error handling

        return (handle, location)
