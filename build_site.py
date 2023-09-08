#!/usr/bin/env python3
from bs4 import BeautifulSoup, Tag
from core.j2 import Jnj2
from core.rss import PisosRss
from core.web import get_text
from core.piso import Piso
from core.sia import Sia
from core.alquila import Alquila
from datetime import datetime
import json


def clean(html, **kwargs):
    n: Tag
    soup = BeautifulSoup(html, "lxml")
    for n in soup.findAll(["th", "td", "span", "code", "li"]):
        txt = get_text(n)
        if n.name == "li" and "None" in txt:
            n.extract()
            continue
        if len(n.select(":scope *")) > 0:
            continue
        if txt not in (None, "None"):
            continue
        if n.name in ("span", "code"):
            n.extract()
        else:
            n.string = ""
    return str(soup)


def read(path: str, **kwargs) -> list[Piso]:
    arr = []
    with open(path, "r") as f:
        for a in json.load(f):
            a = Piso(**{**a, **kwargs})
            arr.append(a)
    return arr


sia = read("docs/plan/sia.json", plan="Sia", u_plan=Sia.URL)
alq = read("docs/plan/alq.json", plan="Alq", u_plan=Alquila.URL)

pisos = sia + alq

now = datetime.now()
j = Jnj2(origen="_template", destino="docs/", post=clean)
j.save("index.html", "index.html", pisos=pisos, now=now)
for p in pisos:
    j.save("piso.html", f"{p.plan.lower()}/{p.id}.html", p=p, now=now)

PisosRss(
    destino="docs/", 
    root="https://s-nt-s.github.io/plan-alquila-sia",
    pisos=pisos
).save("pisos.rss")