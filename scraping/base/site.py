"""Base site class and registry for scraping targets."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
import logging

from .parser import BaseParser, CarListing

logger = logging.getLogger(__name__)


@dataclass
class SiteConfig:
    """Configuracion de un sitio web."""

    name: str  # Identificador unico: "cochesnet", "autocasion"
    display_name: str  # Nombre para mostrar: "Coches.net"
    base_url: str  # URL base: "https://www.coches.net"
    search_path: str  # Path de busqueda: "/segunda-mano"

    # Rate limiting
    delay_between_requests: float = 2.0  # segundos
    delay_between_pages: float = 1.0

    # Paginacion
    max_pages_per_search: int = 100
    items_per_page: int = 30


class BaseSite(ABC):
    """
    Clase base abstracta para sitios web.

    Cada sitio soportado debe implementar esta clase.
    """

    config: SiteConfig
    parser: BaseParser

    def __init__(self):
        """Initialize site with config and parser."""
        self.config = self._create_config()
        self.parser = self._create_parser()

    @abstractmethod
    def _create_config(self) -> SiteConfig:
        """Create site configuration."""
        pass

    @abstractmethod
    def _create_parser(self) -> BaseParser:
        """Create parser instance for this site."""
        pass

    @abstractmethod
    def build_search_url(
        self,
        marca: str,
        year: Optional[int] = None,
        page: int = 1
    ) -> str:
        """
        Build search URL for this site.

        Args:
            marca: Car brand (e.g., "audi", "bmw")
            year: Optional year filter
            page: Page number (1-indexed)

        Returns:
            Full URL for the search
        """
        pass

    @abstractmethod
    def detect_block(self, html: str) -> tuple:
        """
        Detect if we're blocked by anti-bot.

        Args:
            html: HTML response content

        Returns:
            Tuple (is_blocked: bool, block_type: str, details: dict)
        """
        pass

    def parse(self, html: str) -> List[CarListing]:
        """Parse HTML using site's parser."""
        return self.parser.parse(html)

    def get_total_count(self, html: str) -> Optional[int]:
        """Get total results count."""
        return self.parser.get_total_count(html)

    @property
    def name(self) -> str:
        """Site identifier."""
        return self.config.name


class SiteRegistry:
    """Registry of available scraping sites."""

    def __init__(self):
        self._sites: Dict[str, BaseSite] = {}

    def register(self, site: BaseSite) -> None:
        """
        Register a site.

        Args:
            site: Site instance to register
        """
        self._sites[site.name] = site
        logger.info(f"Registered site: {site.config.display_name}")

    def get(self, name: str) -> Optional[BaseSite]:
        """
        Get a site by name.

        Args:
            name: Site identifier

        Returns:
            Site instance or None
        """
        return self._sites.get(name)

    def list_sites(self) -> List[str]:
        """List all registered site names."""
        return list(self._sites.keys())

    def get_all(self) -> Dict[str, BaseSite]:
        """Get all registered sites."""
        return self._sites.copy()

    def __contains__(self, name: str) -> bool:
        return name in self._sites

    def __iter__(self):
        return iter(self._sites.values())


# Global registry instance
_registry: Optional[SiteRegistry] = None


def get_site_registry() -> SiteRegistry:
    """Get the global site registry."""
    global _registry
    if _registry is None:
        _registry = SiteRegistry()
    return _registry
