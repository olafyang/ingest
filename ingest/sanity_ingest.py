from .sanity import SanityClient
from .get_config import get_config, ConfigScope
from typing import List, Dict, Union
from ingest.media.image.photo import Photo
from ingest.image_compressor import compressor
from . import util
import logging

_config = get_config(ConfigScope.SANITY)
_sanity_client = SanityClient(_config["project_id"], _config["token"])
_dataset = _config["dataset"]
_logger = logging.getLogger(__name__)

# Create photo from Photo Object


def create_photo_from_object(handle: str, photo: Photo, tags: List[str] = None, artist: str = None, title: str = None):
    image_data = compressor.save_io(photo.data)
    asset_id = _sanity_client.upload_image(
        _dataset, image_data, util.convert_to_mime(photo.data.format))
    create_photo(handle, asset_id, tags, artist, title)


def create_photo(handle: str, asset_id: str, tags: List[str] = None, artist: str = None, title: str = None) -> dict:
    """Create an entry in the Photo table

    Args:
        handle (str): Handle of the photo
        asset_id (str): Asset of the uploaded photo image
        tags (list, optional): list of tag ids. Defaults to None.
        artist (str, optional): The artist of the photo. Defaults to None.
        title (str, optional): The title of the photo. Defaults to None.

    Returns:
        dict: sanity api response parsed to dict
    """
    mutate = {
        "create": {
            "_type": "photo",
            "objectID": handle.split("/")[1],
            "hdlPrefix": handle.split("/")[0],
            "photo": {"_type": "image",
                      "asset": {
                          "_type": "reference",
                          "_ref": f"{asset_id}"
                      }
                      }
        }
    }

    if tags:
        tags = create_return_tags(tags)
        mutate["create"]["tags"] = list(
            map(lambda e: {"_type": "reference", "_ref": e}, tags))
    if title:
        mutate["create"]["title"] = title
    if artist:
        mutate["create"]["artist"] = artist

    _logger.info(f"Inserting to sanity dataset {_dataset}")
    res_doc = _sanity_client.mutate(
        _dataset, mutate, visibility="async", return_ids=True, auto_generate_array_keys=True)
    return res_doc


def create_return_tags(tags: Union[List[Dict[str, str]], List[str]]) -> List[str]:
    """Create tags and reutrn their id and name, only return the id and name if tag already exist.
    Automaticlly append "tag_" to the start of id when creating if not already given

    Args:
        tags (Union[List[Dict[str, str]], List[str]]): list dictionary containing tag_id and tag_name {"id": "tag:sample", "name": "sample tag"} || list containing tag ids

    Returns:
        List[Dict[str, str]]: List with tag ids
    """
    mutate = []
    for tag in tags:
        if isinstance(tag, dict):
            if tag["id"][0:4] != "tag_":
                tag["id"] = "tag_" + tag["id"]

            mutate.append({"createIfNotExists": {
                "_type": "tag",
                "_id": tag["id"],
                "name": tag["name"]
            }})
        else:
            if tag[0:4] != "tag_":
                tag = "tag_" + tag

            mutate.append({"createIfNotExists": {
                "_type": "tag",
                "_id": tag,
                "name": tag
            }})

    res = _sanity_client.mutate(_dataset, mutate, return_ids=True)["results"]
    return list(map(lambda e: e["id"], res))
