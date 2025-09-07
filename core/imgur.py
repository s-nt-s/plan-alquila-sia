import requests
import os
import logging
from base64 import standard_b64encode
from functools import cache
from requests.exceptions import JSONDecodeError
import bs4
from typing import Union
import re

logger = logging.getLogger(__name__)


class ImgUrlException(Exception):
    pass


def get_text(n: Union[bs4.Tag, None]):
    if n is None:
        return None
    txt = n.get_text()
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) == 0:
        return None
    return txt


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
            logger.warning("env IMGUR_CLIENT empty")
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

        try:
            r = self.session.post(
                ImgUr.UPLOAD,
                data=dict(
                    image=b64_image
                ),
                files=[]
            )
        except requests.exceptions.SSLError:
            raise ImgUrlException(ImgUr.UPLOAD+" no disponible (ssl error)")
        except requests.exceptions.ChunkedEncodingError as e:
            raise ImgUrlException(ImgUr.UPLOAD+" "+str(e))

        if not r.text:
            raise ImgUrlException("Not json response")

        try:
            js = r.json()
        except JSONDecodeError:
            self.__raise_error_from_text(r.text)

        error = get(js, 'data', 'error', 'message')
        if error:
            raise ImgUrlException(error)

        link = get(js, 'data', 'link')

        if link is None:
            raise ImgUrlException("Not link found: "+r.text)

        return link

    def __raise_error_from_text(self, text: str):
        if "</html>" in text and "</title>" in text:
            soup = bs4.BeautifulSoup(text, "html.parser")
            title = get_text(soup.select_one("title"))
            if title is not None:
                raise ImgUrlException("html response instead json: "+title)
        raise ImgUrlException("Not json response: "+text)

    def safe_upload(self, url):
        try:
            lnk = self.upload(url)
            logger.info(f"{url} -> {lnk}")
            return lnk
        except ImgUrlException as e:
            logger.info(f"{url} -> {str(e)}")
            return None
