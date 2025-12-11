"""Test Cochesnet URL structure to verify correct endpoint."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from scraping.sites.cochesnet.parser import CochesNetParser

# Test different URL patterns
urls_to_test = [
    "https://www.coches.net/coches-segunda-mano/?year=2023",
    "https://www.coches.net/coches-segunda-mano/?year=2023&pg=1",
    "https://www.coches.net/segunda-mano/2023/",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

parser = CochesNetParser()

for url in urls_to_test:
    print(f"\n{'='*80}")
    print(f"Testing URL: {url}")
    print('='*80)

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"HTML size: {len(response.text):,} bytes")

        # Parse
        listings = parser.parse(response.text)
        print(f"Listings found: {len(listings)}")

        if listings:
            print(f"\nFirst listing:")
            listing = listings[0]
            print(f"  Title: {listing.title}")
            print(f"  Marca: {listing.marca}")
            print(f"  Modelo: {listing.modelo}")
            print(f"  Year: {listing.year}")
            print(f"  Price: {listing.price}")
            print(f"  URL: {listing.url}")

            if listing.extra_fields:
                conf = listing.extra_fields.get('parsing_confidence', 0)
                method = listing.extra_fields.get('parsing_method', 'unknown')
                print(f"  Confidence: {conf:.2f} ({method})")

    except Exception as e:
        print(f"ERROR: {e}")

print(f"\n{'='*80}")
print("Test completed")
print('='*80)
