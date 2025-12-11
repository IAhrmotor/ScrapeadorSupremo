"""OcasionPlus HTML parser for extracting vehicle listings."""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scraping.base.title_parser import TitleParser, get_title_parser


@dataclass
class OcasionPlusListing:
    """Represents a single vehicle listing from OcasionPlus."""

    # Identificación
    url: str = ""
    listing_id: str = ""

    # Vehículo
    marca: str = ""
    modelo: str = ""
    version: str = ""
    potencia_cv: Optional[int] = None
    titulo_completo: str = ""

    # Precios
    precio_contado: Optional[int] = None
    precio_financiado: Optional[int] = None
    cuota_mensual: Optional[int] = None

    # Características
    year: Optional[int] = None
    kilometros: Optional[int] = None
    combustible: str = ""
    transmision: str = ""
    etiqueta_ambiental: str = ""

    # Ubicación
    ubicacion: str = ""

    # Media
    imagen_url: str = ""

    def to_dict(self) -> dict:
        """Convert listing to dictionary."""
        return {
            "url": self.url,
            "listing_id": self.listing_id,
            "marca": self.marca,
            "modelo": self.modelo,
            "version": self.version,
            "potencia_cv": self.potencia_cv,
            "titulo_completo": self.titulo_completo,
            "precio_contado": self.precio_contado,
            "precio_financiado": self.precio_financiado,
            "cuota_mensual": self.cuota_mensual,
            "year": self.year,
            "kilometros": self.kilometros,
            "combustible": self.combustible,
            "transmision": self.transmision,
            "etiqueta_ambiental": self.etiqueta_ambiental,
            "ubicacion": self.ubicacion,
            "imagen_url": self.imagen_url,
        }


class OcasionPlusParser:
    """Parser for OcasionPlus vehicle listings."""

    BASE_URL = "https://www.ocasionplus.com"

    # CSS selectors based on data-test attributes
    SELECTORS = {
        "card": "div.cardVehicle_card__LwFCi",
        "link": "a.cardVehicle_link__l8xYT",
        "brand_model": "[data-test='span-brand-model']",
        "version": "[data-test='span-version']",
        "price": "[data-test='span-price']",
        "finance_price": "[data-test='span-finance']",
        "finance_quote": "[data-test='span-finace-quote']",
        "year": "[data-test='span-registration-date']",
        "km": "[data-test='span-km']",
        "fuel": "[data-test='span-fuel-type']",
        "transmission": "[data-test='span-engine-transmission']",
        "dealer": "[data-test='div-dealer']",
        "image": "div.cardVehicle_image__fPk_E img",
        "env_label": "img[alt='distintivo-ambiental']",
    }

    def __init__(self, supabase_client=None):
        """
        Initialize parser with optional Supabase client for marca/modelo validation.

        Args:
            supabase_client: Optional Supabase client to load marcas_modelos_validos
        """
        self._title_parser: Optional[TitleParser] = None
        self._supabase = supabase_client

    def _get_title_parser(self) -> TitleParser:
        """Get or create title parser with marca/modelo validation."""
        if self._title_parser is None:
            if self._supabase:
                self._title_parser = get_title_parser(self._supabase)
            else:
                # Try to get supabase client
                try:
                    from scraping.storage.supabase_client import get_supabase_client
                    self._supabase = get_supabase_client()
                    self._title_parser = get_title_parser(self._supabase)
                except Exception:
                    # Fallback to parser without DB validation
                    self._title_parser = TitleParser()
        return self._title_parser

    def parse_listings(self, html: str) -> list[OcasionPlusListing]:
        """
        Parse all vehicle listings from HTML.

        Args:
            html: Raw HTML content

        Returns:
            List of OcasionPlusListing objects
        """
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        # Find all vehicle cards
        cards = soup.select(self.SELECTORS["card"])

        for card in cards:
            try:
                listing = self._parse_card(card)
                if listing and listing.url:
                    listings.append(listing)
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue

        return listings

    def _parse_card(self, card) -> Optional[OcasionPlusListing]:
        """Parse a single vehicle card."""
        listing = OcasionPlusListing()

        # URL and ID
        link = card.select_one(self.SELECTORS["link"])
        if link and link.get("href"):
            href = link["href"]
            listing.url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
            listing.listing_id = self._extract_id_from_url(href)

        # Brand and Model
        brand_model = card.select_one(self.SELECTORS["brand_model"])
        if brand_model:
            listing.titulo_completo = brand_model.get_text(strip=True)
            listing.marca, listing.modelo = self._split_brand_model(listing.titulo_completo)

        # Version and Power
        version = card.select_one(self.SELECTORS["version"])
        if version:
            version_text = version.get_text(strip=True)
            listing.version, listing.potencia_cv = self._parse_version_and_power(version_text)

        # Prices
        price = card.select_one(self.SELECTORS["price"])
        if price:
            listing.precio_contado = self._parse_price(price.get_text(strip=True))

        finance = card.select_one(self.SELECTORS["finance_price"])
        if finance:
            listing.precio_financiado = self._parse_price(finance.get_text(strip=True))

        quote = card.select_one(self.SELECTORS["finance_quote"])
        if quote:
            listing.cuota_mensual = self._parse_price(quote.get_text(strip=True))

        # Year
        year = card.select_one(self.SELECTORS["year"])
        if year:
            listing.year = self._parse_year(year.get_text(strip=True))

        # Kilometers
        km = card.select_one(self.SELECTORS["km"])
        if km:
            listing.kilometros = self._parse_km(km.get_text(strip=True))

        # Fuel type
        fuel = card.select_one(self.SELECTORS["fuel"])
        if fuel:
            listing.combustible = fuel.get_text(strip=True)

        # Transmission
        trans = card.select_one(self.SELECTORS["transmission"])
        if trans:
            listing.transmision = trans.get_text(strip=True)

        # Location
        dealer = card.select_one(self.SELECTORS["dealer"])
        if dealer:
            listing.ubicacion = dealer.get_text(strip=True)

        # Image
        img = card.select_one(self.SELECTORS["image"])
        if img and img.get("src"):
            listing.imagen_url = img["src"]

        # Environmental label
        env_img = card.select_one(self.SELECTORS["env_label"])
        if env_img:
            # Extract label from src (e.g., "/hera/icons/C.svg" -> "C")
            src = env_img.get("src", "")
            match = re.search(r"/([A-Z0-9]+)\.svg", src, re.IGNORECASE)
            if match:
                listing.etiqueta_ambiental = match.group(1).upper()

        return listing

    def _extract_id_from_url(self, url: str) -> str:
        """Extract listing ID from URL."""
        # URL format: /coches-segunda-mano/cupra-formentor-20-tsi-vz-dsg-con-24228km-2023-vwummqar
        # ID is the last segment after the last dash
        parts = url.rstrip("/").split("-")
        if parts:
            return parts[-1]
        return ""

    def _split_brand_model(self, text: str) -> tuple[str, str]:
        """
        Split brand-model text into separate brand and model.

        Uses TitleParser to validate against marcas_modelos_validos table.
        Falls back to simple split if no match found.
        """
        # Try TitleParser first for validated marca/modelo
        try:
            parser = self._get_title_parser()
            result = parser.parse(text)

            if result.marca and result.confidence > 0.5:
                # Use validated marca and modelo
                marca = result.marca
                modelo = result.modelo or ""
                return marca, modelo
        except Exception:
            pass

        # Fallback to simple split
        parts = text.split(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return text, ""

    def _parse_version_and_power(self, text: str) -> tuple[str, Optional[int]]:
        """
        Parse version text and extract power in CV.

        Args:
            text: Version string like "2.0 TSI VZ DSG (245 CV)"

        Returns:
            (version_clean, power_cv) - e.g. ("2.0 TSI VZ DSG", 245)
        """
        # Pattern to match power: (XXX CV) at the end
        power_match = re.search(r"\((\d+)\s*CV\)", text, re.IGNORECASE)

        if power_match:
            power_cv = int(power_match.group(1))
            # Remove the power part from version
            version_clean = re.sub(r"\s*\(\d+\s*CV\)", "", text).strip()
            return version_clean, power_cv

        return text, None

    def _parse_price(self, text: str) -> Optional[int]:
        """Parse price text to integer."""
        # "39.990€" -> 39990
        clean = re.sub(r"[^\d]", "", text)
        return int(clean) if clean else None

    def _parse_year(self, text: str) -> Optional[int]:
        """Parse year from text."""
        match = re.search(r"\d{4}", text)
        return int(match.group()) if match else None

    def _parse_km(self, text: str) -> Optional[int]:
        """Parse kilometers from text."""
        # "24.228 Km" -> 24228
        clean = re.sub(r"[^\d]", "", text)
        return int(clean) if clean else None

    def get_total_count(self, html: str) -> Optional[int]:
        """
        Try to extract total listing count from page.

        Args:
            html: Raw HTML content

        Returns:
            Total count if found, None otherwise
        """
        soup = BeautifulSoup(html, "html.parser")

        # Look for count indicators (adjust selector based on actual site)
        count_patterns = [
            r"(\d+[\d.]*)\s*coches",
            r"(\d+[\d.]*)\s*vehículos",
            r"(\d+[\d.]*)\s*resultados",
        ]

        text = soup.get_text()
        for pattern in count_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(".", "")
                return int(count_str)

        return None
