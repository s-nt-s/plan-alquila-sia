from dataclasses import dataclass, asdict


@dataclass
class Piso:
    id: int
    fecha: str = None
    direccion: str = None
    distrito: str = None
    planta: float = None
    orientacion: str = None
    barrio: str = None
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
        if self.imgs is None:
            self.imgs = []

    def __parse_planta(self, planta):
        if isinstance(planta, str):
            if planta.lower() in ('bj', "baja", "b", "bajo", "bjo"):
                return 0
            words = planta.split()
            if len(words) > 1 and words[0].isdigit():
                return int(words[0])
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
