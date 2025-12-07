"""Provincias de España con sus códigos BORME."""

from enum import Enum


class PROVINCIA(str, Enum):
    """Provincias de España."""
    ALAVA = "01"
    ALBACETE = "02"
    ALICANTE = "03"
    ALMERIA = "04"
    AVILA = "05"
    BADAJOZ = "06"
    BALEARES = "07"
    BARCELONA = "08"
    BURGOS = "09"
    CACERES = "10"
    CADIZ = "11"
    CASTELLON = "12"
    CIUDAD_REAL = "13"
    CORDOBA = "14"
    CORUNA = "15"
    CUENCA = "16"
    GIRONA = "17"
    GRANADA = "18"
    GUADALAJARA = "19"
    GUIPUZCOA = "20"
    HUELVA = "21"
    HUESCA = "22"
    JAEN = "23"
    LEON = "24"
    LLEIDA = "25"
    LA_RIOJA = "26"
    LUGO = "27"
    MADRID = "28"
    MALAGA = "29"
    MURCIA = "30"
    NAVARRA = "31"
    OURENSE = "32"
    ASTURIAS = "33"
    PALENCIA = "34"
    LAS_PALMAS = "35"
    PONTEVEDRA = "36"
    SALAMANCA = "37"
    SANTA_CRUZ_DE_TENERIFE = "38"
    CANTABRIA = "39"
    SEGOVIA = "40"
    SEVILLA = "41"
    SORIA = "42"
    TARRAGONA = "43"
    TERUEL = "44"
    TOLEDO = "45"
    VALENCIA = "46"
    VALLADOLID = "47"
    VIZCAYA = "48"
    ZAMORA = "49"
    ZARAGOZA = "50"
    CEUTA = "51"
    MELILLA = "52"

    @classmethod
    def from_name(cls, name: str) -> "PROVINCIA":
        """Obtener provincia por nombre."""
        # Normalizar nombre - quitar acentos y normalizar
        name_orig = name
        name = name.upper().strip()
        name = name.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        name = name.replace("À", "A").replace("È", "E").replace("Ì", "I").replace("Ò", "O").replace("Ù", "U")
        name = name.replace("Ñ", "N")

        # Mapa de nombres alternativos (sin acentos)
        aliases = {
            "A CORUNA": "CORUNA",
            "LA CORUNA": "CORUNA",
            "ILLES BALEARS": "BALEARES",
            "ISLAS BALEARES": "BALEARES",
            "ARABA/ALAVA": "ALAVA",
            "ARABA": "ALAVA",
            "ALAVA": "ALAVA",
            "BIZKAIA": "VIZCAYA",
            "GIPUZKOA": "GUIPUZCOA",
            "GUIPUZCOA": "GUIPUZCOA",
            "NAFARROA": "NAVARRA",
            "LLEIDA/LERIDA": "LLEIDA",
            "LERIDA": "LLEIDA",
            "GIRONA/GERONA": "GIRONA",
            "GERONA": "GIRONA",
            "TARRAGONA": "TARRAGONA",
            "ALACANT": "ALICANTE",
            "ALICANTE/ALACANT": "ALICANTE",
            "CASTELLO": "CASTELLON",
            "CASTELLON/CASTELLO": "CASTELLON",
            "CASTELLON": "CASTELLON",
            "VALENCIA/VALENCIA": "VALENCIA",
            "VALENCIA/VALENCIA": "VALENCIA",
            "VALENCIA": "VALENCIA",
            "OURENSE/ORENSE": "OURENSE",
            "ORENSE": "OURENSE",
            "SANTA CRUZ DE TENERIFE": "SANTA_CRUZ_DE_TENERIFE",
            "S.C. TENERIFE": "SANTA_CRUZ_DE_TENERIFE",
            "TENERIFE": "SANTA_CRUZ_DE_TENERIFE",
            "PALMAS, LAS": "LAS_PALMAS",
            "RIOJA, LA": "LA_RIOJA",
        }

        # Buscar en aliases primero
        if name in aliases:
            name = aliases[name]

        # Buscar por nombre del enum
        name_normalized = name.replace(" ", "_")

        for provincia in cls:
            if provincia.name == name_normalized:
                return provincia

        raise ValueError(f"InvalidProvince: {name_orig}")

    @classmethod
    def from_code(cls, code: str) -> "PROVINCIA":
        """Obtener provincia por código."""
        code = code.zfill(2)
        for provincia in cls:
            if provincia.value == code:
                return provincia
        raise ValueError(f"Código de provincia no encontrado: {code}")
