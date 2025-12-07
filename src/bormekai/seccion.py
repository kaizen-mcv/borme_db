"""Secciones del BORME."""

from enum import Enum


class SECCION(str, Enum):
    """Secciones del BORME."""
    A = "A"  # Actos inscritos
    B = "B"  # Otros actos publicados
    C = "C"  # Sección de anuncios y avisos legales
