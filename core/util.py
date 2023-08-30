
from datetime import date, datetime
import dataclasses
from os import makedirs
from os.path import dirname
import json


def myconverter(o):
    if isinstance(o, (datetime, date)):
        return o.__str__()
    if dataclasses.is_dataclass(o):
        o = dataclasses.asdict(o)
        for k, v in list(o.items()):
            if v is None:
                del o[k]
        return o


def tmap(fnc, arr):
    return tuple(map(fnc, arr))


def tfilter(fnc, arr):
    return tuple(filter(fnc, arr))


def tsplit(s: str):
    return tuple(s.split())


def safe_int(txt: str):
    if txt is None:
        return None
    num = txt.strip()
    if len(num) == 0:
        return None
    if num[-1] in ("º", "ª", "€"):
        num = num[:-1].strip()
    if num.isdigit():
        return int(num)
    num = num.replace(".", "")
    num = num.replace(",", ".")
    try:
        num = float(num)
        if num == int(num):
            return int(num)
        return num
    except ValueError:
        pass
    return None


def to_file(path, *args, **kwargs):
    if len(kwargs) == 0 and len(args) == 0:
        return
    if len(args) > 0 and len(kwargs) > 0:
        raise ValueError("No se puede usar args y kwargs a la vez")
    if len(args) == 1:
        args = args[0]
    dr = dirname(path)
    makedirs(dr, exist_ok=True)
    with open(path, "w") as f:
        if args:
            json.dump(args, f, indent=2, default=myconverter)
        for i, (k, v) in enumerate(kwargs.items()):
            if i > 0:
                f.write(";\n")
            f.write("const " + k + " = ")
            json.dump(v, f, indent=2, default=myconverter)
            f.write(";")
