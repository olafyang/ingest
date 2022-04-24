import os
import argparse
import logging
import itertools
from .get_config import get_config
from . import s3io
from .media.image.photo import Photo
from .handle.handle import Handle
from .db.db import DB
import re
from . import util, exceptions


_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")
_args: argparse.ArgumentParser = None
_logger = logging.getLogger("INGEST")


def process_photo(path: str, skip_upload: bool = False) -> None:
    photo = Photo(path)
    file_extension = photo.data.format.lower()

    db = DB()
    handle_client = Handle(db)

    handle, location = handle_client.register(photo)

    _logger.info(f'Uploading "{path}"')
    s3_location = s3io.upload_image(
        f"{handle}.{file_extension}", photo, skip_upload=skip_upload)

    db.write_photo(handle, s3_location, photo)
    db.close()


if __name__ == "__main__":
    # Parse command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument("--nocompress",
                        action=argparse.BooleanOptionalAction, help="Do NOT create CDN version")
    parser.add_argument("--noupload",
                        action=argparse.BooleanOptionalAction, help="Do NOT upload object to S3", default=False)
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
    logging.basicConfig()
    if _args.debug:
        _logger.setLevel(logging.DEBUG)
        _logger.debug("Debug enabled")

    config = get_config()

    # Validate config and arguments
    if "HANDLE" not in config:
        _logger.critical('Section "HANDLE" not in config file')
        exit()
    if "DB" not in config:
        _logger.critical('Section "DB" not in config file')
        exit()
    if "S3" not in config:
        _logger.critical('Section "S3_MAIN" not in config file')
        exit()
    if ("S3_CDN" not in config and not _args.nocompress) or ("S3_CDN" in config and config.getboolean("S3_MAIN", "CDNSeperateKey", fallback=False) is True):
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

    # Start processing
    for file in files_to_process:
        if _args.mode == "photo" or _args.mode == "photos":
            process_photo(file, _args.noupload)
