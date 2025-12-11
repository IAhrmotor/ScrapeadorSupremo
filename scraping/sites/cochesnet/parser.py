"""Parser para Coches.net HTML/JSON."""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import json
import logging

from ...base.parser import BaseParser, CarListing
from ...base.title_parser import get_title_parser
from ...storage.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class CochesNetParser(BaseParser):
    """
    Parser para listados de coches en Coches.net.

    Estrategia de extraccion:
    1. JSON embebido (window.__INITIAL_PROPS__) - 10x mas rapido
    2. CSS selectors (fallback)

    Estructura HTML:
    - Container: div.mt-ListAds
    - Each ad: div[data-ad-id].mt-ListAds-item
    - Title: a.mt-CardAd-infoHeaderTitleLink
    - Price: p.mt-CardAdPrice-cashAmount
    """

    def __init__(self):
        super().__init__(source="cochesnet")

        # Initialize title parser with marca_modelos from DB
        try:
            supabase_client = get_supabase_client()
            self.title_parser = get_title_parser(supabase_client)
            logger.info("TitleParser initialized with database-driven parsing")
        except Exception as e:
            logger.warning(f"Failed to initialize TitleParser with DB: {e}. Using heuristic fallback only.")
            self.title_parser = get_title_parser()

    def parse(self, html: str) -> List[CarListing]:
        """Parse HTML and extract car listings."""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Try JSON first (faster)
            listings = self._extract_from_json(soup)
            if listings:
                logger.info(f"Parsed {len(listings)} ads from JSON")
                return listings

            # Fallback to CSS
            logger.info("JSON extraction failed, using CSS selectors")
            return self._extract_from_css(soup)

        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def get_total_count(self, html: str) -> Optional[int]:
        """Extract total results count."""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Try from JSON first
            scripts = soup.find_all('script')
            for script in scripts:
                text = script.string
                if not text:
                    continue

                match = re.search(r'"totalItems"\s*:\s*(\d+)', text)
                if match:
                    return int(match.group(1))

            # Fallback: count from results text
            results_text = soup.find(class_='mt-PaginationInfo-text')
            if results_text:
                match = re.search(r'de\s+([\d.]+)', results_text.get_text())
                if match:
                    return int(match.group(1).replace('.', ''))

            return None

        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return None

    def has_next_page(self, html: str, current_page: int) -> bool:
        """Check if there's a next page."""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Method 1: Check for next page link in HTML
            next_link = soup.find('a', {'rel': 'next'})
            if next_link:
                return True

            # Method 2: Check pagination from JSON data
            # Look for totalPages in full HTML (handles escaped quotes)
            match = re.search(r'totalPages.*?:\s*(\d+)', html)
            if match:
                total_pages = int(match.group(1))
                if current_page < total_pages:
                    return True

            # Method 3: Check if we have results in HTML container
            container = soup.find('div', class_='mt-ListAds')
            if container:
                ads = container.find_all('div', attrs={'data-ad-id': True})
                if len(ads) > 0:
                    # If we have ads, assume there might be more pages
                    # unless we explicitly found no pagination info
                    return True

            return False

        except Exception:
            return False

    def get_pagination_info(self, html: str) -> dict:
        """Extract pagination info from HTML/JSON."""
        info = {'current_page': None, 'total_pages': None, 'total_items': None}
        try:
            # Best pattern: totalPages and totalResults appear together
            # e.g., "totalPages":636,"totalResults":19058
            match = re.search(r'totalPages.*?:\s*(\d+).*?totalResults.*?:\s*(\d+)', html)
            if match:
                info['total_pages'] = int(match.group(1))
                info['total_items'] = int(match.group(2))
            else:
                # Fallback: extract separately
                match = re.search(r'totalPages.*?:\s*(\d+)', html)
                if match:
                    info['total_pages'] = int(match.group(1))

            # Extract currentPage
            match = re.search(r'currentPage.*?:\s*(\d+)', html)
            if match:
                info['current_page'] = int(match.group(1))

        except Exception:
            pass

        return info

    def _extract_from_json(self, soup: BeautifulSoup) -> List[CarListing]:
        """Extract cars from embedded JSON."""
        try:
            scripts = soup.find_all('script')

            for script in scripts:
                text = script.string
                if not text:
                    continue

                # Pattern: window.__INITIAL_PROPS__ = JSON.parse("...")
                match = re.search(
                    r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("(.+?)"\)',
                    text, re.DOTALL
                )
                if match:
                    try:
                        json_str = match.group(1).encode().decode('unicode_escape')
                        data = json.loads(json_str)
                        return self._parse_json_items(data)
                    except Exception as e:
                        logger.debug(f"Failed JSON parse: {e}")
                        continue

            return []

        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return []

    def _parse_json_items(self, data: Dict) -> List[CarListing]:
        """Parse items from JSON data structure."""
        listings = []

        # Find items array
        items = None
        if 'initialResults' in data and 'items' in data['initialResults']:
            items = data['initialResults']['items']
        elif 'props' in data:
            page_props = data.get('props', {}).get('pageProps', {})
            if 'initialResults' in page_props:
                items = page_props['initialResults'].get('items', [])

        if not items:
            return []

        for item in items:
            try:
                listing = self._map_json_to_listing(item)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"Error mapping item: {e}")

        return listings

    def _map_json_to_listing(self, item: Dict) -> Optional[CarListing]:
        """Map JSON item to CarListing."""
        ad_id = item.get('id')
        if not ad_id:
            return None

        title = item.get('title', '')
        url_path = item.get('url', '')

        # Parse title using TitleParser
        parsed = self.title_parser.parse(title)

        # Extract fuel and transmission from JSON
        fuel_type = item.get('fuelType', '')
        transmission = item.get('gearbox', '') or item.get('transmission', '')

        # Normalize values
        marca = parsed.marca or self._extract_marca(title)
        marca_normalized = self._normalize_marca(marca) if marca else None
        fuel_normalized = self._normalize_fuel(fuel_type)

        # Create extra_fields with all parsed data
        extra_fields = {
            'version': parsed.version,
            'parsing_confidence': parsed.confidence,
            'parsing_method': 'database' if parsed.confidence >= 0.7 else 'heuristic',
            'marca_normalizada': marca_normalized,
            'modelo_completo': parsed.modelo,
            'modelo_variante': parsed.version,
            'transmission': transmission,
            'combustible_normalizado': fuel_normalized
        }

        return CarListing(
            ad_id=str(ad_id),
            source=self.source,
            url=f"https://www.coches.net{url_path}" if url_path else None,
            title=title,
            marca=marca,
            modelo=parsed.modelo or self._extract_modelo(title),
            version=parsed.version,
            year=item.get('year'),
            kilometers=item.get('km'),
            fuel=fuel_type,
            power_cv=item.get('hp'),
            transmission=transmission,
            price=item.get('price'),
            price_text=f"{item.get('price'):,} EUR".replace(',', '.') if item.get('price') else None,
            location=item.get('location'),
            raw_data=item,
            extra_fields=extra_fields
        )

    def _extract_from_css(self, soup: BeautifulSoup) -> List[CarListing]:
        """Extract cars using CSS selectors."""
        listings = []

        container = soup.find('div', class_='mt-ListAds')
        if not container:
            logger.warning("No mt-ListAds container found")
            return []

        ad_items = container.find_all('div', attrs={'data-ad-id': True})
        logger.info(f"Found {len(ad_items)} ads via CSS")

        for ad in ad_items:
            try:
                listing = self._parse_ad_element(ad)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"Error parsing ad: {e}")

        return listings

    def _parse_ad_element(self, ad) -> Optional[CarListing]:
        """Parse single ad element."""
        ad_id = ad.get('data-ad-id')
        if not ad_id:
            return None

        # Skip placeholders and native ads
        if ad.find('div', class_='sui-PerfDynamicRendering-placeholder'):
            return None
        if 'mt-ListAds-item--native' in ad.get('class', []):
            return None

        # Title and URL
        title_link = ad.find('a', class_='mt-CardAd-infoHeaderTitleLink')
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        url_path = title_link.get('href', '')

        # Parse title using TitleParser
        parsed = self.title_parser.parse(title)

        # Price
        price_elem = ad.find('p', {'data-testid': 'card-adPrice-price'})
        price_text = price_elem.get_text(strip=True) if price_elem else None
        price_numeric = self._extract_number(price_text)

        # Attributes
        attrs = self._parse_attributes(ad)

        # Normalize values
        marca = parsed.marca or self._extract_marca(title)
        marca_normalized = self._normalize_marca(marca) if marca else None
        fuel_type = attrs.get('fuel', '')
        fuel_normalized = self._normalize_fuel(fuel_type)
        transmission = attrs.get('transmission', '')

        # Create extra_fields with all parsed data
        extra_fields = {
            'version': parsed.version,
            'parsing_confidence': parsed.confidence,
            'parsing_method': 'database' if parsed.confidence >= 0.7 else 'heuristic',
            'marca_normalizada': marca_normalized,
            'modelo_completo': parsed.modelo,
            'modelo_variante': parsed.version,
            'transmission': transmission,
            'combustible_normalizado': fuel_normalized
        }

        return CarListing(
            ad_id=str(ad_id),
            source=self.source,
            url=f"https://www.coches.net{url_path}" if url_path else None,
            title=title,
            marca=marca,
            modelo=parsed.modelo or self._extract_modelo(title),
            version=parsed.version,
            year=attrs.get('year'),
            kilometers=attrs.get('kilometers'),
            fuel=fuel_type,
            power_cv=attrs.get('power'),
            transmission=transmission,
            price=price_numeric,
            price_text=price_text,
            location=attrs.get('location'),
            extra_fields=extra_fields
        )

    def _parse_attributes(self, ad) -> Dict[str, Any]:
        """Parse attributes list."""
        attrs = {}

        attr_list = ad.find('ul', class_='mt-CardAd-attr')
        if not attr_list:
            return attrs

        items = attr_list.find_all('li', class_='mt-CardAd-attrItem')
        items = [i for i in items if 'mt-CardAd-attrItemEnvironmentalLabel' not in i.get('class', [])]

        for item in items:
            text = item.get_text(strip=True)

            if self._is_fuel(text):
                attrs['fuel'] = text
            elif self._is_year(text):
                attrs['year'] = int(text)
            elif 'km' in text.lower():
                attrs['kilometers'] = self._extract_number(text)
            elif 'cv' in text.lower():
                attrs['power'] = self._extract_number(text)
            else:
                attrs['location'] = text

        return attrs

    def _is_fuel(self, text: str) -> bool:
        """Check if text is fuel type."""
        fuels = ['diesel', 'gasolina', 'electrico', 'hibrido', 'gas']
        return any(f in text.lower() for f in fuels)

    def _is_year(self, text: str) -> bool:
        """Check if text is a year."""
        return bool(re.match(r'^(19|20)\d{2}$', text))

    def _extract_marca(self, title: str) -> Optional[str]:
        """Extract brand from title."""
        if not title:
            return None
        parts = title.split()
        return parts[0] if parts else None

    def _extract_modelo(self, title: str) -> Optional[str]:
        """Extract model from title."""
        if not title:
            return None
        parts = title.split(maxsplit=1)
        return parts[1] if len(parts) > 1 else None

    def _normalize_marca(self, marca: str) -> str:
        """Normalize brand name for database lookup."""
        if not marca:
            return ""
        # Convert to uppercase, remove extra spaces
        normalized = marca.strip().upper()
        # Handle common variations
        replacements = {
            'MERCEDES-BENZ': 'MERCEDES',
            'MERCEDES BENZ': 'MERCEDES',
            'ALFA-ROMEO': 'ALFA ROMEO',
            'LAND-ROVER': 'LAND ROVER',
            'ASTON-MARTIN': 'ASTON MARTIN',
        }
        return replacements.get(normalized, normalized)

    def _normalize_fuel(self, fuel: str) -> str:
        """Normalize fuel type."""
        if not fuel:
            return ""
        fuel_lower = fuel.lower().strip()
        # Map to standard values
        fuel_map = {
            'diesel': 'DIESEL',
            'diésel': 'DIESEL',
            'gasolina': 'GASOLINA',
            'petrol': 'GASOLINA',
            'eléctrico': 'ELECTRICO',
            'electrico': 'ELECTRICO',
            'electric': 'ELECTRICO',
            'híbrido': 'HIBRIDO',
            'hibrido': 'HIBRIDO',
            'hybrid': 'HIBRIDO',
            'híbrido enchufable': 'HIBRIDO_ENCHUFABLE',
            'plug-in hybrid': 'HIBRIDO_ENCHUFABLE',
            'gas': 'GAS',
            'glp': 'GLP',
            'gnc': 'GNC',
        }
        return fuel_map.get(fuel_lower, fuel.upper())
