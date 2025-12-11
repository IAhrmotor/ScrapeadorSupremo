"""
Coches.net site module.

URL Base: https://www.coches.net
Formato de busqueda: /segunda-mano/{marca}/{año}?pg={pagina}
"""

from .site import CochesNetSite
from .parser import CochesNetParser

__all__ = ["CochesNetSite", "CochesNetParser"]
