"""Bormekai - Parser de BORME (Boletín Oficial del Registro Mercantil)."""

from .parser import parse
from .borme import Borme, BormeAnuncio, BormeActo, BormeActoCargo
from .seccion import SECCION
from .provincia import PROVINCIA

__version__ = "1.0.0"
__all__ = ["parse", "Borme", "BormeAnuncio", "BormeActo", "BormeActoCargo", "SECCION", "PROVINCIA"]
