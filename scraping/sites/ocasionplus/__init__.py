"""
OcasionPlus site module.

URL Base: https://www.ocasionplus.com
Formato de búsqueda: /coches-segunda-mano?v2&orderBy=morePopular&year[from]=2007&year[to]=2025
Patrón: Scroll infinito (similar a Clicars)
"""

from .site import OcasionPlusSite, OcasionPlusConfig
from .parser import OcasionPlusParser

__all__ = ["OcasionPlusSite", "OcasionPlusConfig", "OcasionPlusParser"]
