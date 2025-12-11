"""Test script for Clicars scraper."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.clicars.app.scraper_agent import ClicarsScraperAgent
from scraping.sites.clicars.parser import ClicarsParser
from scraping.sites.clicars.site import ClicarsSite


async def test_scraper():
    """Test Clicars scraper with Playwright."""
    print("\n" + "="*60)
    print("CLICARS SCRAPER TEST WITH PLAYWRIGHT")
    print("="*60)

    agent = ClicarsScraperAgent(headless=True)

    print("\nTesting Playwright infinite scroll scraping...")
    print("This will click the 'Ver más' button multiple times to load all cars")

    # Test with limited iterations first (5 clicks = ~60-70 cars)
    result = await agent.scrape_all(
        max_iterations=5,  # Start with 5 iterations for testing
        save_to_db=True
    )

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total listings: {result.total_listings}")
    print(f"Saved to DB: {result.saved_to_db}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Method: {result.method_used}")

    if result.errors:
        print(f"\nErrors: {len(result.errors)}")
        for error in result.errors[:5]:
            print(f"  - {error}")

    # Show sample listings
    if result.total_listings > 0:
        print("\n" + "="*60)
        print("DATABASE STATS")
        print("="*60)
        stats = agent.get_stats()
        print(f"Total Clicars listings in DB: {stats.get('total_listings', 0)}")
        print(f"Scraping pattern: {stats.get('scraping_pattern', 'unknown')}")

    agent.close()


async def test_parser_only():
    """Test parser with sample HTML."""
    print("\n" + "="*60)
    print("CLICARS PARSER TEST")
    print("="*60)

    # Sample HTML with a car card
    sample_html = """
    <a data-vehicle-web-id="121906"
       data-analytics-vehicle-maker="Audi"
       data-analytics-vehicle-model="A3"
       href="/coches-segunda-mano-ocasion/comprar-audi-a3-sportback">
      <h2 class="maker">
        <strong>Audi A3</strong>
        <span class="version">Sportback 30 TFSI S tronic</span>
      </h2>
      <span class="info">2021 | 119.763km | 110CV | Automático</span>
      <div class="trigger-modal-price" data-price-web="23490€"></div>
      <span class="fuelName">Mild hybrid</span>
      <img class="vehicle-img" src="https://example.com/image.jpg">
    </a>
    """

    parser = ClicarsParser()
    listings = parser.parse(sample_html)

    print(f"\nFound {len(listings)} listings")

    if listings:
        listing = listings[0]
        print("\nParsed listing:")
        print(f"  ad_id: {listing.ad_id}")
        print(f"  marca: {listing.marca}")
        print(f"  modelo: {listing.modelo}")
        print(f"  version: {listing.version}")
        print(f"  title: {listing.title}")
        print(f"  year: {listing.year}")
        print(f"  kilometers: {listing.kilometers}")
        print(f"  power_cv: {listing.power_cv}")
        print(f"  transmission: {listing.transmission}")
        print(f"  fuel: {listing.fuel}")
        print(f"  price: {listing.price}")


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Clicars scraper")
    parser.add_argument(
        "--parser-only",
        action="store_true",
        help="Test parser only (no HeadlessX required)"
    )

    args = parser.parse_args()

    if args.parser_only:
        await test_parser_only()
    else:
        await test_scraper()


if __name__ == "__main__":
    asyncio.run(main())
