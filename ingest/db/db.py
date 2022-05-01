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

    def commit(self) -> None:
        """Commit changes
        """
        self._connection.commit()

    def close(self) -> None:
        """Commits and close the connection
        """
        self._connection.commit()
        self._connection.close()

    def write_tags(self, handle: str, tags: list):
        """Associate a objet with given tags

        Args:
            handle (str): handle
            tags (list): List of Tags containing tag id
        """

        # Create new tag if not already exist
        values = ""
        for i, tag in enumerate(tags):
            if i != len(tags) - 1:
                values += f'("{tag}"), '
            else:
                values += f'("{tag}")'

        sql = f'INSERT IGNORE INTO `tags` (`id`) VALUES {values};'
        cursor: Cursor = self._connection.cursor()
        cursor.execute(sql)
        self.commit()
        cursor.close()

        values = ""
        for i, tag in enumerate(tags):
            if i != len(tags) - 1:
                values += f'("{handle}", "{tag}"), '
            else:
                values += f'("{handle}", "{tag}")'
        cursor: Cursor = self._connection.cursor()
        sql = f'INSERT INTO `obj_tag` (`handle`, `tag_id`) VALUES {values};'
        cursor.execute(sql)
        self.commit()
        cursor.close()

    # Photos

    def count_handle(self, date: date, hdl_prefix: str):
        cursor: Cursor = self._connection.cursor()
        sql = f'SELECT count(handle) FROM handles WHERE handle LIKE "{hdl_prefix}/P{date.isoformat()}%" AND idx = 1;'
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
                            AND filename = "{photo.filename}"
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
            if k == "data" or k == "filepath":
                continue
            if v is not None:
                val += f'{k} = "{v}", '
        val += f'handle = "{handle}", location = "{location}"'

        sql = f'INSERT INTO photos SET {val};'
        cursor.execute(sql)
        _logger.info(f'Inserted photo {handle} to DB')
        cursor.close()

    def write_cdn(self, cdn_info: dict):
        cursor: Cursor = self._connection.cursor()

        val = ""
        for k, v in cdn_info.items():
            if v is not None:
                val += f'{k} = "{v}", '

        val = val[0:-2]  # Remove last comma
        val += ";"

        _logger.debug("Writing {} to database".format(cdn_info["cdn_key"]))
        sql = f"INSERT INTO cdn SET {val}"
        cursor.execute(sql)
        cursor.close()
