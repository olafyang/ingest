from io import BytesIO
import boto3
from typing import Union
from PIL import Image
from .media.image.photo import Photo
from .get_config import get_config, ConfigScope
import logging

_logger = logging.getLogger(f"INGEST.{__name__}")

_config = get_config(ConfigScope.S3)
_config_cdn = get_config(ConfigScope.S3_CDN)

_s3client = boto3.client(
    "s3",
    endpoint_url=_config["endpoint"],
    aws_access_key_id=_config["accesskeyid"],
    aws_secret_access_key=_config["accesskeysecret"]
)

_s3client_cdn = None
if _config.getboolean("cdnseperatekey", fallback=False):
    _s3client_cdn = boto3.client(
        "s3",
        endpoint_url=_config_cdn["endpoint"],
        aws_access_key_id=_config_cdn["accesskeyid"],
        aws_secret_access_key=_config_cdn["accesskeysecret"]
    )
else:
    _s3client_cdn = _s3client

_main_bucket_name = _config["bucketname"]
_cdn_bucket_name = _config_cdn["bucketname"]


def upload_image(key: str, data: Union[Photo, Image.Image], content_type: str = None):
    if isinstance(data, Image.Image) and content_type is None:
        content_type = f"image/{data.format.lower()}"
        raw_data = BytesIO()
        data.save(raw_data)
        raw_data.seek(0)
    else:
        content_type = data.content_type
        raw_data = data.save_io()

    _logger.debug(f"Content Type is {content_type}")

    _logger.info('Starting upload')
    res = _s3client.put_object(
        Body=raw_data.getvalue(),
        Key=key,
        Bucket=_main_bucket_name,
        ContentType=content_type
    )
    _logger.info("S3 Upload completed")
    return f"s3://{_main_bucket_name}/{key}"


def upload_cdn(key: str, data=Union[Photo, Image.Image], content_type: str = None):
    if isinstance(data, Image.Image) and content_type is None:
        content_type = f"image/{data.format.lower()}"
        raw_data = BytesIO()
        data.save(raw_data)
        raw_data.seek(0)
    else:
        content_type = data.content_type
        raw_data = data.save_io()

    res = _s3client_cdn.put_object(
        Body=raw_data.getvalue(),
        Key=key,
        Bucket=_cdn_bucket_name,
        ContentType=content_type
    )

    # TODO return location
