from configparser import ConfigParser
from enum import Enum
import logging
import os

_logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    S3 = 1
    S3_CDN = 2
    DB = 3
    HANDLE = 4
    FULL = 5
    SANITY = 6


def _parse_config():
    config = ConfigParser()

    _logger.debug("Reading config file")

    if os.path.isfile(os.path.expanduser("~/.ingest.ini")):
        config_file_path = os.path.abspath(os.path.expanduser("~/.ingest.ini"))
    elif os.path.isfile("./config.ini"):
        config_file_path = os.path.abspath("./config.ini")
    else:
        _logger.critical(
            f"No config file found.")
    config.read(config_file_path)
    # TODO Valid sections
    if not config.sections():
        _logger.critical(
            f"Config file not valid, generating example file at {config_file_path}")

        config["HANDLE"] = {
            "host": "Handle Server REST API endpoint Location",
            "username": "Handle Server Username",
            "password": "Handle Server Password",
            "prefix": "Handle Prefix",
            "httpsverify": True
        }
        config["DB"] = {
            "host": "Database location",
            "username": "Database Username",
            "password": "Database Password",
            "db": "Database Name"
        }
        config["S3"] = {
            "endpoint": "AWS Endpoint",
            "accessKeyID": "AWS Access Key ID",
            "accessKeySecret": "AWS Access Key Secret",
            "bucketname": "Main Bucket Name",
            "cdnseperateKey": False
        }
        config["S3_CDN"] = {
            "endpoint": "AWS Endpoint",
            "accessKeyID": "AWS Access Key ID",
            "accessKeySecret": "AWS Access Key Secret",
            "bucketname": "CDN Bucket Name",
            "cdn_endpoint": "CDN Endpoint"
        }
        config["SANITY"] = {
            "token": "Sanity token",
            "project_id": "Project id"
        }
        with open(config_file_path, "w") as config_file:
            config.write(config_file)
            exit()

    return config


_config: ConfigParser = _parse_config()


def get_config(scope: ConfigScope = ConfigScope.FULL) -> ConfigParser:
    if scope == ConfigScope.FULL:
        return _config
    elif scope == ConfigScope.DB:
        return _config["DB"]
    elif scope == ConfigScope.HANDLE:
        return _config["HANDLE"]
    elif scope == ConfigScope.S3:
        return _config["S3"]
    elif scope == ConfigScope.S3_CDN:
        return _config["S3_CDN"]
    elif scope == ConfigScope.SANITY:
        return _config["SANITY"]

    return None
