import pymysql.cursors
from pymysql.connections import Connection
from datetime import date
from get_config import get_config, ConfigScope
from media.image.photo import Photo

_config = get_config(ConfigScope.DB)
_connection: Connection = pymysql.connect(host=_config["host"],
                                          user=_config["username"],
                                          password=_config["password"],
                                          db=_config["db"],
                                          charset="utf8mb4",
                                          cursorclass=pymysql.cursors.DictCursor
                                          )


# Photos

def _make_photo_sql(photo: Photo):
    pass


def get_photo_count_by_date(date: date = None):
    cursor = _connection.cursor()
    sql = f'select count(handle) from photos where date_capture="{date.isoformat()}";'
    cursor.execute(sql)
    res = cursor.fetchone()
    return res["count(handle)"]


def write_photo():
    # TODO Check for possible duplicates by checking same filename or raw_filename under the same date
    cursor = _connection.cursor()
    sql = f"INSERT INTO `photos`"
