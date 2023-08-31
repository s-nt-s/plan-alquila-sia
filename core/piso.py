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

    def get_plan_id(self):
        ord = tuple(sorted('alq sia'.split()))
        pla = self.plan.lower()
        if pla not in ord:
            return self.id
        return ((ord.index(pla)+1)*10000000)+self.id

    def get_planta_title(self):
        planta = self.planta
        if planta == 0:
            planta = "Bajo"
        if isinstance(planta, int):
            planta = str(planta)+'º'
        if self.ascensor:
            planta = planta+" con "
        else:
            planta = planta+" sin "
        planta = planta + "ascensor"
        return planta
    
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
        #if tipo in ('camino', 'cmno'):
        #    return "Cam. "+dire
        return self.direccion
