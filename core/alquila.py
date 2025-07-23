import re

import urllib3
from bs4 import Tag, BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from datetime import date

from .piso import Piso
from .util import safe_int, tmap
from .web import Driver, get_text
from .retry import retry, RetryException
from typing import NamedTuple
import logging
import time

urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class BadAlqFicha(RetryException):
    pass


class Zona(NamedTuple):
    municipio: str
    distrito: str


class ComboOption(NamedTuple):
    txt: str
    dom: WebElement
    items: int
    index: int
    total: int

    @staticmethod
    def parse(options: list[WebElement], index: int):
        if len(options) <= index:
            return None
        dpg = options[index]
        txt: str = dpg.text.strip()
        txt, num = txt.strip().rsplit(None, 1)
        txt = txt.strip()
        num = int(num[1:-1])
        return ComboOption(
            txt=txt,
            dom=dpg,
            items=num,
            index=index,
            total=len(options)
        )


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


class AlqDriver(Driver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def waitLoaded(self):
        self.waitjs('!$("#img_cab_sup_izq").attr("src").endsWith("mapa_cargando.gif")')

    def iter_combo(self, input: str, items: str):
        dvs = None
        index = 0
        while True:
            if dvs is None:
                self.click(input)
                div = self.wait(items)
                # Filtrar solo elementos visibles
                all_divs = div.find_elements(By.XPATH, "./div")
                dvs = [d for d in all_divs if d.is_displayed()]
            info = ComboOption.parse(dvs, index)
            if info is None:
                break
            index += 1
            if info.index == 32:
                print("aquí")
            if info.items == 0:
                continue
            info.dom.click()
            dvs = None  # Resetear la lista para el próximo ciclo
            yield info

    def iter_combo_js(self, input: str, items: str):
        """Versión más robusta usando JavaScript para iterar el combo"""

        # JavaScript que maneja toda la lógica del combo
        js_code = f'''
        var results = [];
        var inputId = "{input}";
        var itemsId = "{items}";

        function getComboOptions() {{
            // Abrir combo usando selector de atributo en lugar de ID
            jQuery("*[id='" + inputId + "']").click();

            // Esperar a que aparezcan los items
            var items = jQuery("*[id='" + itemsId + "'] div");
            var options = [];

            items.each(function(i, elem) {{
                var text = jQuery(elem).text().trim();
                if (text) {{
                    var match = text.match(/^(.*?)\\s+\\((\\d+)\\)$/);
                    if (match) {{
                        options.push({{
                            index: i,
                            text: match[1].trim(),
                            items: parseInt(match[2]),
                            element: elem
                        }});
                    }}
                }}
            }});

            return options;
        }}

        return getComboOptions();
        '''

        # Obtener todas las opciones del combo de una vez
        options = self.execute_script(js_code)

        for opt in options:
            if opt['items'] == 0:
                continue

            # Hacer click usando JavaScript directamente en el elemento
            click_js = f'''
            jQuery("*[id='{input}']").click();
            setTimeout(function() {{
                var items = jQuery("*[id='{items}'] div");
                var targetItem = items.eq({opt['index']});
                if (targetItem.length > 0) {{
                    targetItem.click();
                }}
            }}, 100);
            '''

            self.execute_script(click_js)
            time.sleep(0.5)  # Pequeña pausa para que se procese el click

            yield ComboOption(
                txt=opt['text'],
                dom=None,  # No necesitamos el WebElement
                items=opt['items'],
                index=opt['index'],
                total=len(options)
            )

    def iter_municipios(self):
        info: ComboOption
        for info in self.iter_combo_js(
            input="mainPanel:pf_comboValoresMunicipioInput",
            items="mainPanel:pf_comboValoresMunicipioItems",
        ):
            self.waitLoaded()
            logger.info(f"Municipio {info.index+1}/{info.total}: {info.txt} ({info.items})")
            div = self.safe_wait("mainPanel:pf_comboValoresDistritoPanel", seconds=2)
            if div is not None and div.is_displayed():
                yield from self.iter_distritos()
                continue
            yield Zona(municipio=info.txt, distrito=None)

    def iter_distritos(self):
        municipio = self.execute_script(r'''
            return $("*[id='mainPanel:pf_comboValoresMunicipioInput']").val().trim().replace(/\s+\S+$/, "");
        '''.strip())
        info: ComboOption
        for info in self.iter_combo_js(
            input="mainPanel:pf_comboValoresDistritoPanel",
            items="mainPanel:pf_comboValoresDistritoItems",
        ):
            logger.info(f"Distrito {info.index+1}/{info.total}: {info.txt} ({info.items})")
            yield Zona(municipio=municipio, distrito=info.txt)

    def click_search(self):
        self.execute_script('''
            jQuery("*[id='mainPanel:filtrar']").click();
        ''')
        self.waitLoaded()

    def get_detail(self, id) -> WebElement:
        self.execute_script(f'''
            $("*[id='mainPanel:viviendasTable:table'] tr").find("td:eq(1) > a").filter((i, e)=>e.textContent.trim()=="{id}").click();
        '''.strip())
        self.waitLoaded()
        return self._driver.find_element(By.ID, "mainPanel:solapaDetalle:content")

    def jClick(self, node):
        self.execute_script("jQuery(arguments[0]).click()", node)

class Alquila:
    URL = "https://gestiona.comunidad.madrid/gpal_inter/secure/include/viviendapublicada/busqViviendasPublicadasContenedor.jsf"

    def __init__(self, old: dict[int, Piso] = None):
        self.old = old or {}
        self.today = date.today().strftime("%Y-%m-%d")

    def get_pisos(self):
        def iter_panel(soup: BeautifulSoup):
            tbody = soup.find(
                "tbody", attrs={"id": "mainPanel:viviendasTable:table:tb"})
            for tr in tbody.select("tr"):
                vals = tmap(get_val, tr.findAll("td"))
                if len(vals) == 10:
                    yield vals

        r: list[Piso] = []
        with AlqDriver(wait=10) as w:
            w.get(Alquila.URL)
            for zona in w.iter_municipios():
                w.click_search()
                for vals in iter_panel(w.get_soup()):
                    ps = self.get_piso(
                        w,
                        vals[1],
                        direccion=vals[2],
                        planta=vals[3],
                        publicado=vals[-1],
                        distrito=zona.distrito,
                        municipio=zona.municipio
                    )
                    r.append(ps)
        r = sorted(r, key=lambda x: x.id)
        return r

    def get_piso(self, w: AlqDriver, id: int, **kvargs):
        logger.info(f"Piso {id}")
        detail = w.get_detail(id)

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
        if ps.planta is None:
            ps.planta = "Casa"

        img = w.execute_script("return jQuery(arguments[0]).find('img')[0]", detail)
        while img:
            w.jClick(img)
            img = None
            w.waitLoaded()
            pop: WebElement = w.driver.find_element(By.ID, "mainPanel:popupGaleria_container")
            src = w.get_soup().find(
                "img", attrs={"id": "mainPanel:imagenPopup"})
            src = src.attrs["src"]
            if src not in ps.imgs:
                ps.imgs.append(src)
                img = pop.find_element(By.CSS_SELECTOR, "a[title='Ver foto siguiente']")
            if img is None:
                cls = pop.find_element(By.CSS_SELECTOR, "img[alt='Cancelar']")
                w.jClick(cls)
                w.waitLoaded()

        ps.modificado = self.__get_update(ps)
        return ps

    def __get_update(self, ps: Piso):
        old = self.old.get(ps.id)
        if old is None:
            return None
        if ps.askey() == old.askey():
            return old.modificado
        return self.today


if __name__ == "__main__":
    a = Alquila()
    ps = a.get_pisos()
    import json

    print(json.dumps(ps, indent=2))
