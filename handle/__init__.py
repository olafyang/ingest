from pyhandle.handleclient import PyHandleClient
from pyhandle import handleexceptions
from typing import Union
from io import BytesIO
import logging


class HandleManager:
    _handle_client: PyHandleClient = None

    def __init__(self, server: str, username: str, password: str, verify_https: bool = True) -> None:
        self._handle_client = PyHandleClient("rest").instantiate_with_username_and_password(
            server, username, password, HTTPS_verify=verify_https)
