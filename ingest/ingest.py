from io import TextIOWrapper
import os
import sys
import argparse
import logging
import itertools
from .get_config import get_config
from . import s3io
from .media.image.photo import Photo
from .handle.handle import Handle
from .db.db import DB
from .image_compressor.compressor import compress
import re
from uuid import uuid1
from . import util, exceptions


_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")
_args: argparse.ArgumentParser = None
_config = get_config()
logging.basicConfig(stream=sys.stdout)
_logger = logging.getLogger("ingest")


def process_photo(path: str, tags: list = None, offline: bool = False, no_compress: bool = False, xmp_file: TextIOWrapper = None, check_duplicates: bool = True) -> None:
    _logger.info(f"Start processing {path}")
    photo = Photo(path, xmp_file=xmp_file)
    file_extension = photo.data.format.lower()

    db = DB()
    handle_client = Handle(db)

    if not offline:
        _logger.info("Writing handle record")
        handle, location = handle_client.register(
            photo, check_duplicates=check_duplicates)

        _logger.info("Uploading {} to S3 main bucket {}".format(
            path, _config["S3"]["bucketname"]))
        s3_location = s3io.upload_image(
            f"{handle}.{file_extension}", photo)

        _logger.info("Inserting to database")
        db.write_photo(handle, s3_location, photo,
                       check_duplicate=check_duplicates)

        if tags:
            db.write_tags(handle, tags)
    else:
        _logger.info('"offline" selected, skipping upload"')

    if not no_compress:
        compress_results = compress(photo.data)
        u = str(uuid1()).split("-")[0]
        for item in compress_results:

            if not offline:
                cdn_key = "{}_w{}.{}".format(
                    handle, item[1]["width"], item[1]["content_type"].split("/")[1])
                s3io.upload_cdn(cdn_key, item[0], item[1]["content_type"])
                item[1]["source_handle"] = handle
            else:
                cdn_key = "{}_w{}.{}".format(
                    u, item[1]["width"], item[1]["content_type"].split("/")[1])

            item[1]["cdn_key"] = str(cdn_key)
            item[1]["location"] = "{}/{}".format(
                _config["S3_CDN"]["cdn_endpoint"], cdn_key)
            db.write_cdn(item[1])
    else:
        _logger.info('"nocompress" selected, skipping compress')

    db.close()


if __name__ == "__main__":
    # Parse command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument("--nocompress",
                        action=argparse.BooleanOptionalAction, help="Do NOT create CDN version")
    parser.add_argument("--offline",
                        action=argparse.BooleanOptionalAction, help="Do NOT write to database and S3", default=False)
    parser.add_argument("-m", "--mode", metavar="MODE", required=True,
                        help="Specify the mode to use to process data", choices=["photo", "photos"])
    parser.add_argument(
        "-t", "--tag", action=argparse._AppendAction, help="Set tag", dest="tags")
    # Recursivly process files
    parser.add_argument("-r", "--recursive", metavar="Find files recursively",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--allow-hidden", help="Process hidden files",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--debug", metavar="Enable Debug",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--allow-duplicates", action=argparse.BooleanOptionalAction,
                        help="Skip potential duplication test", default=False)
    parser.add_argument("--xmp", metavar="XMP FILE",
                        help="Read metadata from XMP file")
    parser.add_argument("object", help="The Object to process and upload")

    _args = parser.parse_args()

    # Toggle logging mode
    if _args.debug:
        _logger.setLevel(logging.DEBUG)
        _logger.debug("Debug enabled")
    else:
        _logger.setLevel(logging.INFO)

    # Validate config and arguments
    if "HANDLE" not in _config:
        _logger.critical('Section "HANDLE" not in config file')
        exit()
    if "DB" not in _config:
        _logger.critical('Section "DB" not in config file')
        exit()
    if "S3" not in _config:
        _logger.critical('Section "S3_MAIN" not in config file')
        exit()
    if ("S3_CDN" not in _config and not _args.nocompress) or ("S3_CDN" in _config and _config.getboolean("S3_MAIN", "CDNSeperateKey", fallback=False) is True):
        _logger.critical('Section "S3_CDN" not in config file')
        exit()

    # Run

    # Get files to process
    path = os.path.abspath(_args.object)
    files_to_process = []
    if os.path.isfile(path):
        _logger.debug(f"Adding file {path} to queue")
        files_to_process.append(path)
    else:
        # Get all files within the directory
        if _args.recursive:
            _logger.debug(
                f"Recursive, walking through all sub directories of {path}")
            walk = os.walk(path)
        else:
            _logger.debug(f"Walking through directory {path}")
            walk = [next(os.walk(path))]

        for batch in walk:
            # Get full path of files
            files_in_directory = batch[2]

            # Remove hidden files if not specified
            if not _args.allow_hidden:
                files_in_directory = [
                    n for n in files_in_directory if _HIDDEN_FILE_PATTERN.match(n)]

            # Convert filenames to full path
            files_in_directory = list(map(
                lambda f, p: f"{p}/{f}", files_in_directory, itertools.repeat(batch[0], len(files_in_directory))))

            files_to_process += files_in_directory

    _logger.info(f"Counted {len(files_to_process)} files, start processing")

    if _args.mode is None:
        raise NameError("No mode given")

    skipped_files = []
    # Start processing
    for file in files_to_process:
        try:
            if _args.mode == "photo" or _args.mode == "photos":
                xmp_file = None
                if _args.xmp:
                    if len(files_to_process) > 1:
                        raise KeyError(
                            "Only one photo allowed if using custom XMP file.")
                    _logger.debug(f"Using external XMP file {_args.xmp}")
                    xmp_file = open(_args.xmp, "r")
                    process_photo(file, _args.tags, _args.offline,
                                  _args.nocompress, xmp_file, check_duplicates=not _args.allow_duplicates)
                else:
                    process_photo(file, _args.tags,
                                  _args.offline, _args.nocompress, check_duplicates=not _args.allow_duplicates)
        except exceptions.ObjectDuplicateException:
            _logger.info(f"Skipping {file}")
            skipped_files.append(file)
            continue
    if skipped_files:
        _logger.warn(f"Skipped {len(skipped_files)} files, {str(skipped_files)}")
