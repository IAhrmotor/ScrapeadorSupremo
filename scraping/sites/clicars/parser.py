"""Clicars.com HTML parser for car listings."""

import re
import logging
from typing import List, Optional
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scraping.base.parser import CarListing

logger = logging.getLogger(__name__)


class ClicarsParser:
    """Parser for Clicars.com HTML pages."""

    def parse(self, html: str) -> List[CarListing]:
        """
        Parse all car listings from HTML.

        Args:
            html: HTML content from Clicars page

        Returns:
            List of CarListing objects
        """
        soup = BeautifulSoup(html, 'lxml')
        listings = []

        # Find all car cards - <a> tags with data-vehicle-web-id attribute
        car_cards = soup.find_all('a', attrs={'data-vehicle-web-id': True})

        logger.info(f"Found {len(car_cards)} car cards in HTML")

        for card in car_cards:
            try:
                listing = self._parse_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"Error parsing card: {e}")
                continue

        logger.info(f"Parsed {len(listings)} listings from Clicars")
        return listings

    def _parse_card(self, card) -> Optional[CarListing]:
        """Parse a single car card."""
        try:
            # Extract ad_id from data-vehicle-web-id
            ad_id = card.get('data-vehicle-web-id')
            if not ad_id:
                return None

            # Extract URL
            url = card.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.clicars.com{url}"

            # Extract brand from data-analytics-vehicle-maker
            marca = card.get('data-analytics-vehicle-maker')

            # Extract model from data-analytics-vehicle-model
            modelo = card.get('data-analytics-vehicle-model')

            # Extract title from <h2> with class "maker"
            title_h2 = card.find('h2', class_='maker')
            if title_h2:
                strong_tag = title_h2.find('strong')
                version_span = title_h2.find('span', class_='version')

                marca_title = strong_tag.get_text(strip=True) if strong_tag else None
                version = version_span.get_text(strip=True) if version_span else None

                # Override marca/modelo if found in title
                if marca_title and not marca:
                    parts = marca_title.split()
                    if len(parts) >= 2:
                        marca = parts[0]
                        modelo = parts[1]
                    elif len(parts) == 1:
                        marca = parts[0]

                # Build full title
                title = f"{marca_title} {version}" if version else marca_title
            else:
                title = None
                version = None

            # Extract specs from span with class "info"
            year = None
            kilometers = None
            power_cv = None
            transmission = None

            info_span = card.find('span', class_='info')
            if info_span:
                info_text = info_span.get_text(strip=True)
                year, kilometers, power_cv, transmission = self._extract_specs(info_text)

            # Extract price from trigger-modal-price div
            price = None
            price_div = card.find('div', class_='trigger-modal-price')
            if price_div:
                # Try data-price-web first
                price_str = price_div.get('data-price-web')
                if price_str:
                    price = self._clean_price(price_str)

                # If not found, try to find the strong price
                if not price and price_div.parent:
                    strong_price = price_div.parent.find('strong')
                    if strong_price:
                        price = self._clean_price(strong_price.get_text())

            # Extract fuel type from fuelName span
            fuel = None
            fuel_span = card.find('span', class_='fuelName')
            if fuel_span:
                fuel = fuel_span.get_text(strip=True)

            # Extract image
            img = card.find('img', class_='vehicle-img')
            image_url = img.get('src') if img else None

            return CarListing(
                ad_id=ad_id,
                source="clicars",
                url=url,
                marca=marca,
                modelo=modelo,
                version=version,
                title=title,
                year=year,
                kilometers=kilometers,
                fuel=fuel,
                power_cv=power_cv,
                transmission=transmission,
                price=price,
                price_text=None,
                location=None,
                provincia=None,
                raw_data={
                    "image_url": image_url,
                    "position": card.get('data-analytics-vehicle-position'),
                    "published": card.get('data-analytics-vehicle-web-published')
                }
            )

        except Exception as e:
            logger.debug(f"Error parsing card details: {e}")
            return None

    def _extract_brand_model(self, title: str) -> tuple[Optional[str], Optional[str]]:
        """Extract brand and model from title."""
        parts = title.split()
        if len(parts) >= 2:
            marca = parts[0].strip()
            modelo = parts[1].strip()
            return marca, modelo
        elif len(parts) == 1:
            return parts[0].strip(), None
        return None, None

    def _extract_specs(self, text: str) -> tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
        """
        Extract specifications from text: year, km, HP, transmission.

        Example: "2020 | 74.543km | 130CV | Manual"
        """
        year = None
        kilometers = None
        power_cv = None
        transmission = None

        # Split by pipe
        parts = text.split('|')

        for part in parts:
            part_clean = part.strip()

            # Year (4 digits)
            if re.match(r'^\d{4}$', part_clean):
                try:
                    year = int(part_clean)
                except:
                    pass

            # Kilometers
            if 'km' in part_clean.lower():
                km_match = re.search(r'([\d\.]+)\s*km', part_clean, re.IGNORECASE)
                if km_match:
                    try:
                        km_str = km_match.group(1).replace('.', '').replace(',', '')
                        kilometers = int(km_str)
                    except:
                        pass

            # Power (CV)
            if 'cv' in part_clean.lower():
                cv_match = re.search(r'(\d+)\s*cv', part_clean, re.IGNORECASE)
                if cv_match:
                    try:
                        power_cv = int(cv_match.group(1))
                    except:
                        pass

            # Transmission
            if 'manual' in part_clean.lower():
                transmission = "Manual"
            elif 'automático' in part_clean.lower() or 'automatico' in part_clean.lower():
                transmission = "Automático"

        return year, kilometers, power_cv, transmission

    def _clean_price(self, price_str: str) -> Optional[int]:
        """Clean and convert price string to integer."""
        if not price_str:
            return None

        # Remove € symbol and dots/commas
        clean = price_str.replace('€', '').replace('.', '').replace(',', '').strip()

        try:
            return int(clean)
        except:
            return None

    def _extract_price(self, card) -> Optional[int]:
        """Extract price from card."""
        text = card.get_text()

        # Look for price patterns: 13.190€ or 13190€
        price_matches = re.findall(r'([\d\.]+)€', text)

        if price_matches:
            # Get the last price (usually the discounted/final price)
            return self._clean_price(price_matches[-1])

        return None

    def get_total_count(self, html: str) -> Optional[int]:
        """Get total number of available cars."""
        soup = BeautifulSoup(html, 'lxml')

        # Look for text like "2329 Coches"
        text = soup.get_text()
        match = re.search(r'(\d+)\s*coches', text, re.IGNORECASE)

        if match:
            try:
                return int(match.group(1))
            except:
                pass

        return None

    def has_load_more_button(self, html: str) -> bool:
        """Check if 'Ver más' button is present."""
        soup = BeautifulSoup(html, 'lxml')

        # Look for button with "Ver más" text
        buttons = soup.find_all('button')
        for button in buttons:
            if 'ver más' in button.get_text().lower() or 'ver mas' in button.get_text().lower():
                return True

        return False
