"""
Sites module - Configuracion especifica por sitio web.

Cada subcarpeta representa un sitio web soportado:
- cochesnet/   -> coches.net
- autocasion/  -> autocasion.com

Para agregar un nuevo sitio:
1. Crear carpeta: sites/nuevo_sitio/
2. Crear config.py con SiteConfig
3. Crear parser.py con Parser especifico
4. Registrar en AVAILABLE_SITES
"""

from .cochesnet import CochesNetSite
from .autocasion import AutocasionSite

# Registry de sitios disponibles
AVAILABLE_SITES = {
    "cochesnet": CochesNetSite,
    "autocasion": AutocasionSite,
}

__all__ = [
    "CochesNetSite",
    "AutocasionSite",
    "AVAILABLE_SITES",
]
