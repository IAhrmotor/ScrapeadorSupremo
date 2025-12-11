"""Parser para Autocasion.com HTML/JSON-LD."""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import json
import logging

from ...base.parser import BaseParser, CarListing

logger = logging.getLogger(__name__)


class AutocasionParser(BaseParser):
    """
    Parser para listados de coches en Autocasion.com.

    Estrategia de extraccion (3 niveles):
    1. JSON-LD schema.org (PRIMARY - mas completo y rapido)
    2. JSON embebido (window.__APP_CONTEXT__, __NEXT_DATA__, etc.)
    3. CSS selectors (fallback)

    URL Format:
    - Brand pages: /coches-segunda-mano/{marca}-ocasion
    - NOT: /coches-segunda-mano/{marca} (returns 404)
    """

    def __init__(self):
        super().__init__(source="autocasion")

    def parse(self, html: str) -> List[CarListing]:
        """Parse HTML and extract car listings using 3-tier strategy."""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Tier 1: JSON-LD (most reliable)
            listings = self._extract_from_jsonld(soup)
            if listings:
                listings = self._enrich_from_html(soup, listings)
                logger.info(f"Parsed {len(listings)} ads from JSON-LD")
                return listings

            # Tier 2: Embedded JSON
            listings = self._extract_from_embedded_json(soup)
            if listings:
                logger.info(f"Parsed {len(listings)} ads from embedded JSON")
                return listings

            # Tier 3: CSS selectors (fallback)
            logger.info("JSON extraction failed, using CSS selectors")
            return self._extract_from_css(soup)

        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def get_total_count(self, html: str) -> Optional[int]:
        """Extract total count from H1 tag. Format: '638 Alfa Romeo de segunda mano'"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            h1 = soup.find('h1')

            if not h1:
                return None

            h1_text = h1.get_text(strip=True)
            match = re.match(r'^(\d+)\s+', h1_text)
            if match:
                return int(match.group(1))

            return None

        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return None

    def get_total_pages(self, html: str, listings_per_page: int = 30) -> int:
        """
        Get total number of pages from pagination element.

        Args:
            html: HTML content of the first page
            listings_per_page: Number of listings per page (fallback calculation)

        Returns:
            Total number of pages (minimum 1)
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Method 1: Try to find the pagination element with class "total_pages"
            total_pages_elem = soup.find('a', class_='total_pages')
            if total_pages_elem and total_pages_elem.text.strip().isdigit():
                pages = int(total_pages_elem.text.strip())
                logger.debug(f"Found total pages from pagination: {pages}")
                return max(1, pages)

            # Method 2: Find the last numbered page in pagination
            pagination = soup.find(class_=lambda x: x and 'pag' in str(x).lower())
            if pagination:
                # Find all page number links
                page_links = pagination.find_all('a', href=True)
                max_page = 1
                for link in page_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    # Try to get page number from text
                    if text.isdigit():
                        max_page = max(max_page, int(text))

                    # Try to get page number from URL parameter ?page=N
                    page_match = re.search(r'[?&]page=(\d+)', href)
                    if page_match:
                        max_page = max(max_page, int(page_match.group(1)))

                if max_page > 1:
                    logger.debug(f"Found max page from pagination links: {max_page}")
                    return max_page

            # Method 3: Fallback - calculate from total count
            total_count = self.get_total_count(html)
            if total_count:
                import math
                pages = max(1, math.ceil(total_count / listings_per_page))
                logger.debug(f"Calculated pages from count ({total_count} / {listings_per_page}): {pages}")
                return pages

            logger.warning("Could not determine total pages, defaulting to 1")
            return 1

        except Exception as e:
            logger.error(f"Error getting total pages: {e}")
            # Fallback calculation
            total_count = self.get_total_count(html)
            if total_count:
                import math
                return max(1, math.ceil(total_count / listings_per_page))
            return 1

    def has_next_page(self, html: str, current_page: int) -> bool:
        """Check if there's a next page."""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Check for next link
            next_link = soup.find('a', rel='next')
            if next_link:
                return True

            # Check pagination class
            next_link = soup.find('a', class_=lambda x: x and 'next' in str(x).lower())
            if next_link:
                return True

            # Check pagination container
            pagination = soup.find(class_=lambda x: x and 'pag' in str(x).lower())
            if pagination:
                links = pagination.find_all('a', href=True)
                return len(links) > 0

            return False

        except Exception:
            return False

    def get_next_page_url(self, html: str) -> Optional[str]:
        """Extract next page URL from pagination."""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Look for "next" pagination link
            next_link = soup.find('a', class_=lambda x: x and 'next' in str(x).lower())

            if not next_link:
                next_link = soup.find('a', rel='next')

            if not next_link:
                pagination = soup.find(class_=lambda x: x and 'pag' in str(x).lower())
                if pagination:
                    links = pagination.find_all('a', href=True)
                    if links:
                        next_link = links[-1]

            if next_link:
                href = next_link.get('href')
                if href:
                    if href.startswith('/'):
                        href = f'https://www.autocasion.com{href}'
                    return href

            return None

        except Exception as e:
            logger.error(f"Error extracting next page URL: {e}")
            return None

    # =====================
    # TIER 1: JSON-LD
    # =====================

    def _extract_from_jsonld(self, soup: BeautifulSoup) -> List[CarListing]:
        """Extract cars from JSON-LD schema.org data (primary method)."""
        try:
            jsonld_scripts = soup.find_all('script', type='application/ld+json')

            if not jsonld_scripts:
                return []

            listings = []

            for script in jsonld_scripts:
                try:
                    content = script.string
                    if not content:
                        continue

                    data = json.loads(content)
                    items = data if isinstance(data, list) else [data]

                    for item in items:
                        item_type = item.get('@type', '')
                        if item_type not in ['Product', 'Car', 'Vehicle']:
                            continue

                        listing = self._map_jsonld_to_listing(item)
                        if listing:
                            listings.append(listing)

                except json.JSONDecodeError:
                    continue

            return listings

        except Exception as e:
            logger.error(f"Error extracting JSON-LD: {e}")
            return []

    def _map_jsonld_to_listing(self, item: Dict) -> Optional[CarListing]:
        """Map JSON-LD schema.org item to CarListing."""
        try:
            offers = item.get('offers', {})
            item_offered = offers.get('itemOffered', {})
            brand_obj = item.get('brand', {})

            # Extract basic info
            marca = brand_obj.get('name', '') if isinstance(brand_obj, dict) else str(brand_obj)
            modelo = item_offered.get('model', '')
            nombre = item.get('name', '')
            ad_id = item_offered.get('identifier')

            if not ad_id:
                return None

            # Extract version from name
            version = self._extract_version(nombre, marca, modelo)

            # Extract kilometers
            km = None
            mileage = item_offered.get('mileageFromOdometer', {})
            if isinstance(mileage, dict):
                km = mileage.get('value')
            elif isinstance(mileage, (int, float)):
                km = int(mileage)

            # Extract power
            power = None
            engine = item_offered.get('vehicleEngine', {})
            if isinstance(engine, dict):
                power_obj = engine.get('enginePower', {})
                if isinstance(power_obj, dict):
                    power = power_obj.get('value')
                elif isinstance(power_obj, (int, float)):
                    power = int(power_obj)

            # Extract price
            price = None
            price_str = offers.get('price')
            if price_str:
                try:
                    price = int(price_str)
                except ValueError:
                    price = self._extract_number(str(price_str))

            return CarListing(
                ad_id=str(ad_id),
                source=self.source,
                url=offers.get('url'),
                title=nombre,
                marca=marca.upper() if marca else None,
                modelo=modelo,
                version=version,
                year=item_offered.get('productionDate'),
                kilometers=km,
                fuel=self._infer_fuel_type(version, nombre),
                power_cv=power,
                transmission=item_offered.get('vehicleTransmission'),
                price=price,
                price_text=f"{price} EUR" if price else None,
                raw_data=item
            )

        except Exception as e:
            logger.debug(f"Error mapping JSON-LD: {e}")
            return None

    def _enrich_from_html(self, soup: BeautifulSoup, listings: List[CarListing]) -> List[CarListing]:
        """Enrich JSON-LD data with HTML article data (fuel, location)."""
        try:
            articles = soup.find_all('article', class_='anuncio')

            # Build mapping ad_id -> article attrs
            article_data = {}
            for article in articles:
                ad_id = self._extract_ad_id_from_article(article)
                if not ad_id:
                    continue

                ul = article.find('ul')
                if not ul:
                    continue

                attrs = {'fuel': None, 'location': None}

                for li in ul.find_all('li'):
                    text = li.get_text(strip=True)
                    text_lower = text.lower()

                    # Fuel type
                    if any(f in text_lower for f in ['diésel', 'diesel', 'gasolina', 'híbrido', 'hibrido', 'eléctrico', 'electrico', 'glp', 'gnc']):
                        attrs['fuel'] = text
                    # Location (not year, not km)
                    elif not re.match(r'^\d{4}$', text) and 'km' not in text_lower:
                        attrs['location'] = text

                article_data[str(ad_id)] = attrs

            # Enrich listings
            for listing in listings:
                if listing.ad_id in article_data:
                    attrs = article_data[listing.ad_id]
                    if not listing.fuel and attrs.get('fuel'):
                        listing.fuel = attrs['fuel']
                    if attrs.get('location'):
                        listing.location = attrs['location']

            return listings

        except Exception as e:
            logger.debug(f"Error enriching from HTML: {e}")
            return listings

    # =====================
    # TIER 2: Embedded JSON
    # =====================

    def _extract_from_embedded_json(self, soup: BeautifulSoup) -> List[CarListing]:
        """Extract cars from embedded JSON (window.__APP_CONTEXT__, __NEXT_DATA__, etc.)."""
        try:
            scripts = soup.find_all('script')

            for script in scripts:
                script_text = script.string
                if not script_text:
                    continue

                json_data = None

                # Pattern 1: window.__APP_CONTEXT__
                match = re.search(r'window\.__APP_CONTEXT__\s*=\s*({.+?});', script_text, re.DOTALL)
                if match:
                    try:
                        json_data = json.loads(match.group(1))
                        logger.debug("Found JSON via __APP_CONTEXT__")
                    except Exception:
                        pass

                # Pattern 2: window.__INITIAL_STATE__
                if not json_data:
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script_text, re.DOTALL)
                    if match:
                        try:
                            json_data = json.loads(match.group(1))
                            logger.debug("Found JSON via __INITIAL_STATE__")
                        except Exception:
                            pass

                # Pattern 3: __NEXT_DATA__
                if not json_data:
                    match = re.search(r'__NEXT_DATA__\s*=\s*({.+?})</script>', script_text, re.DOTALL)
                    if match:
                        try:
                            json_data = json.loads(match.group(1))
                            logger.debug("Found JSON via __NEXT_DATA__")
                        except Exception:
                            pass

                # Pattern 4: window.__DATA__
                if not json_data:
                    match = re.search(r'window\.__DATA__\s*=\s*({.+?});', script_text, re.DOTALL)
                    if match:
                        try:
                            json_data = json.loads(match.group(1))
                            logger.debug("Found JSON via __DATA__")
                        except Exception:
                            pass

                if json_data:
                    listings = self._parse_embedded_json(json_data)
                    if listings:
                        return listings

            return []

        except Exception as e:
            logger.error(f"Error extracting embedded JSON: {e}")
            return []

    def _parse_embedded_json(self, json_data: Dict) -> List[CarListing]:
        """Parse embedded JSON structure to extract car listings."""
        try:
            items = None

            # Path 1: Direct items/vehicles
            if 'items' in json_data:
                items = json_data['items']
            elif 'vehicles' in json_data:
                items = json_data['vehicles']
            elif 'ads' in json_data:
                items = json_data['ads']

            # Path 2: data.items/vehicles
            elif 'data' in json_data:
                data_obj = json_data['data']
                if isinstance(data_obj, dict):
                    items = (
                        data_obj.get('items') or
                        data_obj.get('vehicles') or
                        data_obj.get('ads') or
                        data_obj.get('results')
                    )

            # Path 3: props.pageProps.items
            elif 'props' in json_data:
                page_props = json_data.get('props', {}).get('pageProps', {})
                if isinstance(page_props, dict):
                    items = (
                        page_props.get('items') or
                        page_props.get('vehicles') or
                        page_props.get('ads') or
                        page_props.get('results')
                    )

            # Path 4: initialData/initialState
            elif 'initialData' in json_data or 'initialState' in json_data:
                initial = json_data.get('initialData') or json_data.get('initialState')
                if isinstance(initial, dict):
                    items = (
                        initial.get('items') or
                        initial.get('vehicles') or
                        initial.get('ads') or
                        initial.get('results')
                    )

            if items and isinstance(items, list):
                listings = []
                for item in items:
                    listing = self._map_json_to_listing(item)
                    if listing:
                        listings.append(listing)
                return listings

            return []

        except Exception as e:
            logger.error(f"Error parsing embedded JSON: {e}")
            return []

    def _map_json_to_listing(self, item: Dict) -> Optional[CarListing]:
        """Map embedded JSON item to CarListing."""
        try:
            # ID
            ad_id = str(
                item.get('id') or
                item.get('ad_id') or
                item.get('adId') or
                item.get('anuncioId') or
                item.get('vehicleId') or
                ''
            )

            if not ad_id:
                return None

            # Title
            title = (
                item.get('title') or
                item.get('nombre') or
                item.get('name') or
                ''
            )

            # URL
            url = (
                item.get('url') or
                item.get('link') or
                item.get('href') or
                ''
            )
            if url and url.startswith('/'):
                url = f'https://www.autocasion.com{url}'

            # Price
            price = None
            price_text = None
            price_obj = item.get('price') or item.get('precio') or item.get('pvp')
            if isinstance(price_obj, dict):
                price = price_obj.get('amount') or price_obj.get('value')
            elif isinstance(price_obj, (int, float)):
                price = int(price_obj)
            elif isinstance(price_obj, str):
                price = self._extract_number(price_obj)
                price_text = price_obj

            # Brand (marca)
            marca = (
                item.get('marca') or
                item.get('brand') or
                item.get('make') or
                ''
            )

            # Model (modelo)
            modelo = (
                item.get('modelo') or
                item.get('model') or
                ''
            )

            # Year
            year = item.get('year') or item.get('año') or item.get('ano')
            if year:
                try:
                    year = int(year) if isinstance(year, (int, float)) else int(re.sub(r'[^\d]', '', str(year))[:4])
                except ValueError:
                    year = None

            # Kilometers
            km = None
            km_raw = item.get('kilometers') or item.get('kilometros') or item.get('km') or item.get('mileage')
            if km_raw:
                if isinstance(km_raw, (int, float)):
                    km = int(km_raw)
                else:
                    km = self._extract_number(str(km_raw))

            # Power
            power = None
            power_raw = item.get('power') or item.get('potencia') or item.get('cv') or item.get('horsepower')
            if power_raw:
                if isinstance(power_raw, (int, float)):
                    power = int(power_raw)
                else:
                    power = self._extract_number(str(power_raw))

            # Fuel
            fuel = (
                item.get('fuel') or
                item.get('combustible') or
                item.get('fuelType') or
                ''
            )

            # Transmission
            transmission = item.get('transmission') or item.get('cambio') or ''

            # Location
            location = None
            location_raw = item.get('location') or item.get('localidad') or item.get('ciudad') or item.get('provincia')
            if isinstance(location_raw, dict):
                location = location_raw.get('name') or location_raw.get('ciudad') or ''
            elif location_raw:
                location = str(location_raw)

            return CarListing(
                ad_id=ad_id,
                source=self.source,
                url=url,
                title=title,
                marca=marca.upper() if marca else None,
                modelo=modelo,
                version=item.get('version') or item.get('trim'),
                year=year,
                kilometers=km,
                fuel=fuel,
                power_cv=power,
                transmission=transmission,
                price=price,
                price_text=price_text,
                location=location,
                raw_data=item
            )

        except Exception as e:
            logger.debug(f"Error mapping JSON item: {e}")
            return None

    # =====================
    # TIER 3: CSS Selectors
    # =====================

    def _extract_from_css(self, soup: BeautifulSoup) -> List[CarListing]:
        """Extract cars using CSS selectors (fallback method)."""
        listings = []

        articles = soup.find_all('article', class_='anuncio')
        if not articles:
            logger.warning("No article.anuncio elements found")
            return []

        logger.info(f"Found {len(articles)} ads via CSS")

        for article in articles:
            try:
                listing = self._parse_article(article)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"Error parsing article: {e}")

        return listings

    def _parse_article(self, article) -> Optional[CarListing]:
        """Parse single article element."""
        ad_id = self._extract_ad_id_from_article(article)

        # Extract link and title
        link_elem = article.find('a', href=True)
        url = None
        title = None

        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('/'):
                href = f'https://www.autocasion.com{href}'
            url = href

            title_elem = (
                link_elem.find('h2', itemprop='name') or
                link_elem.find('h2') or
                link_elem.find('h3', itemprop='name') or
                link_elem.find('h3')
            )
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract ad_id from URL if not found
            if not ad_id and href:
                match = re.search(r'ref(\d+)/?$', href)
                if match:
                    ad_id = match.group(1)

        if not ad_id and not url:
            return None

        # Extract price
        price = None
        price_text = None
        contenido = article.find('div', class_='contenido-anuncio')
        if contenido:
            price_elem = contenido.find('p', class_='precio')
            if price_elem and 'financiado' not in (price_elem.get('class') or []):
                # Remove discount span
                for span in price_elem.find_all(class_=lambda x: x and 'flecha' in str(x).lower()):
                    span.decompose()
                price_text = price_elem.get_text(strip=True)
                # Remove "Al contado" prefix
                price_text = re.sub(r'^Al\s+contado\s*', '', price_text, flags=re.IGNORECASE)
                price = self._extract_number(price_text)

        # Extract attributes
        attrs = {}
        ul = article.find('ul')
        if ul:
            lis = ul.find_all('li')
            for li in lis:
                text = li.get_text(strip=True)
                self._parse_attribute(text, attrs)

            # Last li often is location
            if lis:
                last_item = lis[-1].get_text(strip=True)
                if not any(x in last_item.lower() for x in ['km', 'cv', 'hp', 'diesel', 'gasolina', 'manual', 'automático']):
                    if not re.match(r'^\d{4}$', last_item):
                        attrs['location'] = last_item

        # Extract marca/modelo from title
        marca, modelo = self._extract_marca_modelo(title)

        # Extract power and transmission from title if not found
        if title:
            if not attrs.get('power'):
                power = self._extract_power_from_text(title)
                if power:
                    attrs['power'] = power
            if not attrs.get('transmission'):
                trans = self._extract_transmission_from_text(title)
                if trans:
                    attrs['transmission'] = trans

        return CarListing(
            ad_id=str(ad_id) if ad_id else None,
            source=self.source,
            url=url,
            title=title,
            marca=marca,
            modelo=modelo,
            year=attrs.get('year'),
            kilometers=attrs.get('kilometers'),
            fuel=attrs.get('fuel'),
            power_cv=attrs.get('power'),
            transmission=attrs.get('transmission'),
            price=price,
            price_text=price_text,
            location=attrs.get('location'),
        )

    def _extract_ad_id_from_article(self, article) -> Optional[str]:
        """Extract ad_id from article element."""
        # Try data-product-key
        ad_id = article.get('data-product-key')
        if ad_id:
            return str(ad_id)

        # Try favoritos button
        favoritos = article.find(class_='favoritos')
        if favoritos:
            ad_id = favoritos.get('data-ad')
            if ad_id:
                return str(ad_id)

        # Try other data attributes
        ad_id = article.get('data-id') or article.get('data-ad-id') or article.get('id')
        if ad_id:
            return str(ad_id)

        # Try extracting from URL
        link = article.find('a', href=True)
        if link:
            href = link.get('href', '')
            match = re.search(r'ref(\d+)/?$', href)
            if match:
                return match.group(1)

        return None

    def _parse_attribute(self, text: str, attrs: Dict):
        """Parse attribute text into attrs dict."""
        if not text:
            return

        text_lower = text.lower()

        # Year (4 digits)
        if re.match(r'^\d{4}$', text):
            attrs['year'] = int(text)

        # Kilometers
        elif 'km' in text_lower:
            attrs['kilometers'] = self._extract_number(text)

        # Power
        elif any(x in text_lower for x in ['cv', 'hp', 'kw']):
            power = self._extract_number(text)
            if 'kw' in text_lower and power:
                power = int(power * 1.36)  # Convert kW to CV
            attrs['power'] = power

        # Fuel type
        elif any(f in text_lower for f in ['diésel', 'diesel', 'gasolina', 'gasóleo', 'híbrido', 'hibrido', 'eléctrico', 'electrico', 'glp', 'gnc']):
            attrs['fuel'] = text

        # Transmission
        elif any(t in text_lower for t in ['manual', 'automático', 'automatico', 'automática']):
            attrs['transmission'] = text

    # =====================
    # HELPER METHODS
    # =====================

    def _extract_version(self, nombre: str, marca: str, modelo: str) -> Optional[str]:
        """Extract version from full name."""
        if not nombre:
            return None

        nombre_sin_marca = nombre
        if marca:
            nombre_sin_marca = nombre.replace(marca, '', 1).strip()

        if modelo and modelo in nombre_sin_marca:
            partes = nombre_sin_marca.split(modelo)
            version = partes[-1].strip()
        else:
            version = nombre_sin_marca

        return version if version else None

    def _infer_fuel_type(self, version: str, nombre: str = None) -> Optional[str]:
        """
        Infer fuel type from version/name.

        Patterns:
        - Diesel: BlueHDi, HDi, TDI, dCi, CDTi, CDTI, SDI, JTD, JTDM, CRDi, etc.
        - Gasolina: PureTech, TSI, TFSI, FSI, VTi, GTI, Turbo, TCe, etc.
        - Hibrido: Hybrid, e-Hybrid, PHEV, HEV, eTSI, etc.
        - Electrico: Electric, EV, kWh, e-tron, etc.
        """
        text = (version or '') + ' ' + (nombre or '')
        text_lower = text.lower()

        # Electrico (check first - most specific)
        electric_patterns = [
            'eléctrico', 'electrico', 'electric', ' ev ', 'bev',
            'kwh', 'e-tron', 'id.', 'mach-e'
        ]
        for pattern in electric_patterns:
            if pattern in text_lower:
                return 'Eléctrico'

        # Hibrido (check before diesel/gasolina)
        hybrid_patterns = [
            'hybrid', 'híbrido', 'hibrido', 'phev', 'hev',
            'e-hybrid', 'ehybrid', 'plug-in', 'plugin',
            'etsi', 'e-tsi', 'mhev'
        ]
        for pattern in hybrid_patterns:
            if pattern in text_lower:
                return 'Híbrido'

        # Diesel
        diesel_patterns = [
            'bluehdi', 'hdi', 'tdi', 'dci', 'cdti', 'cdi',
            'sdi', 'jtd', 'jtdm', 'crdi', 'd4d', 'ddis',
            'dtec', 'i-dtec', 'skyactiv-d', 'bluetec',
            'ecoblue', 'tdci', 'duratorq'
        ]
        for pattern in diesel_patterns:
            if pattern in text_lower:
                return 'Diésel'

        # Check for standalone 'd' patterns (e.g., "320d", "520d")
        if re.search(r'\b\d+d\b', text_lower):
            return 'Diésel'

        # Gasolina
        gasoline_patterns = [
            'puretech', 'tsi', 'tfsi', 'fsi', 'gti', 'gdi',
            'vti', 'tgi', 'turbo', 'mpi', 'tce', 'sce',
            'ecoboost', 'skyactiv-g', 'vtec', 'i-vtec',
            't-gdi', 'cvvt', 'mivec', 'multiair'
        ]
        for pattern in gasoline_patterns:
            if pattern in text_lower:
                return 'Gasolina'

        # GLP/GNC (Gas)
        gas_patterns = ['glp', 'gnc', 'cng', 'lpg', 'bifuel', 'bi-fuel']
        for pattern in gas_patterns:
            if pattern in text_lower:
                return 'GLP/GNC'

        return None

    def _extract_marca_modelo(self, title: str) -> tuple:
        """Extract marca and modelo from title."""
        if not title:
            return None, None

        parts = title.strip().split()
        if len(parts) < 2:
            return None, None

        marca = parts[0].upper()

        # Handle compound models (Clase C, Serie 3)
        if len(parts) >= 3 and parts[1].lower() in ['clase', 'serie', 'tipo', 'range', 'discovery', 'grand']:
            modelo = f"{parts[1]} {parts[2]}"
        else:
            modelo = parts[1] if len(parts) > 1 else None

        return marca, modelo

    def _extract_power_from_text(self, text: str) -> Optional[int]:
        """Extract power (CV/HP/kW) from text."""
        if not text:
            return None

        text_lower = text.lower()
        power_match = re.search(r'(\d+)\s*(cv|hp|kw)', text_lower)
        if power_match:
            power_value = int(power_match.group(1))
            unit = power_match.group(2)

            # Convert kW to CV
            if unit == 'kw':
                power_value = int(power_value * 1.36)

            return power_value

        return None

    def _extract_transmission_from_text(self, text: str) -> Optional[str]:
        """Extract transmission (Manual/Automático) from text."""
        if not text:
            return None

        text_lower = text.lower()

        # Automatic patterns (check first)
        automatic_patterns = [
            r'\bautomático\b', r'\bautomatico\b', r'\bautomática\b',
            r'\baut\.\b', r'\bauto\b', r'\b[sd]sg\b',
            r'\btronic\b', r'\bmatic\b', r'\bsteptronic\b',
            r'\bmultitronic\b', r'\bpowershift\b', r'\beasytronic\b'
        ]
        for pattern in automatic_patterns:
            if re.search(pattern, text_lower):
                return "Automático"

        # Manual patterns
        manual_patterns = [
            r'\bmanual\b', r'\bman\.\b',
            r'\b6\s*vel\b', r'\b5\s*vel\b'
        ]
        for pattern in manual_patterns:
            if re.search(pattern, text_lower):
                return "Manual"

        return None
