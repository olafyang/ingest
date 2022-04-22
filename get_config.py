from configparser import ConfigParser
from enum import Enum
import logging
import os


class ConfigScope(Enum):
    S3 = 1
    S3_CDN = 2
    DB = 3
    HANDLE = 4
    FULL = 5


def _parse_config():
    config = ConfigParser()

    logging.debug("Reading config file")
    config_file_path = os.path.abspath("config.ini")
    config.read(config_file_path)
    if not config.sections():
        logging.critical(
            f"No config file found, generating example file at {config_file_path}")

        config["HANDLE_SERVER"] = {
            "location": "Handle Server REST API endpoint Location",
            "username": "Handle Server Username",
            "password": "Handle Server Password",
            "httpsverify": True
        }
        config["DB"] = {
            "location": "Database location",
            "username": "Database Username",
            "password": "Database Password"
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
            "bucketname": "CDN Bucket Name"
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

    return None
