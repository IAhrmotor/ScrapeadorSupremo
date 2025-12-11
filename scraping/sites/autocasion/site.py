"""Autocasion.com site configuration."""

from typing import Optional
import re

from ...base.site import BaseSite, SiteConfig
from ...base.parser import BaseParser
from .parser import AutocasionParser


class AutocasionSite(BaseSite):
    """
    Configuracion para Autocasion.com.

    Formato de URLs:
    - Marca: /coches-segunda-mano/{marca}-ocasion
    - IMPORTANTE: El sufijo "-ocasion" es OBLIGATORIO (sin el da 404)
    - Paginacion: ?page={numero}

    NO soporta filtro por año en URL.
    """

    def _create_config(self) -> SiteConfig:
        return SiteConfig(
            name="autocasion",
            display_name="Autocasion.com",
            base_url="https://www.autocasion.com",
            search_path="/coches-segunda-mano",
            delay_between_requests=2.0,
            delay_between_pages=1.0,
            max_pages_per_search=50,
            items_per_page=20,
        )

    def _create_parser(self) -> BaseParser:
        return AutocasionParser()

    def build_search_url(
        self,
        marca: str,
        year: Optional[int] = None,
        page: int = 1
    ) -> str:
        """
        Construye URL de busqueda para Autocasion.com.

        IMPORTANTE: El formato correcto es /marca-ocasion (NO /marca)

        Args:
            marca: Marca en formato slug (ej: "alfa-romeo")
            year: NO SOPORTADO - se ignora (Autocasion no filtra por año en URL)
            page: Numero de pagina (1-indexed)

        Returns:
            URL completa (ej: https://www.autocasion.com/coches-segunda-mano/audi-ocasion?page=2)
        """
        # Normalizar marca a slug
        marca_slug = marca.lower().strip().replace(' ', '-')

        # IMPORTANTE: Agregar sufijo -ocasion (obligatorio)
        base = f"{self.config.base_url}{self.config.search_path}/{marca_slug}-ocasion"

        # Paginacion
        if page > 1:
            base = f"{base}?page={page}"

        # Log warning si se paso año (no soportado)
        if year:
            import logging
            logging.getLogger(__name__).warning(
                f"Autocasion no soporta filtro por año en URL. "
                f"Se ignorara year={year}"
            )

        return base

    def detect_block(self, html: str) -> tuple:
        """
        Detecta si estamos bloqueados en Autocasion.com.

        Returns:
            (is_blocked, block_type, details)
        """
        html_lower = html.lower()
        details = {"indicators": []}

        # Check for actual content first - if we have real listings data, not blocked
        has_real_content = (
            'application/ld+json' in html_lower or
            'itemlistorder' in html_lower or
            'coche de segunda mano' in html_lower or
            'autocasion.com' in html_lower and len(html) > 50000
        )

        if has_real_content:
            return False, None, details

        # Cloudflare challenge/block page (not just CDN headers)
        cloudflare_block_indicators = [
            'cf_captcha',
            'challenge-running',
            'ray id',
            'checking your browser',
            'please wait while we verify'
        ]
        if any(x in html_lower for x in cloudflare_block_indicators):
            details["indicators"].append("Cloudflare challenge detected")
            return True, "cloudflare", details

        # CAPTCHA
        if 'captcha' in html_lower and 'recaptcha' not in html_lower:
            details["indicators"].append("CAPTCHA detected")
            return True, "captcha", details

        # 404
        if '404' in html_lower and 'no encontrada' in html_lower:
            details["indicators"].append("404 error")
            return True, "error_404", details

        # Robot block
        robot_indicators = ['automated request', 'bot detected', 'access denied']
        if any(x in html_lower for x in robot_indicators):
            details["indicators"].append("Robot block")
            return True, "robot_block", details

        # Verificar contenido real
        if len(html) < 3000:
            if 'anuncio' not in html_lower and 'application/ld+json' not in html_lower:
                details["indicators"].append("No expected content")
                return True, "empty_response", details

        return False, None, details

    def get_brands_list(self) -> list:
        """
        Lista de marcas soportadas por Autocasion.com.

        Returns:
            Lista de slugs de marcas
        """
        return [
            "abarth", "alfa-romeo", "audi", "bmw", "citroen", "cupra",
            "dacia", "ds", "fiat", "ford", "honda", "hyundai", "jaguar",
            "jeep", "kia", "land-rover", "lexus", "mazda", "mercedes",
            "mini", "mitsubishi", "nissan", "opel", "peugeot", "porsche",
            "renault", "seat", "skoda", "smart", "ssangyong", "subaru",
            "suzuki", "tesla", "toyota", "volkswagen", "volvo"
        ]
