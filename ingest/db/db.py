import pymysql.cursors
from pymysql.cursors import Cursor
from pymysql.connections import Connection
from datetime import date
from ..get_config import get_config, ConfigScope
from ..media.image.photo import Photo
import logging
from .. import exceptions

_logger = logging.getLogger(__name__)
_config = get_config(ConfigScope.DB)


class DB:
    _connection: Connection = None

    def __init__(self):
        self._connection = pymysql.connect(host=_config["host"],
                                           user=_config["username"],
                                           password=_config["password"],
                                           db=_config["db"],
                                           charset="utf8mb4",
                                           cursorclass=pymysql.cursors.DictCursor
                                           )

    def close(self) -> None:
        """Commits and close the connection
        """
        self._connection.commit()
        self._connection.close()

    # Photos

    def count_photo(self, date: date, hdl_prefix: str):
        cursor: Cursor = self._connection.cursor()
        sql = f'select count(handle) from photos where handle like "{hdl_prefix}/P{date.isoformat()}%";'
        cursor.execute(sql)
        res = cursor.fetchone()
        cursor.close()
        return res["count(handle)"]

    # Cambile thest 2 functions ??

    def photo_has_duplicate(self, photo: Photo) -> bool:
        """Checks if a photo has possible duplicates using date and filenames.

        Args:
            photo (Photo): The Photo class to check

        Returns:
            bool: True if possible duplicates exists, False if otherwise
        """
        if photo.date_capture:
            handle_date = photo.date_capture
        elif photo.date_export:
            handle_date = photo.date_export
        else:
            handle_date = date.today()

        cursor: Cursor = self._connection.cursor()
        duplicate_sql = f"""
            SELECT IF(
            (
                SELECT Count(handle)
                FROM photos
                WHERE (
                        handle like "%P{handle_date.isoformat()}%"
                        AND (
                            raw_filename = "{photo.raw_filename}"
                            OR filename = "{photo.filename}"
                        )
                    ) = 1
            ),
            1,
            0
            ) AS result;"""
        cursor.execute(duplicate_sql)
        cursor.close()
        return bool(cursor.fetchone()["result"])

    def write_photo(self, handle: str, location: str, photo: Photo, check_duplicate: bool = True):
        # Checking for possible duplication
        if self.photo_has_duplicate(photo):
            _logger.warn(f'Possible duplicate for file {photo.filename}!')
            if check_duplicate:
                raise exceptions.ObjectDuplicateException
        # Inserting data
        cursor: Cursor = self._connection.cursor()
        # Making column values
        val = ""
        for k, v in photo.__dict__.items():
            if k == "data":
                continue
            if v is not None:
                val += f'{k} = "{v}", '
        val += f'handle = "{handle}", location = "{location}"'

        sql = f'INSERT INTO photos SET {val};'
        cursor.execute(sql)
        print(f'Inserted photo {handle}')
        cursor.close()
