"""
Autocasion.com site module.

URL Base: https://www.autocasion.com
Formato de busqueda: /coches-segunda-mano/{marca}-ocasion
IMPORTANTE: El sufijo "-ocasion" es obligatorio

Desktop App:
    python -m scraping.sites.autocasion.app.main        # GUI
    python -m scraping.sites.autocasion.app.main cli    # CLI
"""

from .site import AutocasionSite
from .parser import AutocasionParser
from .app.scraper_agent import AutocasionScraperAgent
from .app.runner import AutocasionRunner

__all__ = ["AutocasionSite", "AutocasionParser", "AutocasionScraperAgent", "AutocasionRunner"]
