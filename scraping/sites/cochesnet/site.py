"""Coches.net site configuration."""

from typing import Optional
import re

from ...base.site import BaseSite, SiteConfig
from ...base.parser import BaseParser
from .parser import CochesNetParser


class CochesNetSite(BaseSite):
    """
    Configuracion para Coches.net.

    Formato de URLs:
    - Sin año: /segunda-mano/{marca}/
    - Con año: /segunda-mano/{marca}/{año}
    - Paginacion: ?pg={numero}

    IMPORTANTE: No existe formato de rango de años.
    Para rangos se debe iterar año por año.
    """

    def _create_config(self) -> SiteConfig:
        return SiteConfig(
            name="cochesnet",
            display_name="Coches.net",
            base_url="https://www.coches.net",
            search_path="/segunda-mano",
            delay_between_requests=2.5,
            delay_between_pages=1.5,
            max_pages_per_search=100,
            items_per_page=30,
        )

    def _create_parser(self) -> BaseParser:
        return CochesNetParser()

    def build_search_url(
        self,
        marca: str,
        year: Optional[int] = None,
        page: int = 1
    ) -> str:
        """
        Construye URL de busqueda para Coches.net.

        Args:
            marca: Marca en formato slug (ej: "audi", "land-rover")
            year: Año opcional (ej: 2020)
            page: Numero de pagina (1-indexed)

        Returns:
            URL completa (ej: https://www.coches.net/segunda-mano/audi/2020?pg=2)
        """
        # Normalizar marca a slug
        marca_slug = marca.lower().strip().replace(' ', '-')

        # Base URL
        base = f"{self.config.base_url}{self.config.search_path}/{marca_slug}"

        # Añadir año si se especifica
        if year:
            base = f"{base}/{year}"
        else:
            base = f"{base}/"

        # Añadir paginacion (solo si no es pagina 1)
        if page > 1:
            base = f"{base}?pg={page}"

        return base

    def detect_block(self, html: str) -> tuple:
        """
        Detecta si estamos bloqueados en Coches.net.

        Returns:
            (is_blocked, block_type, details)
        """
        html_lower = html.lower()
        details = {"indicators": []}

        # Imperva/Incapsula (usado por Coches.net)
        if any(x in html_lower for x in ['incapsula', 'imperva', '_incap_']):
            details["indicators"].append("Imperva/Incapsula WAF detected")
            return True, "incapsula", details

        # Cloudflare (backup protection)
        if any(x in html_lower for x in ['cloudflare', 'cf-ray', 'cf_captcha']):
            details["indicators"].append("Cloudflare detected")
            return True, "cloudflare", details

        # CAPTCHA generico
        if 'captcha' in html_lower:
            details["indicators"].append("CAPTCHA detected")
            return True, "captcha", details

        # Pagina de error
        if any(x in html_lower for x in ['pag404', 'error 404', 'página no encontrada']):
            details["indicators"].append("404 error page")
            return True, "error_404", details

        # Bloqueo por robot
        if any(x in html_lower for x in ['robot', 'automated', 'blocked', 'forbidden']):
            details["indicators"].append("Robot/automated block")
            return True, "robot_block", details

        # Verificar que hay contenido real
        if len(html) < 5000:
            # Pagina muy pequeña puede ser un error
            if 'mt-ListAds' not in html and '__INITIAL_PROPS__' not in html:
                details["indicators"].append("Page too small, no expected content")
                return True, "empty_response", details

        return False, None, details

    def get_brands_list(self) -> list:
        """
        Lista de marcas soportadas por Coches.net.

        Returns:
            Lista de slugs de marcas
        """
        return [
            "abarth", "alfa-romeo", "audi", "bmw", "citroen", "cupra",
            "dacia", "ds", "fiat", "ford", "honda", "hyundai", "jaguar",
            "jeep", "kia", "land-rover", "lexus", "mazda", "mercedes-benz",
            "mini", "mitsubishi", "nissan", "opel", "peugeot", "porsche",
            "renault", "seat", "skoda", "smart", "ssangyong", "subaru",
            "suzuki", "tesla", "toyota", "volkswagen", "volvo"
        ]
