#!/usr/bin/env python3
from bs4 import BeautifulSoup, Tag
from core.j2 import Jnj2
from core.rss import PisosRss
from core.web import get_text
from core.piso import Piso
from core.sia import Sia
from core.alquila import Alquila
from core.mail import Mail
from datetime import datetime
from textwrap import dedent
import json
from glob import glob
import re


def clean(html, **kwargs):
    n: Tag
    soup = BeautifulSoup(html, "lxml")
    for n in soup.find_all(["th", "td", "span", "code", "li"]):
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
    for a in soup.select("body a"):
        if a.attrs.get("target"):
            continue
        href = (a.attrs.get("href") or "")
        prtc = href.split("://")[0].lower()
        if prtc in ('http', 'https'):
            a.attrs["target"] = '_blank'
    return str(soup)


def readjs(path: str, **kwargs) -> list[Piso]:
    arr = []
    with open(path, "r") as f:
        for a in json.load(f):
            a = Piso(**{**a, **kwargs})
            arr.append(a)
    return arr


def readhtml(path: str):
    with open(path, "r") as f:
        return f.read()


URL = dict(
    sia=dict(
        home="https://www.emvs.es/Alquiler/SIA",
        search=Sia.URL,
    ),
    alq=dict(
        home="https://www.comunidad.madrid/servicios/vivienda/plan-alquila",
        search=Alquila.URL,
    )
)

FAVICON = "🏠"
sia = readjs("docs/plan/sia.json", plan="sia")
alq = readjs("docs/plan/alq.json", plan="alq")

for i, p in reversed(tuple(enumerate(sia))):
    if p.reservada is True:
        del sia[i]
        continue
    p.reservada = None

pisos = sia + alq

now = datetime.now()
j = Jnj2(origen="_template", destino="docs/", post=clean)
j.save(
    "index.html",
    "index.html",
    pisos=pisos,
    now=now,
    URL=URL,
    favicon=FAVICON
)
for p in pisos:
    j.save(
        "piso.html",
        f"{p.plan}/{p.id}.html",
        p=p,
        URL=URL[p.plan],
        now=now,
        mail=Mail.askInfo(p),
        favicon=FAVICON
    )

ids = {
    'sia': set(p.id for p in sia),
    'alq': set(p.id for p in alq)
}
for file in (glob("docs/sia/*.html")+glob("docs/alq/*.html")):
    plan, id = file.split("/")[-2:]
    id = id.split(".")[0]
    if id.isdigit() and int(id) not in ids[plan]:
        html = readhtml(file)
        html = re.sub(r"\s*<header[^><]*>.*?</header>",
                      "", html, flags=re.DOTALL)
        html = html.replace(
            "<main>",
            dedent('''
                <header class="warn">
                    <p>Este piso ya no esta disponible. Mejor vuelve a consultar <a href="../">el listado</a>.</p>
                </header>
                <main>
            ''').strip()
        )
        with open(file, "w") as f:
            f.write(html)

PisosRss(
    destino="docs/",
    root="https://s-nt-s.github.io/plan-alquila-sia",
    pisos=pisos
).save("pisos.rss")
