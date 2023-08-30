#!/usr/bin/env python3

from core.alquila import Alquila
from core.sia import Sia
from core.util import to_file
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)


def dump(name: str, objs):
    key = name.split("/")[-1].upper()
    to_file(name+".json", objs)
    to_file(name+".js", **{key: objs})


dump("docs/plan/sia", Sia().get_pisos())

dump("docs/plan/alq", Alquila().get_pisos())
