import os
import argparse
import pymysql
import pyhandle
import logging
from io import BytesIO
from typing import Union
import itertools
import re

# logging.basicConfig(level=logging.DEBUG)

HDL_AUTHFILE = os.environ.get("HDL_AUTHFILE")
RE_HIDDEN_FILE_PATTERN = re.compile(r".+[\.].+")


class IngestTool():
    def __init__(self, client: pyhandle.handleclient.PyHandleClient):
        self.client = client

    def upload_image(self, ):
        pass

    def upload_cdn(self, ):
        pass

    def add_photo(self, handle: str, target: str, photo: Union[str, BytesIO]):
        if not isinstance(photo, BytesIO):
            logging.info("Opening file")
            photo = open(photo, "rb")

        #  TODO: add upload
        # TODO: add optional compression and cdn upload
        self.client.register_handle(handle, target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nocompress",
                        action=argparse.BooleanOptionalAction, help="Do NOT create CDN version")
    parser.add_argument("-s", "--server", metavar="Handle Server Location",
                        default="https://195.201.30.29:8000")
    parser.add_argument("-m", "--mode", metavar="MODE",
                        help="Specify the mode to use to process data", choices=["photo", "photos"])
    parser.add_argument("-r", "--recursive", metavar="Find files recursively",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--allow-hidden", help="Process hidden files",
                        action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    parser.add_argument("object", help="The Object to process and upload")

    args = parser.parse_args()

    if args.username and args.password:
        # Using Basic Auth
        client = pyhandle.handleclient.PyHandleClient(
            "rest").instantiate_with_username_and_password(args.server, args.username, args.password, HTTPS_verify=False)
    else:
        # Using Client Certificate
        # TODO: Investigate Auth Flow
        logging.critical("Not Yet Implemented")
        raise Exception("Not Yet Implemented")

    ingest_tool = IngestTool(client)

    path = os.path.abspath(args.object)
    files_to_process = []
    if os.path.isfile(path):
        files_to_process.append(path)
    else:
        # Get all files within the directory
        if args.recursive:
            walk = os.walk(path)
        else:
            walk = [next(os.walk(path))]

        for batch in walk:
            # Get full path of files
            files_in_directory = batch[2]

            # Remove hidden files if not specified
            if not args.allow_hidden:
                files_in_directory = [
                    n for n in files_in_directory if RE_HIDDEN_FILE_PATTERN.match(n)]

            # Convert filenames to full path
            files_in_directory = list(map(
                lambda f, p: f"{p}/{f}", files_in_directory, itertools.repeat(batch[0], len(files_in_directory))))

            files_to_process = files_to_process + files_in_directory

    print(files_to_process)
