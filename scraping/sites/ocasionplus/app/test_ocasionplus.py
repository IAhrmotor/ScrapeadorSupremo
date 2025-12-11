"""
Test script for OcasionPlus scraper.

Usage:
    python scraping/sites/ocasionplus/app/test_ocasionplus.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.ocasionplus.app.scraper_agent import OcasionPlusScraperAgent
from scraping.sites.ocasionplus.parser import OcasionPlusParser
from scraping.sites.ocasionplus.site import OcasionPlusSite


def test_url_generation():
    """Test URL generation."""
    print("\n" + "="*60)
    print("TEST: URL Generation")
    print("="*60)

    site = OcasionPlusSite()

    # Default URL
    url = site.get_search_url()
    print(f"\nDefault URL:\n  {url}")

    # Custom year range
    url_2020 = site.get_search_url(year_from=2020, year_to=2024)
    print(f"\n2020-2024 URL:\n  {url_2020}")

    # With brand filter
    url_audi = site.get_url_for_brand("audi", year_from=2018, year_to=2023)
    print(f"\nAudi 2018-2023 URL:\n  {url_audi}")

    print("\n✓ URL generation OK")


def test_parser_with_sample():
    """Test parser with sample HTML."""
    print("\n" + "="*60)
    print("TEST: Parser with Sample HTML")
    print("="*60)

    # Sample HTML from the site
    sample_html = '''
    <div class="cardVehicle_card__LwFCi">
        <a class="cardVehicle_link__l8xYT button" target="_self"
           href="/coches-segunda-mano/cupra-formentor-20-tsi-vz-dsg-con-24228km-2023-vwummqar">
            <div class="cardVehicle_image__fPk_E">
                <img alt="Cupra Formentor" src="https://img.ocasionplus.com/test.jpg">
            </div>
            <div class="cardVehicle_description__Gp9vd">
                <div class="cardVehicle_prices__yMKDU">
                    <h2 class="cardVehicle_column_text__EvQkB">
                        <span class="cardVehicle_spot__e6YZx" data-test="span-brand-model">Cupra Formentor</span>
                        <span class="cardVehicle_finance__SG6JV" data-test="span-version">2.0 TSI VZ DSG (245 CV)</span>
                    </h2>
                    <div class="cardVehicle_column_amount___VgVU">
                        <div class="cardVehicle_amount__JGeQe">
                            <span class="cardVehicle_spot__e6YZx" data-test="span-price">39.990€</span>
                            <span class="cardVehicle_finance__SG6JV" data-test="span-finance">36.355€</span>
                        </div>
                        <div class="cardVehicle_quota__onan1">
                            <span>desde</span>
                            <span class="cardVehicle_cuote__eSQXl" data-test="span-finace-quote">559€</span>
                            <span>/mes</span>
                        </div>
                    </div>
                </div>
                <div class="characteristics_characteristics__ZF6yE">
                    <div class="characteristics_content__vqUuu">
                        <span class="flex-column characteristics_iconEnvironmentalLabel__8vrFb">
                            <img alt="distintivo-ambiental" src="/hera/icons/C.svg">
                        </span>
                        <span class="characteristics_elements__Mb1S_" data-test="span-registration-date">2023</span>
                        <span class="characteristics_elements__Mb1S_" data-test="span-km">24.228 Km</span>
                        <span class="characteristics_elements__Mb1S_" data-test="span-fuel-type">Gasolina</span>
                        <span class="characteristics_elements__Mb1S_" data-test="span-engine-transmission">Automático</span>
                    </div>
                </div>
                <div class="cardVehicle_dealer__41Xs5" data-test="div-dealer">
                    <span class="flex-column cardVehicle_icon__EH9Tp">
                        <img alt="localization" src="/hera/icons/locationFill.svg">
                    </span>Cádiz - Jerez
                </div>
            </div>
        </a>
    </div>
    '''

    parser = OcasionPlusParser()
    listings = parser.parse_listings(sample_html)

    if listings:
        listing = listings[0]
        print(f"\nParsed listing:")
        print(f"  Marca: {listing.marca}")
        print(f"  Modelo: {listing.modelo}")
        print(f"  Version: {listing.version}")
        print(f"  Potencia CV: {listing.potencia_cv}")
        print(f"  Precio contado: {listing.precio_contado}€")
        print(f"  Precio financiado: {listing.precio_financiado}€")
        print(f"  Cuota mensual: {listing.cuota_mensual}€")
        print(f"  Año: {listing.year}")
        print(f"  Kilómetros: {listing.kilometros}")
        print(f"  Combustible: {listing.combustible}")
        print(f"  Transmisión: {listing.transmision}")
        print(f"  Etiqueta: {listing.etiqueta_ambiental}")
        print(f"  Ubicación: {listing.ubicacion}")
        print(f"  URL: {listing.url}")

        # Test to_dict
        data = listing.to_dict()
        print(f"\n  to_dict() keys: {list(data.keys())}")

        print("\n✓ Parser OK")
    else:
        print("\n✗ No listings parsed!")


async def test_scraper_quick(headless: bool = False, max_iterations: int = 3):
    """
    Quick scraper test with limited iterations.

    Args:
        headless: Run browser in headless mode
        max_iterations: Number of scroll iterations
    """
    print("\n" + "="*60)
    print("TEST: Scraper Quick Test")
    print("="*60)

    agent = OcasionPlusScraperAgent(headless=headless)

    result = await agent.scrape_all(
        max_iterations=max_iterations,
        save_to_db=False,  # Don't save during test
        year_from=2020,
        year_to=2024
    )

    print(f"\nResult:")
    print(f"  Total listings: {result.total_listings}")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print(f"  Errors: {result.errors}")

    if result.total_listings > 0:
        print("\n✓ Scraper OK")
    else:
        print("\n⚠ No listings found (may be blocked or need adjustment)")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("OCASIONPLUS SCRAPER TESTS")
    print("="*60)

    # Test 1: URL generation
    test_url_generation()

    # Test 2: Parser
    test_parser_with_sample()

    # Test 3: Quick scraper test (optional, requires Playwright)
    run_scraper_test = input("\n¿Ejecutar test de scraper con Playwright? (s/n): ").lower().strip()
    if run_scraper_test == 's':
        headless = input("¿Modo headless? (s/n): ").lower().strip() == 's'
        asyncio.run(test_scraper_quick(headless=headless))

    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
