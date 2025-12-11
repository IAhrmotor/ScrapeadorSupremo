"""Test Cochesnet scraping with Selenium."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scraping.sites.cochesnet.parser import CochesNetParser

# Configure headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

print("="*80)
print("TESTING COCHESNET WITH SELENIUM")
print("="*80)

# Test URL
url = "https://www.coches.net/citroen/segunda-mano/2025/"

print(f"\nURL: {url}")
print("Initializing Chrome driver (headless)...")

driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)

    print("Navigating to URL...")
    driver.get(url)

    print("Waiting for page to load...")
    import time
    time.sleep(3)  # Wait for JavaScript to execute

    # Get HTML
    html = driver.page_source
    print(f"HTML size: {len(html):,} bytes")

    # Check for JSON
    has_json = "__INITIAL_PROPS__" in html
    print(f"Has __INITIAL_PROPS__: {has_json}")

    # Parse
    parser = CochesNetParser()
    listings = parser.parse(html)

    print(f"\nListings found: {len(listings)}")

    if listings:
        print("\nFirst 5 listings:")
        for i, listing in enumerate(listings[:5], 1):
            print(f"{i}. {listing.marca} {listing.modelo} ({listing.year}) - {listing.price_text}")
            if listing.extra_fields:
                conf = listing.extra_fields.get('parsing_confidence', 0)
                print(f"   Confidence: {conf:.2f}")
    else:
        print("\nNo listings found - saving HTML for debugging")
        with open('selenium_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved to: selenium_debug.html")

        # Show snippet
        print(f"\nHTML snippet:\n{html[:500]}")

    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    if driver:
        driver.quit()
        print("\nDriver closed")
