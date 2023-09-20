from dataclasses import dataclass, asdict
import re

re_sp = re.compile(r"\s+")


@dataclass
class Piso:
    id: int
    publicado: str = None
    modificado: str = None
    direccion: str = None
    municipio: str = None
    distrito: str = None
    barrio: str = None
    planta: float = None
    orientacion: str = None
    precio: float = None
    metros: float = None
    dormitorios: int = None
    aseos: int = None
    cee: str = None
    mascotas: bool = None
    amueblada: bool = None
    ascensor: bool = None
    calefacion: bool = None
    garaje: bool = None
    adaptada: bool = None
    piscina: bool = None
    porteria: bool = None
    trastero: bool = None
    reservada: bool = None
    imgs: list[str] = None
    plan: str = None
    u_plan: str = None

    def __post_init__(self):
        self.planta = self.__parse_planta(self.planta)
        self.cee = self.__parse_cee(self.cee)
        self.distrito = self.__parse_distrito(self.distrito)
        if self.imgs is None:
            self.imgs = []

    def __parse_distrito(self, distrito):
        if distrito == "Moncloa":
            return "Moncloa-Aravaca"
        if distrito == "Puente De Vallecas":
            return "Puente de Vallecas"
        return distrito

    def __parse_planta(self, planta):
        if isinstance(planta, str):
            if planta.lower() in ('bj', "baja", "b", "bajo", "bjo"):
                return 0
            words = planta.split()
            if len(words) > 1 and words[0].isdigit():
                return int(words[0])
            m = re.search(r"^(\d+)\D+", planta)
            if m:
                return int(m.group(1))
        return planta

    def __parse_cee(self, cee):
        if cee in ('Pdte.', 'Pendiente'):
            return None
        return cee

    def asdict(self):
        o = asdict(self)
        for k, v in list(o.items()):
            if v is None:
                del o[k]
        return o

    def items(self):
        return self.asdict().items()

    def get_plan_id(self):
        ord = tuple(sorted('alq sia'.split()))
        if self.plan not in ord:
            return self.id
        return ((ord.index(self.plan)+1)*10000000)+self.id

    def get_planta_title(self):
        ascensor = "ascensor"
        if self.ascensor:
            ascensor = "con "+ascensor
        else:
            ascensor = "sin "+ascensor
        if self.planta is None:
            return ascensor
        planta = self.planta
        if planta == 0:
            planta = "Bajo"
        if isinstance(planta, int):
            planta = str(planta)+'º'
        planta = planta + " "+ascensor
        return planta

    def get_dormitorio_title(self):
        if len(self.imgs) == 0 and not isinstance(self.dormitorios, int):
            return ""
        dormitorios = str(self.dormitorios)+" dormitorios"
        if self.dormitorios == 1:
            dormitorios = dormitorios[:-1]
        if len(self.imgs) == 0:
            return dormitorios
        fotos = str(len(self.imgs))+" fotos"
        if len(self.imgs) == 1:
            fotos = fotos[:-1]
        return dormitorios+f" ({fotos})"

    def get_direccion(self):
        spl = self.direccion.split(None, 1)
        if len(spl) != 2:
            return self.direccion
        dire = spl[1]
        tipo = spl[0].lower()
        if tipo == "calle":
            return "C/ "+dire
        if tipo in ("avenida", 'avda'):
            return "Av. "+dire
        if tipo == "paseo":
            return "Pº "+dire
        if tipo in ('travesía', 'trva'):
            return "Trª "+dire
        if tipo == "plaza":
            return "Pl. "+dire
        if tipo == 'ronda':
            return "Rda. "+dire
        # if tipo in ('camino', 'cmno'):
        #    return "Cam. "+dire
        return self.direccion

    def askey(self):
        obj = asdict(self)
        for k in ('modificado', 'municipio', 'distrito', 'barrio'):
            if k in obj:
                del obj[k]
        for k, v in list(obj.items()):
            if isinstance(v, list):
                obj[k] = tuple(v)
        obj = sorted(obj.items())
        return tuple(obj)

    @property
    def fecha(self):
        return self.modificado or self.publicado

    @property
    def zona(self):
        return self.distrito or self.municipio

    @property
    def mapa(self):
        def clean(s: str):
            s = re_sp.sub(" ", s).strip()
            s = s.replace('"', "")
            s = s.replace(' ', "+")
            return s

        arr = [
            self.direccion,
            self.zona,
            "Madrid"
        ]
        arr = map(clean, arr)
        url = "https://www.google.com/maps/place/" + ",+".join(arr)
        return url
