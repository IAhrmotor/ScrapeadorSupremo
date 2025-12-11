"""Base parser class for HTML/JSON extraction."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CarListing:
    """Modelo unificado de anuncio de coche."""

    # Identificacion
    ad_id: str
    source: str  # "cochesnet", "autocasion"
    url: Optional[str] = None

    # Vehiculo
    marca: Optional[str] = None
    modelo: Optional[str] = None
    version: Optional[str] = None
    title: Optional[str] = None

    # Caracteristicas
    year: Optional[int] = None
    kilometers: Optional[int] = None
    fuel: Optional[str] = None
    power_cv: Optional[int] = None
    transmission: Optional[str] = None

    # Precio
    price: Optional[int] = None
    price_text: Optional[str] = None

    # Ubicacion
    location: Optional[str] = None
    provincia: Optional[str] = None

    # Metadata
    raw_data: Dict[str, Any] = field(default_factory=dict)
    extra_fields: Dict[str, Any] = field(default_factory=dict)  # For parser metadata (confidence, etc.)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ad_id": self.ad_id,
            "source": self.source,
            "url": self.url,
            "marca": self.marca,
            "modelo": self.modelo,
            "version": self.version,
            "title": self.title,
            "year": self.year,
            "kilometers": self.kilometers,
            "fuel": self.fuel,
            "power_cv": self.power_cv,
            "transmission": self.transmission,
            "price": self.price,
            "price_text": self.price_text,
            "location": self.location,
            "provincia": self.provincia,
        }


class BaseParser(ABC):
    """
    Clase base abstracta para parsers de HTML.

    Cada sitio implementa su propio parser heredando de esta clase.
    """

    def __init__(self, source: str):
        """
        Initialize parser.

        Args:
            source: Nombre del sitio (ej: "cochesnet")
        """
        self.source = source

    @abstractmethod
    def parse(self, html: str) -> List[CarListing]:
        """
        Parse HTML and extract car listings.

        Args:
            html: HTML content from the site

        Returns:
            List of CarListing objects
        """
        pass

    @abstractmethod
    def get_total_count(self, html: str) -> Optional[int]:
        """
        Extract total number of results from HTML.

        Args:
            html: HTML content

        Returns:
            Total count or None if not found
        """
        pass

    @abstractmethod
    def has_next_page(self, html: str, current_page: int) -> bool:
        """
        Check if there's a next page.

        Args:
            html: HTML content
            current_page: Current page number

        Returns:
            True if next page exists
        """
        pass

    def _extract_number(self, text: str) -> Optional[int]:
        """Extract first number from text (utility method)."""
        import re
        if not text:
            return None
        digits = re.sub(r'[^\d]', '', text)
        return int(digits) if digits else None
