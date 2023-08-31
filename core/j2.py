import os
import re
from urllib.parse import parse_qsl, urlsplit

import bs4
from jinja2 import Environment, FileSystemLoader

re_br = re.compile(r"<br/>(\s*</)")
re_last_modified = re.compile(
    r'^\s*<meta[^>]+http-equiv="Last-Modified"[^>]+>\s*$',
    flags=re.MULTILINE
)


def millar(value):
    if value is None:
        return "----"
    if not isinstance(value, (int, float)):
        return value
    value = "{:,.0f}".format(value).replace(",", ".")
    return value


def get_query(url):
    q = urlsplit(url)
    q = parse_qsl(q.query)
    q = dict(q)
    return q


def decimal(value):
    if not isinstance(value, (int, float)):
        return value
    if int(value) == value:
        return int(value)
    return str(value).replace(".", ",")


def toTag(html: str, *args):
    if len(args) > 0:
        html = html.format(*args)
    tag = bs4.BeautifulSoup(html, 'html.parser')
    return tag


class Jnj2():

    def __init__(self, origen, destino, pre=None, post=None):
        self.j2_env = Environment(
            loader=FileSystemLoader(origen), trim_blocks=True)
        self.j2_env.filters['millar'] = millar
        self.j2_env.filters['decimal'] = decimal
        self.j2_env.filters['round'] = lambda x: round(
            x) if x is not None else None
        self.destino = destino
        self.pre = pre
        self.post = post
        self.lastArgs = None

    def save(self, template, destino=None, parse=None, **kwargs):
        self.lastArgs = kwargs
        if destino is None:
            destino = template
        out = self.j2_env.get_template(template)
        html = out.render(**kwargs)
        if self.pre:
            html = self.pre(html, **kwargs)
        if parse:
            html = parse(html, **kwargs)
        if self.post:
            html = self.post(html, **kwargs)

        destino = self.destino + destino
        directorio = os.path.dirname(destino)

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        if self.__is_changed(destino, html):
            with open(destino, "wb") as fh:
                fh.write(bytes(html, 'UTF-8'))

        return html

    def __is_changed(self, destino, new_html):
        if not os.path.isfile(destino):
            return True
        with open(destino, "r") as f:
            old_html = f.read()
        new_html = re_last_modified.sub("", new_html)
        old_html = re_last_modified.sub("", old_html)
        if old_html == new_html:
            return False
        return True

    def exists(self, destino):
        destino = self.destino + destino
        return os.path.isfile(destino)
