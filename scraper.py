#!/usr/bin/env python3

import json
from os.path import isfile
from core.piso import Piso
from core.alquila import Alquila
from core.sia import Sia
from core.util import to_file
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)


def read(path: str, **kwargs) -> dict[int, Piso]:
    obj = {}
    if isfile(path):
        with open(path, "r") as f:
            for a in json.load(f):
                a = Piso(**{**a, **kwargs})
                obj[a.id] = a
    return obj


def dump(name: str, objs):
    key = name.split("/")[-1].upper()
    to_file(name+".json", objs)
    to_file(name+".js", **{key: objs})


PLAN = ('sia', 'alq')
PLAN = set(sys.argv[1:]).intersection(PLAN) or PLAN

if 'sia' in PLAN:
    old_sia = read("docs/plan/sia.json")
    dump("docs/plan/sia", Sia(old=old_sia).get_pisos())

if 'alq' in PLAN:
    old_alq = read("docs/plan/alq.json")
    dump("docs/plan/alq", Alquila(old=old_alq).get_pisos())
