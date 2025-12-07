"""Sistema de logging centralizado para BORME."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import settings


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
) -> Path:
    """
    Configura el sistema de logging para todo el proyecto.

    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Nombre del archivo de log (None = auto-generar)
        console: Si True, también muestra logs en consola

    Returns:
        Path al archivo de log creado
    """
    # Crear directorio de logs si no existe
    log_dir = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # Nombre de archivo auto-generado si no se especifica
    if log_file is None:
        log_file = f"borme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    log_path = log_dir / log_file

    # Formato de logs
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para archivo
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    handlers = [file_handler]

    # Handler para consola
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # Configurar root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True,  # Sobrescribir configuración previa
    )

    # Silenciar logs verbosos de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("bormeparser").setLevel(logging.WARNING)

    return log_path


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.

    Args:
        name: Nombre del logger (normalmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Logger por defecto del proyecto
logger = get_logger("borme")
