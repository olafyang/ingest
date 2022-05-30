from io import BytesIO
import json
import requests
from typing import Union
import logging

_logger = logging.getLogger(__name__)


class SanityClientException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    pass


class SanityUnauthorizedException(SanityClientException):
    pass


class SanityClient:
    def __init__(self, project_id: str, token: str, api_version="v2021-06-07", use_cdn=False):
        self._auth_token = token
        self._api_version = api_version
        self._use_cdn = use_cdn
        if use_cdn:
            self._url = f"https://{project_id}.apicdn.sanity.io/{api_version}"
        else:
            self._url = f"https://{project_id}.api.sanity.io/{api_version}"

    def query(self, dataset: str, query: str) -> Union[None, list]:
        res = requests.get(f"{self._url}/data/query/{dataset}",
                           headers={
                               "Authorization": f"Bearer {self._auth_token}",
                               "Content-Type": "application/json"
                           },
                           params={
                               "query": query
                           })

        res_json = res.json()
        if len(res_json["result"]) == 0:
            return None
        return res.json()["result"]

    def mutate(self, dataset: str, mutations: Union[list, dict], return_ids: bool = False, return_documents: bool = False, visibility: str = "sync", dry_run: bool = False, auto_generate_array_keys: bool = False) -> dict:
        if isinstance(mutations, dict):
            if not "mutations" in mutations.keys():
                mutations = {"mutations": [mutations]}
        else:
            mutations = {"mutations": mutations}

        mutatetion_data = json.dumps(mutations)
        _logger.debug(
            "Sending mutation request, using dataset {}".format(dataset))
        res = requests.post(f"{self._url}/data/mutate/{dataset}",
                            headers={
                                "Authorization": f"Bearer {self._auth_token}",
                                "Content-Type": "application/json"
                            },
                            params={
                                "returnIds": "true" if return_ids else "false",
                                "returnDocuments": "true" if return_documents else "false",
                                "visibility": visibility,
                                "autoGenerateArrayKeys": "true" if auto_generate_array_keys else "false",
                                "dryRun": "true" if dry_run else "false"
                            },
                            data=mutatetion_data)

        if res.status_code != 200:
            raise SanityClientException(res.json())

        return res.json()

    def upload_image(self, dataset: str, data: BytesIO, mime_type: str) -> str:
        """Upload an image to the sanity asset api image endpoint

        Args:
            dataset (str): The dataset of the asset
            data (BytesIO): image data
            image_type (str): the image format im mime type format

        Returns:
            str: The sanity _id value
        """
        # TODO read data from file

        if not isinstance(data, bytes):
            if isinstance(data, BytesIO):
                data = data.read()

        _logger.debug(
            "Uploading image to sanity api asset endpoint, using dataset {}".format(dataset))
        res = requests.post(f"{self._url}/assets/images/{dataset}",
                            headers={
                                "Authorization": f"Bearer {self._auth_token}",
                                "Content-Type": mime_type
                            },
                            data=data).json()

        return res["document"]["_id"]
