"""Parser de PDFs del BORME."""

import datetime
import logging
import re
from pathlib import Path

from .borme import Borme, BormeAnuncio, BormeActo, BormeActoTexto, BormeActoCargo
from .provincia import PROVINCIA
from .seccion import SECCION
from .acto import ACTOS_CARGO

logger = logging.getLogger(__name__)

# Intentar importar bormeparser para parsear PDFs
# Si no está disponible, solo funcionará from_json
try:
    import bormeparser
    from bormeparser.backends.pypdf2.parser import PyPDF2Parser
    import bormeparser.provincia as bp_provincia
    HAS_BORMEPARSER = True

    # Parchear bormeparser.provincia.PROVINCIA.from_title para soportar nombres bilingües
    _original_from_title = bp_provincia.PROVINCIA.from_title

    @classmethod
    def _patched_from_title(cls, title):
        """Versión parcheada que soporta nombres bilingües de provincias."""
        # Normalizar nombre (quitar tildes y pasar a mayúsculas)
        title_upper = title.upper().strip()
        title_normalized = title_upper.replace("Á", "A").replace("É", "E")
        title_normalized = title_normalized.replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
        title_normalized = title_normalized.replace("À", "A").replace("È", "E")
        title_normalized = title_normalized.replace("Ì", "I").replace("Ò", "O").replace("Ù", "U")
        title_normalized = title_normalized.replace("Ñ", "N")

        # Mapa de nombres bilingües/con espacios a nombres estándar de bormeparser
        # Las claves están SIN tildes (normalizadas)
        bilingual_map = {
            # Comunidad Valenciana
            "ALICANTE/ALACANT": "ALICANTE",
            "CASTELLON/CASTELLO": "CASTELLON",
            "VALENCIA/VALENCIA": "VALENCIA",
            # Cataluña
            "GIRONA/GERONA": "GIRONA",
            "LLEIDA/LERIDA": "LLEIDA",
            # Galicia (A_CORUÑA tiene tilde en bormeparser)
            "A CORUNA": "A_CORUÑA",
            "LA CORUNA": "A_CORUÑA",
            # Baleares
            "ILLES BALEARS": "ILLES_BALEARS",
            # País Vasco
            "ARABA/ALAVA": "ARABA",
            "BIZKAIA": "BIZKAIA",
            "GIPUZKOA": "GIPUZKOA",
            # Otras con espacios
            "CIUDAD REAL": "CIUDAD_REAL",
            "LA RIOJA": "LA_RIOJA",
            "LAS PALMAS": "LAS_PALMAS",
            "SANTA CRUZ DE TENERIFE": "SANTA_CRUZ_DE_TENERIFE",
        }

        # Buscar usando el nombre normalizado (sin tildes)
        if title_normalized in bilingual_map:
            title = bilingual_map[title_normalized]
        else:
            title = title_upper

        try:
            return getattr(cls, title)
        except AttributeError:
            # Intentar con el nombre normalizado (reemplazando espacios por _)
            try:
                return getattr(cls, title_normalized.replace(" ", "_"))
            except AttributeError:
                raise ValueError(f'InvalidProvince: {title}')

    bp_provincia.PROVINCIA.from_title = _patched_from_title

except ImportError:
    HAS_BORMEPARSER = False
    logger.warning("bormeparser no disponible, solo se podrán cargar archivos JSON")


def parse(filename: str, seccion: SECCION = SECCION.A) -> Borme:
    """
    Parsear un archivo PDF del BORME.

    Args:
        filename: Ruta al archivo PDF
        seccion: Sección del BORME (A, B, C)

    Returns:
        Borme: Objeto Borme con los datos parseados
    """
    if not HAS_BORMEPARSER:
        raise ImportError("bormeparser es necesario para parsear PDFs. Instálalo con: pip install bormeparser")

    # Usar bormeparser para parsear el PDF
    borme_bp = bormeparser.parse(filename, bormeparser.SECCION.A if seccion == SECCION.A else seccion)

    # Convertir a nuestro modelo
    return _convert_from_bormeparser(borme_bp, filename)


def _convert_from_bormeparser(borme_bp, filename: str) -> Borme:
    """Convertir un Borme de bormeparser a nuestro modelo."""

    # Convertir provincia
    try:
        provincia = PROVINCIA.from_name(borme_bp.provincia.name)
    except (ValueError, AttributeError):
        provincia = str(borme_bp.provincia)

    # Convertir anuncios
    anuncios = {}
    for anuncio_bp in borme_bp.get_anuncios():
        actos = []
        for acto_bp in anuncio_bp.get_borme_actos():
            if acto_bp.name in ACTOS_CARGO:
                # Convertir sets a listas para el constructor
                value = {k: set(v) if isinstance(v, (list, set)) else v for k, v in acto_bp.value.items()}
                acto = BormeActoCargo(acto_bp.name, value)
            else:
                acto = BormeActoTexto(acto_bp.name, acto_bp.value)
            actos.append(acto)

        anuncio = BormeAnuncio(
            id=anuncio_bp.id,
            empresa=anuncio_bp.empresa,
            registro=anuncio_bp.registro or "",
            sucursal=anuncio_bp.sucursal,
            liquidacion=anuncio_bp.liquidacion,
            datos_registrales=anuncio_bp.datos_registrales or "",
            actos=actos,
        )
        anuncios[anuncio.id] = anuncio

    borme = Borme(
        date=borme_bp.date,
        seccion=borme_bp.seccion,
        provincia=provincia,
        num=borme_bp.num,
        cve=borme_bp.cve,
        anuncios=anuncios,
        filename=filename,
    )

    return borme
