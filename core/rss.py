import rfeed
from datetime import datetime
from textwrap import dedent
from xml.dom.minidom import parseString as parseXml
import re
import os


from .piso import Piso

re_last_modified = re.compile(
    r'^\s*<lastBuildDate>[^>]+</lastBuildDate>\s*$',
    flags=re.MULTILINE
)


class PisosRss:
    def __init__(self, destino, root: str, pisos: list[Piso]):
        self.root = root
        self.pisos = pisos
        self.destino = destino

    def save(self, out: str):
        feed = rfeed.Feed(
            title="Pla Alquila Sia",
            link=self.root+'/'+out,
            description="Lista de pisos del Plan Alquila y el Plan Sia",
            language="es-ES",
            lastBuildDate=datetime.now(),
            items=list(self.iter_items())
        )

        destino = self.destino + out
        directorio = os.path.dirname(destino)

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        rss = self.__get_rss(feed)
        if self.__is_changed(destino, rss):
            with open(destino, "w") as f:
                f.write(rss)

    def __is_changed(self, destino, new_rss):
        if not os.path.isfile(destino):
            return True
        with open(destino, "r") as f:
            old_rss = f.read()
        new_rss = re_last_modified.sub("", new_rss)
        old_rss = re_last_modified.sub("", old_rss)
        if old_rss == new_rss:
            return False
        return True
    
    def __get_rss(self, feed: rfeed.Feed):
        def bkline(s, i):
            return s.split("\n", 1)[i]
        rss = feed.rss()
        dom = parseXml(rss)
        prt = dom.toprettyxml()
        rss = bkline(rss, 0)+'\n'+bkline(prt, 1)
        return rss

    def iter_items(self):
        for p in self.pisos:
            link = f'{self.root}/{p.plan.lower()}/{p.id}'
            metros = round(p.metros) if p.metros else None
            yield rfeed.Item(
                title=f'{p.precio}€ {p.distrito}',
                link=link,
                description=dedent(f'''
                    {p.get_direccion()},
                    {p.get_planta_title()},
                    {metros}m², {p.dormitorios} hab, {p.aseos} aseos,
                    {len(p.imgs)} fotos
                ''').strip().replace("Nonem², ", "").replace("\n", "<br/>"),
                guid=rfeed.Guid(link+'?'+p.fecha),
                pubDate=datetime(*map(int, p.fecha.split("-"))),
            )
