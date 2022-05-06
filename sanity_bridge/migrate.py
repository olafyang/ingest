import pymysql
import requests
from pymysql.cursors import Cursor
from ingest.sanity import SanityClient
from ingest.sanity_ingest import create_photo
from ingest.get_config import get_config, ConfigScope

_db_config = get_config(ConfigScope.DB)
_sanity_config = get_config(ConfigScope.SANITY)

connection = pymysql.connect(host=_db_config["host"],
                             user=_db_config["username"],
                             password=_db_config["password"],
                             db="handle",
                             charset="utf8mb4",
                             cursorclass=pymysql.cursors.DictCursor
                             )
cursor: Cursor = connection.cursor()


cursor.execute("""SELECT a.source_handle AS handle,
    a.width,
    a.location
FROM cdn a
    INNER JOIN (
        SELECT source_handle,
            MAX(width) width
        FROM cdn
        GROUP BY source_handle
    ) b ON a.source_handle = b.source_handle
    AND a.width = b.width;""")
photos = cursor.fetchall()
cursor.close()

sc = SanityClient(_sanity_config["project_id"], _sanity_config["token"])

for item in photos:
    handle = item["handle"]
    location = item["location"]

    res = requests.get(location)

    print(f"Uploading image {location} to sanity")
    asset_id = sc.upload_image(
        _sanity_config["dataset"], res.content, res.headers["Content-Type"])

    print(f"Creating Photo {handle}")
    create_photo(handle, asset_id, artist="OLAF YANG")
