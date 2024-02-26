import requests
import os
import logging
from base64 import standard_b64encode
from functools import cache
from requests.exceptions import JSONDecodeError


logger = logging.getLogger(__name__)


class ImgUrlException(Exception):
    pass


def get(obj, *args):
    if not obj or not args:
        return None
    for a in args:
        if not isinstance(obj, dict):
            return obj
        obj = obj.get(a)
        if obj is None:
            return None
    return obj


class ImgUr:
    UPLOAD = "https://api.imgur.com/3/image"

    @staticmethod
    @cache
    def get_client_id():
        client_id = os.environ.get("IMGUR_CLIENT")
        if isinstance(client_id, str):
            client_id = client_id.strip()
        if client_id in (None, ""):
            logger.warn("env IMGUR_CLIENT empty")
            return None
        return client_id

    def __init__(self, session=None, client_id=None):
        self.session = session or requests.Session()
        self.client_id = client_id
        if self.client_id is None:
            self.client_id = ImgUr.get_client_id()
        self.session.headers.update({
            'Authorization': f'Client-ID {self.client_id}',
            'Accept': 'application/json'
        })

    def upload(self, url):
        if self.client_id is None:
            raise ImgUrlException(
                "Client-ID mandatory (set env var IMGUR_CLIENT)"
            )

        rimg = self.session.get(url, verify=False)
        b64_image = standard_b64encode(rimg.content)

        r = self.session.post(
            ImgUr.UPLOAD,
            data=dict(
                image=b64_image
            ),
            files=[]
        )

        if not r.text:
            raise ImgUrlException("Not json response")

        try:
            js = r.json()
        except JSONDecodeError:
            raise ImgUrlException("Not json response: "+r.text)

        error = get(js, 'data', 'error', 'message')
        if error:
            raise ImgUrlException(error)

        link = get(js, 'data', 'link')

        if link is None:
            raise ImgUrlException("Not link found: "+r.text)

        return link

    def safe_upload(self, url):
        try:
            lnk = self.upload(url)
            logger.info(f"{url} -> {lnk}")
            return lnk
        except ImgUrlException as e:
            logger.info(f"{url} -> {str(e)}")
            return None
