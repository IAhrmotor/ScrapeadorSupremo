"""Clicars.com site configuration and URL building."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClicarsConfig:
    """Configuration for Clicars scraping."""

    base_url: str = "https://www.clicars.com"
    search_url: str = "https://www.clicars.com/coches-segunda-mano-ocasion"

    # Delays
    delay_between_scrolls: float = 2.0
    delay_between_clicks: float = 3.0
    delay_after_load: float = 2.0

    # Scroll settings
    scroll_step: int = 500
    max_scroll_attempts: int = 100

    # Load more button - <button data-action="next-page">Ver más coches</button>
    load_more_button_selector: str = "button[data-action='next-page']"

    # Listings
    listings_per_load: int = 12
    expected_total_listings: int = 2329  # As shown on site


class ClicarsSite:
    """Clicars.com site handler - infinite scroll pattern."""

    def __init__(self, config: Optional[ClicarsConfig] = None):
        self.config = config or ClicarsConfig()

    def get_search_url(self, filters: Optional[dict] = None) -> str:
        """
        Build search URL with optional filters.

        Note: Clicars uses infinite scroll, so there's only ONE URL.
        All cars are loaded dynamically on the same page.
        """
        url = self.config.search_url

        if filters:
            # Add filters as query params if needed
            # Example: ?marca=audi&precio_min=10000
            params = []
            for key, value in filters.items():
                params.append(f"{key}={value}")
            if params:
                url += "?" + "&".join(params)

        return url

    def detect_block(self, html: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Detect if page is blocked by anti-bot protection.

        Returns:
            (is_blocked, block_type, message)
        """
        html_lower = html.lower()

        # Cloudflare
        if "cloudflare" in html_lower and ("challenge" in html_lower or "checking your browser" in html_lower):
            return True, "cloudflare", "Cloudflare challenge detected"

        # DataDome
        if "datadome" in html_lower:
            return True, "datadome", "DataDome protection detected"

        # Generic bot detection
        if "access denied" in html_lower or "forbidden" in html_lower:
            return True, "access_denied", "Access denied"

        # Check for actual content
        if "coches" not in html_lower and "clicars" not in html_lower:
            return True, "no_content", "Page content missing"

        return False, None, None
