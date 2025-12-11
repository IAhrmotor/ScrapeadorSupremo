"""Final comprehensive test of the Cochesnet parser with real HTML."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.sites.cochesnet.parser import CochesNetParser

# Read saved HTML
with open('cochesnet_debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("Testing CochesNetParser with real HTML...")
print("="*80)

# Create parser
parser = CochesNetParser()

# Parse
listings = parser.parse(html)

print(f"\nTotal listings parsed: {len(listings)}")

if listings:
    print("\n" + "="*80)
    print("SUCCESS - Listings found!")
    print("="*80)

    # Show first 5 listings
    print("\nFirst 5 listings:")
    for i, listing in enumerate(listings[:5], 1):
        print(f"\n[{i}] {listing.title}")
        print(f"    Marca: {listing.marca}")
        print(f"    Modelo: {listing.modelo}")

        if listing.extra_fields:
            version = listing.extra_fields.get('version')
            confidence = listing.extra_fields.get('parsing_confidence', 0)
            method = listing.extra_fields.get('parsing_method', 'unknown')

            print(f"    Version: {version or '(none)'}")
            print(f"    Confidence: {confidence:.2f} ({method.upper()})")

        print(f"    Precio: {listing.price or '(none)'}")
        print(f"    Ano: {listing.year or '(none)'}")
        print(f"    KM: {listing.kilometers or '(none)'}")

    # Statistics
    if all(l.extra_fields for l in listings):
        confidences = [l.extra_fields.get('parsing_confidence', 0) for l in listings]
        avg_conf = sum(confidences) / len(confidences)
        perfect = sum(1 for c in confidences if c == 1.0)

        print("\n" + "="*80)
        print("PARSING STATISTICS")
        print("="*80)
        print(f"Average confidence: {avg_conf:.2f}")
        print(f"Perfect matches (1.0): {perfect}/{len(listings)} ({perfect/len(listings)*100:.1f}%)")

else:
    print("\n" + "="*80)
    print("ERROR - No listings found")
    print("="*80)
    print("\nDebugging...")

    # Manual test
    from bs4 import BeautifulSoup
    import re
    import json

    soup = BeautifulSoup(html, 'lxml')
    scripts = soup.find_all('script')

    print(f"Total <script> tags: {len(scripts)}")

    for i, script in enumerate(scripts):
        text = script.string
        if text and '__INITIAL_PROPS__' in text:
            print(f"\nFound __INITIAL_PROPS__ in script #{i+1}")

            # Try regex
            match = re.search(r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("(.+?)"\)', text, re.DOTALL)

            if match:
                print("Regex matched!")
                try:
                    json_str = match.group(1).encode().decode('unicode_escape')
                    data = json.loads(json_str)
                    print(f"JSON parsed, keys: {list(data.keys())[:10]}")

                    # Check for items
                    if 'initialResults' in data:
                        items = data['initialResults'].get('items', [])
                        print(f"Found {len(items)} items in initialResults")

                        if items:
                            print(f"\nFirst item keys: {list(items[0].keys())[:15]}")
                            print(f"First item title: {items[0].get('title', 'NO TITLE')}")
                            print(f"First item id: {items[0].get('id', 'NO ID')}")

                except Exception as e:
                    print(f"Error processing JSON: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("Regex did NOT match")
                print(f"Text starts with: {text[:200]}")
