import os
import argparse
import logging
import itertools
from get_config import get_config
import s3io
from PIL import Image
from media.photo import Photo
import re


_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")


def process_photo(photo: Photo):
    file_extension = photo.data.format.lower()
    s3io.upload_image(f"test.{file_extension}", photo)
    pass


if __name__ == "__main__":

    # Parse command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nocompress",
                        action=argparse.BooleanOptionalAction, help="Do NOT create CDN version")
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

    args = parser.parse_args()

    # Toggle logging mode
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

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
    if ("S3_CDN" not in config and not args.nocompress) or ("S3_CDN" in config and config.getboolean("S3_MAIN", "CDNSeperateKey", fallback=False) is True):
        logging.critical('Section "S3_CDN" not in config file')
        exit()

    # Run

    # Get files to process
    path = os.path.abspath(args.object)
    files_to_process = []
    if os.path.isfile(path):
        logging.debug(f"Adding file {path} to queue")
        files_to_process.append(path)
    else:
        # Get all files within the directory
        if args.recursive:
            logging.debug(f"Recursive, walking through all sub directories of {path}")
            walk = os.walk(path)
        else:
            logging.debug(f"Walking through directory {path}")
            walk = [next(os.walk(path))]

        for batch in walk:
            # Get full path of files
            files_in_directory = batch[2]

            # Remove hidden files if not specified
            if not args.allow_hidden:
                files_in_directory = [
                    n for n in files_in_directory if _HIDDEN_FILE_PATTERN.match(n)]

            # Convert filenames to full path
            files_in_directory = list(map(
                lambda f, p: f"{p}/{f}", files_in_directory, itertools.repeat(batch[0], len(files_in_directory))))

            files_to_process.append(files_in_directory)

        logging.info(f"Counted {len(files_to_process)}, start processing")

    # Start processing
    for file in files_to_process:
        if args.mode == "photo" or args.mode == "photos":
            p = Photo(file)
            process_photo(p)
