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
from . import sanity_ingest


_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")
_args: argparse.ArgumentParser = None
_config = get_config()
logging.basicConfig(stream=sys.stdout)
_logger = logging.getLogger("ingest")


def process_photo(path: str, tags: list = None, offline: bool = False, no_compress: bool = False, xmp_file: TextIOWrapper = None, check_duplicates: bool = True, use_sanity: bool = False) -> None:
    """Process a Photo object

    Args:
        path (str): Path of the photo object on the machine
        tags (list, optional): tags to associate with the photo, automatically transform all letters to upper case. Defaults to None.
        offline (bool, optional): disable file upload and database insert. Defaults to False.
        no_compress (bool, optional): disable compress image. Defaults to False.
        xmp_file (TextIOWrapper, optional): read metadata from a xmp file. Defaults to None.
        check_duplicates (bool, optional): check for possible duplications in the system. Defaults to True.
        use_sanity (bool, optional): upload the photo to sanity,io. Defaults to False.
    """
    # TODO add support for non local photo source (Ingest by passing bytes or Buffer)
    _logger.info(f"Start processing {path}")
    photo = Photo(path, xmp_file=xmp_file)
    file_extension = photo.data.format.lower()

    db = DB()
    handle_client = Handle(db)

    if tags:
        tags = list(map(lambda tag: tag.upper(), tags))

    if not offline:
        handle, location = handle_client.register(
            photo, check_duplicates=check_duplicates)

        s3_location = s3io.upload_image(
            f"{handle}.{file_extension}", photo)

        db.write_photo(handle, s3_location, photo,
                       check_duplicate=check_duplicates)

        if tags:
            db.write_tags(handle, tags)

        if use_sanity:
            sanity_ingest.create_photo_from_object(
                handle, photo, tags, photo.artist)
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
    parser.add_argument("--sanity", action=argparse.BooleanOptionalAction,
                        help="Use Sanity.io", default=False)
    parser.add_argument("--nocompress",
                        action=argparse.BooleanOptionalAction, help="Do NOT create CDN version")
    parser.add_argument("--offline",
                        action=argparse.BooleanOptionalAction, help="Do NOT write to database and S3", default=False)
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
    # TODO add artist and title options
    parser.add_argument("--xmp", metavar="XMP FILE",
                        help="Read metadata from XMP file")
    parser.add_argument("mode", help="Media type", choices=["photo", "photos"])
    parser.add_argument("object", help="The Object to process and upload")

    _args = parser.parse_args()

    if _args.tags:
        if True in list(map(lambda x: len(x) > 25, _args.tags)):
            raise KeyError("Length of tag id can not exceed 25")

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

    if not os.path.exists(path):
        raise KeyError(f"Path {path} does not exist")

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
                                  _args.nocompress, xmp_file, check_duplicates=not _args.allow_duplicates, use_sanity=_args.sanity)
                else:
                    process_photo(file, _args.tags,
                                  _args.offline, _args.nocompress, check_duplicates=not _args.allow_duplicates, use_sanity=_args.sanity)
        except exceptions.ObjectDuplicateException:
            _logger.info(f"Skipping {file}")
            skipped_files.append(file)
            continue
    if skipped_files:
        _logger.warn(
            f"Skipped {len(skipped_files)} files, {str(skipped_files)}")
