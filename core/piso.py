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
        if self.cee in ('Pdte.', 'Pendiente'):
            self.cee = None
        if isinstance(self.planta, str) and self.planta.lower() in ('bj', "baja", "b", "bajo", "bjo"):
            self.planta = 0
        if self.imgs is None:
            self.imgs = []

    def asdict(self):
        o = asdict(self)
        for k, v in list(o.items()):
            if v is None:
                del o[k]
        return o

    def items(self):
        return self.asdict().items()
