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

sia = readjs("docs/plan/sia.json", plan="Sia")
alq = readjs("docs/plan/alq.json", plan="Alq")

pisos = sia + alq

now = datetime.now()
j = Jnj2(origen="_template", destino="docs/", post=clean)
j.save(
    "index.html",
    "index.html",
    pisos=pisos,
    now=now,
    URL=URL
)
for p in pisos:
    plan = p.plan.lower()
    j.save(
        "piso.html",
        f"{plan}/{p.id}.html",
        p=p,
        URL=URL[plan],
        now=now,
        mail=Mail.askInfo(p)
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
        html = re.sub("\s*<header[^><]*>.*?</header>", "", html, flags=re.DOTALL)
        html = html.replace(
            "<main>",
            dedent('''
                <header class="warn">
                    <p>Este piso ya no esta disponible. Mejor vuelve a consultar <a href="../" target="_self">el listado</a>.</p>
                </header>
                <main>
            ''').strip()
        )
        with open(file, "w") as f:
            f.write(html)

PisosRss(
    destino="docs/",
    root="https://s-nt-s.github.io/plan-alquila-sia",
    pisos=[p for p in pisos if p.reservada is not True]
).save("pisos.rss")
