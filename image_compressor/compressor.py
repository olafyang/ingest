from pickletools import optimize
from urllib import request
from urllib.parse import urlparse
import argparse
import os
import sys
import io
from typing import Optional, NoReturn, Union
import boto3
from PIL import Image


class UnsupportedProtocol(Exception):
    pass


s3 = boto3.client("s3",
                  endpoint_url="https://s3.eu-central-003.backblazeb2.com",
                  aws_access_key_id=os.environ.get("ACCESS_KEY_ID"),
                  aws_secret_access_key=os.environ.get("ACCESS_KEY_SECRET"))


def download_image_s3(bucket_name: str, key: str) -> Image:
    """
    Download an image from a given S3 bucket
    :param bucket_name: S3 bucket name
    :param key: S3 object key
    :return: PIL Image Object
    """
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    image = Image.open(io.BytesIO(obj["Body"].read()))
    return image


def resize(image: Image, width: int) -> Image:
    """
    Resize an PIL Image object proportionally based on a given width
    :param image: image to resize
    :param width: width of desired output image
    :return:
    """
    old_size = image.size
    new_size = (width, int(old_size[1] * (width / old_size[0])))
    image = image.resize(new_size)
    return image


def save_io(image: Image, img_format: str = "JPEG", quality: int = 85) -> io.BytesIO:
    """
    Save an PIL Image to bytesIO
    :param image: source image
    :param img_format: output image format, defaults JPEG
    :param quality: image quality if using jpg, defaults to 85
    :return:
    """
    img_format = img_format.upper()

    b = io.BytesIO()
    if img_format == "PNG":
        image.save(b, format="PNG", optimize=True)
    else:
        image.save(b, format="JPEG", quality=quality, optimize=True)

    b.seek(0)
    return b


def upload_s3(bucket_name: str, body: Union[Image.Image, io.BytesIO], key: str, fmt: str) -> NoReturn:
    """
    Uploads a PIL Image or BytesIO Object to given S3 bucket
    :param bucket_name: S3 bucket name
    :param body: Image or BytesIO object
    :param key:  S3 object key
    :param fmt: Content-Type Header
    """
    if isinstance(body, Image.Image):
        body = save_io(body)
        fmt = "JPEG"

    fmt = fmt.upper()

    fmt = Image.MIME[fmt]

    res = s3.put_object(Body=body.getvalue(
    ), Key=key, Bucket=args.bucket_upload, ContentType=fmt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quality", type=int,
                        help="Quality setting of output image", default=85)
    parser.add_argument("-x", "--resize", type=int,
                        help="Output image x dimension size, scales y automatically")
    parser.add_argument(
        "-t", "--type", choices=["png", "jpg", "jpeg"], help="Output image format, can be either jpg or png",
        default="jpg")
    parser.add_argument(
        "image", help="Source image location, can either be local or via http")
    parser.add_argument(
        "-d", "--use-s3", help="Use a S3 bucket as image source", metavar="BUCKET NAME", dest="bucket_download")
    parser.add_argument("-u", "--upload-s3",
                        help="Upload output image to a S3 bucket", metavar="BUCKET NAME", dest="bucket_upload")
    args = parser.parse_args()

    if args.bucket_download:

        img = download_image_s3(args.bucket_download, args.image)
    else:
        img = Image.open(open(args.image, "rb"))

    file_basename = "".join(args.image.split(".")[0:-1])
    file_extension = args.image.split(".")[-1].lower()

    if file_extension == "png":
        out_format = "PNG"
    elif file_extension == "jpg":
        out_format = "JPEG"
    else:
        out_format = "JPEG"

    if args.resize:
        img = resize(img, 1000)

    if args.bucket_upload:
        if args.type.upper() == "PNG" or out_format == "PNG":
            out = save_io(img, "PNG")
        else:
            out = save_io(img, "JPEG", args.quality)
        upload_s3(args.bucket_upload, out, os.path.basename(args.image), fmt=out_format)
