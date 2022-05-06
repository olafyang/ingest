from .sanity import SanityClient
from .get_config import get_config, ConfigScope
from typing import List, Dict, Union
from pprint import pprint

_config = get_config(ConfigScope.SANITY)
_sanity_client = SanityClient(_config["project_id"], _config["token"])
_dataset = _config["dataset"]

# Create photo from Photo Object


def create_photo(handle: str, asset_id: str, tags: list = None,  artist: str = None, title: str = None) -> dict:
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
        pass
        # FIXME Tags crahing the editdor
        # tags = create_return_tags(tags)
        # mutate["create"]["tags"] = list(
        #     map(lambda e: {"_type": "reference", "_ref": e}, tags))
    if title:
        mutate["create"]["title"] = title
    if artist:
        mutate["create"]["artist"] = artist

    res = _sanity_client.mutate(
        _dataset, mutate, visibility="async", return_ids=True)
    return res


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
            }})

    res = _sanity_client.mutate(_dataset, mutate, return_ids=True)["results"]
    return list(map(lambda e: e["id"], res))
