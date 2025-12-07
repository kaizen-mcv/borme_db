"""Cargos societarios."""

# Mapa de abreviaturas a nombres completos de cargos
CARGOS = {
    "Presidente": "Presidente",
    "PRESIDENTE": "Presidente",
    "Pdte.": "Presidente",
    "Vicepresid.": "Vicepresidente",
    "VICEPRESIDEN": "Vicepresidente",
    "Vicepresi.1º": "Vicepresidente primero",
    "Vicepr.2": "Vicepresidente segundo",
    "Consejero": "Consejero",
    "Cons.": "Consejero",
    "CONSEJERO": "Consejero",
    "Secretario": "Secretario",
    "SECRETARIO": "Secretario",
    "Vicesecret.": "Vicesecretario",
    "Adm. Unico": "Administrador único",
    "ADM.UNICO": "Administrador único",
    "Admin.Unico": "Administrador único",
    "Adm. Solid.": "Administrador solidario",
    "ADM.SOLIDAR.": "Administrador solidario",
    "Admin.Solid": "Administrador solidario",
    "Adm. Mancom": "Administrador mancomunado",
    "Admin.Manc": "Administrador mancomunado",
    "ADM.CONJUNTO": "Administrador conjunto",
    "Apoderado": "Apoderado",
    "APODERADO": "Apoderado",
    "Apo.Manc.": "Apoderado mancomunado",
    "Apo.Sol.": "Apoderado solidario",
    "Representan": "Representante",
    "Represent.": "Representante",
    "Con.Delegado": "Consejero delegado",
    "Cons.Delegad": "Consejero delegado",
    "Liquidador": "Liquidador",
    "LIQUIDADOR": "Liquidador",
    "LiquiSoli": "Liquidador solidario",
    "Auditor": "Auditor",
    "Aud.Supl.": "Auditor suplente",
    "Gerente": "Gerente",
    "GERENTE": "Gerente",
    "Dir. General": "Director general",
    "Dir.Gral.": "Director general",
    "DTOR.GENERAL": "Director general",
    "Socio único": "Socio único",
    "Socio": "Socio",
    "Tesorero": "Tesorero",
    "Vocal": "Vocal",
    "VOCAL": "Vocal",
    # ... muchos más cargos
}

# Lista de todas las abreviaturas de cargos
CARGO_KEYWORDS = list(CARGOS.keys())


def normalize_cargo(cargo: str) -> str:
    """Normalizar nombre de cargo."""
    return CARGOS.get(cargo, cargo)
