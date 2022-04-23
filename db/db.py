import pymysql.cursors
from pymysql.cursors import Cursor
from pymysql.connections import Connection
from datetime import date
from get_config import get_config, ConfigScope
from media.image.photo import Photo
import logging

_logger = logging.getLogger(f"INGEST.{__name__}")
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
        """Commit and close the connection
        """
        self._connection.commit()
        self._connection.close()
    # Photos

    def _make_photo_sql(self, photo: Photo):
        pass

    def get_photo_count_by_date(self, date: date = None):
        cursor: Cursor = self._connection.cursor()
        sql = f'select count(handle) from photos where date_capture="{date.isoformat()}";'
        cursor.execute(sql)
        res = cursor.fetchone()
        return res["count(handle)"]

    def write_photo(self, handle: str, location: str, photo: Photo, check_duplicate: bool = True):
        # Checking for possible duplication
        cursor: Cursor = self._connection.cursor()
        duplicate_sql = f"""SELECT IF((SELECT Count(handle)
        FROM   photos 
        WHERE  ( date_capture = "{photo.date_capture}" 
                AND ( raw_filename = "{photo.raw_filename}" 
                        OR filename = "{photo.filename}" ) ) = 1), 1, 0) AS result; 
        """
        cursor.execute(duplicate_sql)
        has_duplicate = bool(cursor.fetchone()["result"])
        cursor.close()

        if has_duplicate:
            _logger.warn(f'Possible duplicate for file {photo.filename}!')
            if check_duplicate:
                _logger.critical(
                    f'Check Duplicate enabled, skipping "{photo.filename}"')
                return
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
