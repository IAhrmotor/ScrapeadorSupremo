"""
Scraping module for ScrapeadorSupremo.

Architecture:
- engine/     -> HeadlessX API client (unico motor de scraping)
- sites/      -> Configuracion por sitio web
    - cochesnet/   -> coches.net
    - autocasion/  -> autocasion.com
- base/       -> Clases base abstractas

Uso:
    from scraping import MasterScraper

    with MasterScraper() as scraper:
        # Scrapear un sitio
        results = scraper.scrape("cochesnet", "audi", year=2020)

        # Scrapear todos los sitios
        all_results = scraper.scrape_all_sites("bmw")
"""

from .base.site import BaseSite, SiteRegistry, get_site_registry
from .base.parser import BaseParser, CarListing
from .engine.headlessx import HeadlessXClient, HeadlessXConfig
from .master import MasterScraper, ScrapeResult, ScrapingStats
from .sites import AVAILABLE_SITES, CochesNetSite, AutocasionSite
from .storage import SupabaseClient, get_supabase_client

__all__ = [
    # Base
    "BaseSite",
    "SiteRegistry",
    "get_site_registry",
    "BaseParser",
    "CarListing",
    # Engine
    "HeadlessXClient",
    "HeadlessXConfig",
    # Master
    "MasterScraper",
    "ScrapeResult",
    "ScrapingStats",
    # Sites
    "AVAILABLE_SITES",
    "CochesNetSite",
    "AutocasionSite",
    # Storage
    "SupabaseClient",
    "get_supabase_client",
]
