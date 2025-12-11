"""OcasionPlus.com site configuration and URL building."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode


@dataclass
class OcasionPlusConfig:
    """Configuration for OcasionPlus scraping."""

    base_url: str = "https://www.ocasionplus.com"
    search_path: str = "/coches-segunda-mano"

    # Delays
    delay_between_scrolls: float = 2.0
    delay_between_clicks: float = 3.0
    delay_after_load: float = 2.0

    # Scroll settings (infinite scroll pattern)
    scroll_step: int = 500
    max_scroll_attempts: int = 200

    # Load more button selector - OcasionPlus uses "Ver más coches" button
    load_more_button_selector: str = "button.seeMoreCars_button__WXdaL, button[class*='seeMoreCars']"

    # Listings
    listings_per_load: int = 24


class OcasionPlusSite:
    """OcasionPlus.com site handler - infinite scroll pattern."""

    def __init__(self, config: Optional[OcasionPlusConfig] = None):
        self.config = config or OcasionPlusConfig()

    def get_search_url(
        self,
        year_from: int = 2007,
        year_to: int = 2025,
        order_by: str = "morePopular",
        filters: Optional[dict] = None
    ) -> str:
        """
        Build search URL with year range and optional filters.

        Args:
            year_from: Año inicial (default 2007)
            year_to: Año final (default 2025)
            order_by: Ordenación (morePopular, lowerPrice, higherPrice, etc.)
            filters: Filtros adicionales (marca, precio, km, etc.)

        Returns:
            URL completa para scraping

        Note: OcasionPlus uses infinite scroll, all cars load on same page.
        """
        base_url = f"{self.config.base_url}{self.config.search_path}"

        # Base params
        params = {
            "v2": "",
            "orderBy": order_by,
            "year[from]": year_from,
            "year[to]": year_to,
        }

        # Add extra filters
        if filters:
            params.update(filters)

        # Build URL manually to handle special chars
        param_parts = []
        for key, value in params.items():
            if value == "":
                param_parts.append(key)
            else:
                param_parts.append(f"{key}={value}")

        return f"{base_url}?{'&'.join(param_parts)}"

    def get_url_for_brand(self, marca: str, year_from: int = 2007, year_to: int = 2025) -> str:
        """
        Build search URL filtered by brand.

        Args:
            marca: Marca en formato slug (ej: "audi", "bmw")
            year_from: Año inicial
            year_to: Año final

        Returns:
            URL filtrada por marca
        """
        return self.get_search_url(
            year_from=year_from,
            year_to=year_to,
            filters={"brand": marca.lower()}
        )

    def detect_block(self, html: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Detect if page is blocked by anti-bot protection.

        Returns:
            (is_blocked, block_type, message)
        """
        html_lower = html.lower()

        # Cloudflare - be more specific to avoid false positives
        cloudflare_blocked = (
            ("cf-browser-verification" in html_lower) or
            ("cf_captcha_kind" in html_lower) or
            ("checking your browser" in html_lower and "cloudflare" in html_lower) or
            ("cf-challenge-running" in html_lower)
        )
        if cloudflare_blocked:
            return True, "cloudflare", "Cloudflare challenge detected"

        # DataDome
        if "datadome" in html_lower:
            return True, "datadome", "DataDome protection detected"

        # Imperva/Incapsula
        if any(x in html_lower for x in ['incapsula', 'imperva', '_incap_']):
            return True, "incapsula", "Imperva/Incapsula WAF detected"

        # Generic bot detection
        if "access denied" in html_lower or "forbidden" in html_lower:
            return True, "access_denied", "Access denied"

        # CAPTCHA
        if "captcha" in html_lower and "recaptcha" not in html_lower:
            return True, "captcha", "CAPTCHA detected"

        # Check for actual content
        if "ocasionplus" not in html_lower and "coches" not in html_lower:
            return True, "no_content", "Page content missing"

        return False, None, None

    def get_brands_list(self) -> list[str]:
        """
        Lista de marcas comunes disponibles en OcasionPlus.

        Returns:
            Lista de slugs de marcas
        """
        return [
            "abarth", "alfa-romeo", "audi", "bmw", "citroen", "cupra",
            "dacia", "ds", "fiat", "ford", "honda", "hyundai", "jaguar",
            "jeep", "kia", "land-rover", "lexus", "mazda", "mercedes",
            "mini", "mitsubishi", "nissan", "opel", "peugeot", "porsche",
            "renault", "seat", "skoda", "smart", "subaru", "suzuki",
            "tesla", "toyota", "volkswagen", "volvo"
        ]
