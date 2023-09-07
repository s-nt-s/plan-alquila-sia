import re
import time

import urllib3
from bs4 import Tag
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.remote.webelement import WebElement

from .piso import Piso
from .util import safe_int, tmap
from .web import Driver, get_text
from .retry import retry, RetryException
import logging

urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class BadAlqFicha(RetryException):
    pass


def get_val(n: Tag):
    txt = get_text(n)
    if txt is None:
        return None
    num = safe_int(txt)
    if num is not None:
        return num
    lw = txt.lower()
    if lw in ("si", "no", 'true', 'false'):
        bol = lw in ('si', 'true')
        if n.attrs.get("type") == "checkbox" and "checked" not in n.attrs:
            bol = not bol
        return bol
    if re.match(r"^\d+\d+/\d+\d+/20\d+\d+$", txt):
        # txt = date(*reversed(txt.split("/")))
        txt = "-".join(reversed(txt.split("/")))
    if len(txt) > 1 and txt.upper() == txt:
        return txt.title()
    words = txt.split()
    if len(words) > 1 and len(words[0]) > 1 and words[0].upper() == words[0]:
        words[0] = words[0].title()
        txt = " ".join(words)
    return txt


class Alquila:
    URL = "https://gestiona.comunidad.madrid/gpal_inter/secure/include/viviendapublicada/busqViviendasPublicadasContenedor.jsf"

    def __init__(self, old: dict[int, Piso] = None):
        self.old = old or {}

    def get_pisos(self):
        r: list[Piso] = []
        page = -1
        with Driver(wait=10) as w:
            w.get(Alquila.URL)
            while True:
                page += 1
                logger.info(f"Página {page+1}")
                w.click("mainPanel:pf_comboValoresDistritoPanel")
                div = w.wait("mainPanel:pf_comboValoresDistritoItems")
                dvs = div.find_elements_by_xpath("./div")
                if len(dvs) <= page:
                    break
                dpg: WebElement = dvs[page]
                dist: str = dpg.text.rsplit(None, 1)[0]
                dpg.click()
                w.click("mainPanel:filtrar")
                time.sleep(2)
                w.safe_click("mainPanel:solapaListado:header:inactive")
                time.sleep(2)
                soup = w.get_soup()
                tbody = soup.find(
                    "tbody", attrs={"id": "mainPanel:viviendasTable:table:tb"})
                for tr in tbody.select("tr"):
                    vals = tmap(get_val, tr.findAll("td"))
                    if len(vals) != 10:
                        continue
                    ps = self.get_piso(w, vals[1],
                                       direccion=vals[2],
                                       planta=vals[3],
                                       fecha=vals[-1],
                                       distrito=dist
                                       )
                    r.append(ps)
        r = sorted(r, key=lambda x: x.id)
        return r

    def get_piso(self, w: Driver, id: int, **kvargs):
        logger.info(f"Piso {id}")
        w.click(f"//td/a[text()='{id}']")
        time.sleep(2)
        cont = w.wait("mainPanel:solapaDetalle:content")

        @retry(times=3, sleep=3)
        def get_soup_vals():
            soup = w.get_soup()
            div = soup.find(
                "div", attrs={"id": "mainPanel:solapaDetalle:content"})
            vals = tmap(get_val, div.findAll("input"))
            if len(vals) < 12:
                raise BadAlqFicha()
            return soup, vals

        soup, vals = get_soup_vals()
        vals = iter(vals)

        ps = Piso(
            id=id,
            precio=next(vals),
            metros=next(vals),
            dormitorios=next(vals),
            aseos=(next(vals) or 0) + (next(vals) or 0),
            cee=next(vals),
            mascotas=next(vals),
            amueblada=next(vals),
            ascensor=next(vals),
            calefacion=next(vals),
            garaje=next(vals),
            adaptada=next(vals),
            piscina=next(vals),
            porteria=next(vals),
            trastero=next(vals),
            **kvargs
        )

        @retry(times=3, exceptions=StaleElementReferenceException, sleep=2)
        def find_element_by_css_selector(node: WebElement, css: str):
            try:
                return node.find_element_by_css_selector(css)
            except NoSuchElementException:
                return None

        img = find_element_by_css_selector(cont, "img")
        while img:
            w.execute_script("jQuery(arguments[0]).click()", img)
            time.sleep(2)
            img = None
            pop = w.wait("mainPanel:popupGaleria_container")
            src = w.get_soup().find(
                "img", attrs={"id": "mainPanel:imagenPopup"})
            src = src.attrs["src"]
            if src not in ps.imgs:
                ps.imgs.append(src)
                img = pop.find_element_by_css_selector(
                    "a[title='Ver foto siguiente']")
            if img is None:
                cls = pop.find_element_by_css_selector("img[alt='Cancelar']")
                w.execute_script("jQuery(arguments[0]).click()", cls)
                time.sleep(3)
        w.click("mainPanel:solapaListado:header:inactive")
        return ps


if __name__ == "__main__":
    a = Alquila()
    ps = a.get_pisos()
    import json

    print(json.dumps(ps, indent=2))
