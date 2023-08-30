import urllib3

from .piso import Piso
from .util import safe_int, tmap
from .web import Driver, get_text
from .retry import retry, RetryException
import logging

urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class BadSiaFicha(RetryException):
    pass


def get_val(n):
    txt = get_text(n)
    if txt is None:
        return None
    num = safe_int(txt)
    if num is not None:
        return num
    lw = txt.lower()
    if lw in ("si", "no"):
        return lw == "si"
    if len(txt) > 1 and txt.upper() == txt:
        return txt.title()
    return txt


class Sia:
    URL = "https://www3.emvs.es/SMAWeb/"

    def get_pisos(self):
        r: list[Piso] = []
        page = 0
        with Driver(wait=10) as w:
            w.get(Sia.URL)
            w.click("//p/input[@type='submit']")
            while True:
                page += 1
                logger.info(f"Página {page}")
                w.wait("//div//table//th")
                for tr in w.get_soup().select("tr"):
                    tds = tr.findAll("td")
                    txt = tmap(get_val, tds)
                    if len(tds) != 7:
                        continue
                    ps = self.get_piso(w, txt[0], page)
                    r.append(ps)
                nxt = w.safe_wait("//td/a[text()='%s']" % (page + 1))
                if nxt is None:
                    break
                nxt.click()
        r = sorted(r, key=lambda x: x.id)
        return r

    def get_piso(self, w: Driver, id: int, page: int) -> Piso:
        logger.info(f"Piso {id}")
        w.click(f"//td[text()='{id}']")
        w.wait(".form-group input")

        @retry(times=3, sleep=3)
        def get_soup_vals():
            soup = w.get_soup()
            vals = tmap(get_val, soup.select(".form-group input"))
            if len(vals) < 12:
                raise BadSiaFicha()
            return soup, vals

        soup, vals = get_soup_vals()

        ps = Piso(
            id=id,
            direccion=vals[1],
            precio=vals[2],
            distrito=vals[3],
            barrio=vals[4],
            dormitorios=vals[5],
            aseos=vals[6],
            planta=vals[7],
            cee=vals[8],
            orientacion=vals[9],
            adaptada=vals[10],
            ascensor=vals[11],
            reservada=soup.select_one(
                "img[src$='imagenes/RESERVADA.png']") is not None
        )
        for img in soup.select("div.rectanguloBusquedas input[src]"):
            img = get_text(img)
            img = img.rsplit("&", 1)[0]
            ps.imgs.append(img)
        w.click("//div/input[@type='submit']")
        if page > 1:
            w.click("//td/a[text()='%s']" % page)
        return ps


if __name__ == "__main__":
    s = Sia()
    ps = s.get_pisos()
    import json

    print(json.dumps(ps, indent=2))
