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
from . import util, exceptions


_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")
_args: argparse.ArgumentParser = None
_config = get_config()
logging.basicConfig(stream=sys.stdout)
_logger = logging.getLogger("ingest")


def process_photo(path: str, offline: bool = False, no_compress: bool = False) -> None:
    _logger.info(f"Start processing {path}")
    photo = Photo(path)
    file_extension = photo.data.format.lower()

    db = DB()
    handle_client = Handle(db)

    if not offline:
        _logger.info("Writing handle record")
        handle, location = handle_client.register(photo)

        _logger.info("Uploading %s to S3 main bucket %s".format(
            path, _config["S3"]["bucketname"]))
        s3_location = s3io.upload_image(
            f"{handle}.{file_extension}", photo, skip_upload=offline)

        _logger.info("Inserting to database")
        db.write_photo(handle, s3_location, photo)
    else:
        _logger.info('"noupload" selected, skipping upload"')

    if not no_compress:
        c = compress(photo.data)
        for i in enumerate(c):
            with open(f"{i[0]}.jpeg", "wb") as file:
                file.write(i[1][0].read())
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
    parser.add_argument("-m", "--mode", metavar="MODE",
                        help="Specify the mode to use to process data", choices=["photo", "photos"])
    # Recursivly process files
    parser.add_argument("-r", "--recursive", metavar="Find files recursively",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--allow-hidden", help="Process hidden files",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--debug", metavar="Enable Debug",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("object", help="The Object to process and upload")

    _args = parser.parse_args()

    # Toggle logging mode
    if _args.debug:
        _logger.setLevel(logging.DEBUG)
        _logger.debug("Debug enabled")

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

            files_to_process.append(files_in_directory)

    _logger.info(f"Counted {len(files_to_process)} files, start processing")

    if _args.mode is None:
        raise NameError("No mode given")
    # Start processing
    for file in files_to_process:
        if _args.mode == "photo" or _args.mode == "photos":
            process_photo(file, _args.offline)
