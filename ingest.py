import os
import argparse
import logging
import itertools
from get_config import get_config
import s3io
from media.image.photo import Photo
import re


_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")
_args: argparse.ArgumentParser = None


def process_photo(photo: Photo):
    file_extension = photo.data.format.lower()
    if not _args.noupload:
        s3io.upload_image(f"test.{file_extension}", photo)
    else:
        logging.info('Option "noupload" selected, skipping upload')
    pass


if __name__ == "__main__":
    logging.basicConfig()

    # Parse command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument("--nocompress",
                        action=argparse.BooleanOptionalAction, help="Do NOT create CDN version")
    parser.add_argument(
        "--noupload", action=argparse.BooleanOptionalAction, help="Do NOT upload object to S3")
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
        logging.root.setLevel(logging.DEBUG)
        logging.debug("Debug enabled")

    config = get_config()

    # Validate config and arguments
    if "HANDLE_SERVER" not in config:
        logging.critical('Section "HANDLE_SERVER" not in config file')
        exit()
    if "DB" not in config:
        logging.critical('Section "DB" not in config file')
        exit()
    if "S3" not in config:
        logging.critical('Section "S3_MAIN" not in config file')
        exit()
    if ("S3_CDN" not in config and not _args.nocompress) or ("S3_CDN" in config and config.getboolean("S3_MAIN", "CDNSeperateKey", fallback=False) is True):
        logging.critical('Section "S3_CDN" not in config file')
        exit()

    # Run

    # Get files to process
    path = os.path.abspath(_args.object)
    files_to_process = []
    if os.path.isfile(path):
        logging.debug(f"Adding file {path} to queue")
        files_to_process.append(path)
    else:
        # Get all files within the directory
        if _args.recursive:
            logging.debug(
                f"Recursive, walking through all sub directories of {path}")
            walk = os.walk(path)
        else:
            logging.debug(f"Walking through directory {path}")
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

        logging.info(f"Counted {len(files_to_process)}, start processing")

    # Start processing
    for file in files_to_process:
        if _args.mode == "photo" or _args.mode == "photos":
            p = Photo(file)
            process_photo(p)
