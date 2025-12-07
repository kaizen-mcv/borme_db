"""Funciones de regex para parsear el BORME."""

import re
from .sociedad import ALL_SOCIEDADES, SIGLAS
from .acto import ACTOS_CARGO, ACTOS_CARGO_ENTRANTE


def clean_empresa(nombre: str) -> str:
    """Limpiar y normalizar nombre de empresa."""
    nombre = nombre.rstrip(".")

    if nombre.endswith(" EN LIQUIDACION"):
        nombre = re.sub(" EN LIQUIDACION$", "", nombre)

    if nombre.endswith(" SUCURSAL EN ESPAÑA"):
        nombre = re.sub(" SUCURSAL EN ESPAÑA$", "", nombre)

    nombre = nombre.rstrip(".")

    # Normalizar siglas de tipo de sociedad
    for sigla in sorted(SIGLAS.keys()):
        regexp = " " + sigla.replace(".", r"\.") + "$"
        nombre = re.sub(regexp, " " + SIGLAS[sigla], nombre)

    return nombre


def is_company(data: str) -> bool:
    """Comprobar si es algún tipo de sociedad (vs persona física)."""
    siglas = [f" {s}" for s in ALL_SOCIEDADES]
    data = clean_empresa(data)
    alguna_sigla = any(data.endswith(s) for s in siglas)
    if not alguna_sigla:
        return "SOCIEDAD" in data
    return True


def is_acto_cargo(data: str) -> bool:
    """Comprobar si es un acto que tiene como parámetro una lista de cargos."""
    return data in ACTOS_CARGO


def is_acto_cargo_entrante(data: str) -> bool:
    """Comprobar si es un acto que aporta nuevos cargos."""
    if not is_acto_cargo(data):
        raise ValueError(f"No es un acto con cargos: {data}")
    return data in ACTOS_CARGO_ENTRANTE


def regex_empresa_tipo(data: str) -> tuple[str, str]:
    """
    Extraer nombre de empresa y tipo de sociedad.

    Args:
        data: "GRUAS BANCALERO SL"

    Returns:
        tuple: (empresa="GRUAS BANCALERO", tipo="SL")
    """
    empresa = clean_empresa(data)
    tipo = ""
    for t in ALL_SOCIEDADES:
        if empresa.endswith(f" {t}"):
            empresa = empresa[:-len(t) - 1]
            tipo = t
            empresa = empresa.rstrip(",")
    return empresa, tipo


# Regex para parsear anuncios
REGEX_EMPRESA = re.compile(r"^(\d+) - (.*?)\.?$")
REGEX_EMPRESA_REGISTRO = re.compile(r"^(\d+) - (.*)\(R\.M\. (.*)\)\.?$")

# Regex para cargos
REGEX_CARGOS = re.compile(r"([^:]+): ([^\.]+)\.?")


def parse_cargos(data: str) -> dict[str, set[str]]:
    """
    Parsear lista de cargos.

    Args:
        data: "Adm. Solid.: RAMA SANCHEZ JOSE PEDRO;RAMA SANCHEZ JAVIER JORGE."

    Returns:
        dict: {"Adm. Solid.": {"RAMA SANCHEZ JOSE PEDRO", "RAMA SANCHEZ JAVIER JORGE"}}
    """
    cargos = {}

    # Buscar patrones "Cargo: nombre1;nombre2."
    matches = REGEX_CARGOS.findall(data)
    for cargo, nombres in matches:
        cargo = cargo.strip()
        entidades = set()
        for e in nombres.split(";"):
            e = e.strip(" .")
            if e:
                e = clean_empresa(e)
                entidades.add(e)
        if cargo in cargos:
            cargos[cargo].update(entidades)
        else:
            cargos[cargo] = entidades

    return cargos
