"""Gestion de rutas de archivos BORME."""

import os
from datetime import date
from pathlib import Path

from .config import settings


def get_borme_xml_filepath(dt: date) -> Path:
    """Obtener ruta del archivo XML de indice para una fecha."""
    year = str(dt.year)
    month = f"{dt.month:02d}"
    day = f"{dt.day:02d}"
    filename = f"BORME-S-{year}{month}{day}.xml"
    return settings.xml_dir / year / month / filename


def get_borme_pdf_path(dt: date) -> Path:
    """Obtener directorio de PDFs para una fecha."""
    year = f"{dt.year:02d}"
    month = f"{dt.month:02d}"
    day = f"{dt.day:02d}"
    return settings.pdf_dir / year / month / day


def get_borme_json_path(dt: date) -> Path:
    """Obtener directorio de JSONs para una fecha."""
    year = f"{dt.year:02d}"
    month = f"{dt.month:02d}"
    day = f"{dt.day:02d}"
    return settings.json_dir / year / month / day


def files_exist(files: list) -> bool:
    """Verificar si todos los archivos existen."""
    return all(os.path.exists(f) for f in files)
