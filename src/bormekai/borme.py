"""Modelos de datos del BORME."""

import datetime
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .acto import ACTO, ACTOS_CARGO
from .provincia import PROVINCIA

logger = logging.getLogger(__name__)

FILE_VERSION = "2001"


class BormeActo:
    """Representa un Acto del Registro Mercantil."""

    def __init__(self, name: str, value):
        if name not in ACTO.ALL_KEYWORDS:
            logger.warning(f"Invalid acto found: {name}")
        self.name = name
        self.value = value

    def __lt__(self, other):
        return self.name < other.name

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name}): {self.value}>"


class BormeActoTexto(BormeActo):
    """Acto con valor de texto."""

    def __init__(self, name: str, value: str | None):
        if name in ACTOS_CARGO:
            raise ValueError(f"No se puede crear BormeActoTexto con acto de cargo: {name}")
        super().__init__(name, value)


class BormeActoCargo(BormeActo):
    """Acto con lista de cargos."""

    def __init__(self, name: str, value: dict[str, set]):
        if name not in ACTOS_CARGO:
            raise ValueError(f"No se puede crear BormeActoCargo sin acto de cargo: {name}")

        # Convertir listas a sets
        for k, v in value.items():
            if isinstance(v, list):
                value[k] = set(v)

        super().__init__(name, value)

    @property
    def cargos(self) -> dict[str, set]:
        return self.value

    def get_nombres_cargos(self) -> list[str]:
        return list(self.value.keys())


@dataclass
class BormeAnuncio:
    """Representa un anuncio con un conjunto de actos mercantiles."""

    id: int
    empresa: str
    registro: str = ""
    sucursal: bool = False
    liquidacion: bool = False
    datos_registrales: str = ""
    actos: list[BormeActo] = field(default_factory=list)

    def __post_init__(self):
        logger.debug(f"new BormeAnuncio({self.id}) {self.empresa}")

    @classmethod
    def from_dict(cls, id: int, empresa: str, actos_list: list, extra: dict, datos_registrales: str = "") -> "BormeAnuncio":
        """Crear anuncio desde diccionario."""
        anuncio = cls(
            id=id,
            empresa=empresa,
            registro=extra.get("registro", ""),
            sucursal=extra.get("sucursal", False),
            liquidacion=extra.get("liquidacion", False),
            datos_registrales=datos_registrales,
        )

        for acto in actos_list:
            for acto_nombre, valor in acto.items():
                if acto_nombre == "Datos registrales":
                    anuncio.datos_registrales = valor
                    continue

                if acto_nombre in ACTOS_CARGO:
                    a = BormeActoCargo(acto_nombre, valor)
                else:
                    a = BormeActoTexto(acto_nombre, valor)
                anuncio.actos.append(a)

        return anuncio

    def get_borme_actos(self) -> list[BormeActo]:
        return self.actos

    def get_actos(self):
        for acto in self.actos:
            yield acto.name, acto.value

    def __repr__(self):
        return f"<BormeAnuncio({self.id}) {self.empresa} (r:{self.registro}, s:{self.sucursal}, l:{self.liquidacion}) ({len(self.actos)})>"


@dataclass
class Borme:
    """Representa un BORME parseado."""

    date: datetime.date
    seccion: str
    provincia: PROVINCIA
    num: int
    cve: str
    anuncios: dict[int, BormeAnuncio] = field(default_factory=dict)
    filename: str | None = None
    _url: str | None = None

    def __post_init__(self):
        if isinstance(self.date, tuple):
            self.date = datetime.date(year=self.date[0], month=self.date[1], day=self.date[2])
        self.anuncios_rango = (
            min(self.anuncios.keys()) if self.anuncios else 0,
            max(self.anuncios.keys()) if self.anuncios else 0,
        )

    @property
    def url(self) -> str:
        if not self._url:
            dt = self.date
            self._url = f"https://www.boe.es/borme/dias/{dt.year}/{dt.month:02d}/{dt.day:02d}/pdfs/{self.cve}.pdf"
        return self._url

    def get_anuncio(self, anuncio_id: int) -> BormeAnuncio:
        try:
            return self.anuncios[anuncio_id]
        except KeyError:
            raise ValueError(f"Anuncio {anuncio_id} not found in BORME {self}")

    def get_anuncios_ids(self) -> list[int]:
        return sorted(self.anuncios.keys())

    def get_anuncios(self) -> list[BormeAnuncio]:
        return list(self.anuncios.values())

    def _to_dict(self, include_url: bool = True) -> dict:
        doc = {
            "cve": self.cve,
            "date": self.date.isoformat(),
            "seccion": self.seccion,
            "provincia": self.provincia.name if isinstance(self.provincia, PROVINCIA) else str(self.provincia),
            "num": self.num,
            "from_anuncio": self.anuncios_rango[0],
            "to_anuncio": self.anuncios_rango[1],
            "anuncios": {},
            "num_anuncios": len(self.anuncios),
            "version": FILE_VERSION,
        }

        for id, anuncio in self.anuncios.items():
            doc["anuncios"][str(anuncio.id)] = {
                "empresa": anuncio.empresa,
                "registro": anuncio.registro,
                "sucursal": anuncio.sucursal,
                "liquidacion": anuncio.liquidacion,
                "datos registrales": anuncio.datos_registrales,
                "actos": [],
                "num_actos": len(anuncio.actos),
            }
            for acto in anuncio.actos:
                acto_dict = {acto.name: acto.value}
                doc["anuncios"][str(anuncio.id)]["actos"].append(acto_dict)

        if include_url:
            doc["url"] = self.url

        return doc

    def to_json(self, path: str | None = None, overwrite: bool = True, pretty: bool = True, include_url: bool = True) -> str | bool:
        """Guardar BORME como JSON."""

        def set_default(obj):
            if isinstance(obj, set):
                return sorted(obj)
            elif isinstance(obj, PROVINCIA):
                return obj.name
            raise TypeError(type(obj))

        if path is None:
            path = Path(self.filename).with_suffix(".json").name if self.filename else f"{self.cve}.json"

        path = Path(path)
        if path.is_file() and not overwrite:
            return False
        if path.is_dir():
            path = path / f"{self.cve}.json"

        doc = self._to_dict(include_url)
        indent = 2 if pretty else None

        with open(path, "w") as fp:
            json.dump(doc, fp, default=set_default, indent=indent, sort_keys=True)

        return str(path)

    @classmethod
    def from_json(cls, filename: str) -> "Borme":
        """Crear Borme desde archivo JSON."""
        with open(filename) as fp:
            d = json.load(fp)

        cve = d["cve"]
        date = datetime.datetime.strptime(d["date"], "%Y-%m-%d").date()
        seccion = d["seccion"]
        provincia_str = d["provincia"].upper()
        try:
            provincia = PROVINCIA.from_name(provincia_str)
        except ValueError:
            provincia = provincia_str  # Mantener como string si no se reconoce
        num = d["num"]
        url = d.get("url")

        anuncios = {}
        for id_anuncio, data in sorted(d["anuncios"].items(), key=lambda t: int(t[0])):
            extra = {
                "liquidacion": data.get("liquidacion", False),
                "sucursal": data.get("sucursal", False),
                "registro": data.get("registro", ""),
            }
            anuncio = BormeAnuncio.from_dict(
                int(id_anuncio),
                data["empresa"],
                data.get("actos", []),
                extra,
                data.get("datos registrales", ""),
            )
            anuncios[anuncio.id] = anuncio

        borme = cls(
            date=date,
            seccion=seccion,
            provincia=provincia,
            num=num,
            cve=cve,
            anuncios=anuncios,
            filename=filename,
        )
        borme._url = url
        return borme

    def __lt__(self, other):
        return self.anuncios_rango[1] < other.anuncios_rango[0]

    def __repr__(self):
        return f"<Borme({self.cve}) {self.date} {self.provincia}>"
