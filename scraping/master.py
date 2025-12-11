"""
Master Scraper - Orquestador principal de scraping multi-sitio.

Centraliza todas las operaciones de scraping usando HeadlessX como
unico motor y delegando a cada Site su configuracion especifica.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .base.site import BaseSite, SiteRegistry, get_site_registry
from .base.parser import CarListing
from .engine.headlessx import HeadlessXClient, HeadlessXConfig
from .sites import AVAILABLE_SITES

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    """Resultado de una operacion de scraping."""

    site: str
    marca: str
    year: Optional[int]
    page: int
    listings: List[CarListing]
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    @property
    def count(self) -> int:
        return len(self.listings)


@dataclass
class ScrapingStats:
    """Estadisticas de scraping."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_listings: int = 0
    by_site: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class MasterScraper:
    """
    Scraper maestro que orquesta el scraping de multiples sitios.

    Usa HeadlessX como unico motor de scraping.
    Cada sitio define su propia configuracion de URLs y parsing.

    Ejemplo:
        scraper = MasterScraper()
        scraper.setup()

        # Scrapear una marca en un sitio
        results = scraper.scrape("cochesnet", "audi", year=2020)

        # Scrapear en todos los sitios
        results = scraper.scrape_all_sites("bmw")

        scraper.cleanup()
    """

    def __init__(self, headlessx_config: Optional[HeadlessXConfig] = None):
        """
        Inicializa el Master Scraper.

        Args:
            headlessx_config: Configuracion para HeadlessX (usa defaults si no se proporciona)
        """
        self.client = HeadlessXClient(headlessx_config)
        self.registry = get_site_registry()
        self.stats = ScrapingStats()
        self._is_setup = False

        # Register available sites
        self._register_sites()

    def _register_sites(self) -> None:
        """Registra todos los sitios disponibles."""
        for name, site_class in AVAILABLE_SITES.items():
            site = site_class()
            self.registry.register(site)
            self.stats.by_site[name] = 0

    def setup(self) -> None:
        """Configura el scraper y conecta con HeadlessX."""
        logger.info("Setting up MasterScraper...")
        self.client.setup()
        self._is_setup = True
        logger.info(f"MasterScraper ready. Sites: {self.registry.list_sites()}")

    def cleanup(self) -> None:
        """Limpia recursos."""
        self.client.cleanup()
        self._is_setup = False
        logger.info("MasterScraper cleaned up")

    def scrape(
        self,
        site_name: str,
        marca: str,
        year: Optional[int] = None,
        max_pages: Optional[int] = None
    ) -> List[ScrapeResult]:
        """
        Scrapea listados de coches de un sitio.

        Args:
            site_name: Nombre del sitio ("cochesnet", "autocasion")
            marca: Marca a buscar
            year: Año opcional (no todos los sitios lo soportan)
            max_pages: Maximo de paginas a scrapear (None = usar default del sitio)

        Returns:
            Lista de ScrapeResult con los resultados por pagina
        """
        if not self._is_setup:
            self.setup()

        site = self.registry.get(site_name)
        if not site:
            raise ValueError(f"Sitio no encontrado: {site_name}. Disponibles: {self.registry.list_sites()}")

        results = []
        page = 1
        max_p = max_pages or site.config.max_pages_per_search
        consecutive_empty = 0

        logger.info(f"Starting scrape: {site_name}/{marca}" + (f"/{year}" if year else ""))

        while page <= max_p:
            result = self._scrape_page(site, marca, year, page)
            results.append(result)

            self.stats.total_requests += 1
            if result.success:
                self.stats.successful_requests += 1
                self.stats.total_listings += result.count
                self.stats.by_site[site_name] += result.count
            else:
                self.stats.failed_requests += 1
                if result.error:
                    self.stats.errors.append(f"{site_name}:{marca}:p{page} - {result.error}")

            # Check if should continue
            if not result.success:
                logger.warning(f"Page {page} failed, stopping")
                break

            if result.count == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    logger.info(f"2 consecutive empty pages, stopping")
                    break
            else:
                consecutive_empty = 0

            page += 1

            # Delay between pages
            if page <= max_p:
                time.sleep(site.config.delay_between_pages)

        total_listings = sum(r.count for r in results)
        logger.info(f"Scrape complete: {len(results)} pages, {total_listings} listings")

        return results

    def _scrape_page(
        self,
        site: BaseSite,
        marca: str,
        year: Optional[int],
        page: int
    ) -> ScrapeResult:
        """Scrapea una pagina individual."""
        start = time.time()

        try:
            # Build URL
            url = site.build_search_url(marca, year, page)
            logger.info(f"Scraping page {page}: {url}")

            # Fetch HTML
            html = self.client.get_page(url)

            # Check for blocks
            is_blocked, block_type, details = site.detect_block(html)
            if is_blocked:
                logger.warning(f"Blocked: {block_type} - {details}")
                return ScrapeResult(
                    site=site.name,
                    marca=marca,
                    year=year,
                    page=page,
                    listings=[],
                    success=False,
                    error=f"Blocked: {block_type}",
                    duration_seconds=time.time() - start
                )

            # Parse listings
            listings = site.parse(html)

            return ScrapeResult(
                site=site.name,
                marca=marca,
                year=year,
                page=page,
                listings=listings,
                success=True,
                duration_seconds=time.time() - start
            )

        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
            return ScrapeResult(
                site=site.name,
                marca=marca,
                year=year,
                page=page,
                listings=[],
                success=False,
                error=str(e),
                duration_seconds=time.time() - start
            )

    def scrape_all_sites(
        self,
        marca: str,
        year: Optional[int] = None,
        max_pages: Optional[int] = None
    ) -> Dict[str, List[ScrapeResult]]:
        """
        Scrapea una marca en TODOS los sitios registrados.

        Args:
            marca: Marca a buscar
            year: Año opcional
            max_pages: Maximo de paginas por sitio

        Returns:
            Dict site_name -> List[ScrapeResult]
        """
        all_results = {}

        for site_name in self.registry.list_sites():
            logger.info(f"=== Scraping {site_name} ===")
            try:
                results = self.scrape(site_name, marca, year, max_pages)
                all_results[site_name] = results

                # Delay between sites
                site = self.registry.get(site_name)
                if site:
                    time.sleep(site.config.delay_between_requests)

            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
                all_results[site_name] = []

        return all_results

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadisticas de scraping."""
        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "success_rate": (
                self.stats.successful_requests / self.stats.total_requests * 100
                if self.stats.total_requests > 0 else 0
            ),
            "total_listings": self.stats.total_listings,
            "by_site": self.stats.by_site,
            "error_count": len(self.stats.errors),
        }

    def list_sites(self) -> List[Dict[str, str]]:
        """Lista todos los sitios disponibles."""
        return [
            {
                "name": site.name,
                "display_name": site.config.display_name,
                "base_url": site.config.base_url
            }
            for site in self.registry
        ]

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
