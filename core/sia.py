import urllib3
from datetime import date
import logging

from .piso import Piso
from .util import safe_int, tmap
from .web import Driver, get_text, get_query
from .retry import retry, RetryException
from .imgur import ImgUr

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

    def __init__(self, old: dict[int, Piso] = None):
        self.old = old or {}
        self.today = date.today().strftime("%Y-%m-%d")

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

        old = self.old.get(id) or Piso(id=-1, imgs=[], publicado=self.today)
        ps = Piso(
            id=id,
            publicado=old.publicado or self.today,
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
        ps.imgs = self.__parse_imgs(w, ps.imgs, old.imgs)
        w.click("//div/input[@type='submit']")
        if page > 1:
            w.click("//td/a[text()='%s']" % page)

        ps.modificado = self.__get_update(ps)
        return ps

    def __get_update(self, ps: Piso):
        old = self.old.get(ps.id)
        if old is None:
            return None
        if ps.askey() == old.askey():
            return old.modificado
        return self.today

    def __parse_imgs(self, w: Driver, imgs: list[str], old: list[str]):
        if len(imgs) == 0 or ImgUr.get_client_id() is None:
            return imgs
        iup = ImgUr(
            session=w.pass_cookies()
        )

        imgur = {}
        for o in old:
            if "i.imgur.com" in o:
                imgur[o.split("?", 1)[-1]] = o

        def get_url(img: str):
            qry = get_query(img).get('idDoc')
            if qry is None:
                return img
            if qry in imgur:
                return imgur[qry]
            lnk = iup.safe_upload(img)
            if lnk is None:
                return img
            return lnk + '?' + qry

        return list(map(get_url, imgs))


if __name__ == "__main__":
    s = Sia()
    ps = s.get_pisos()
    import json

    print(json.dumps(ps, indent=2))
