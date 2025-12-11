"""Debug why parser returns 0 listings despite having valid JSON."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import re

# Read the HTML saved by HeadlessX
with open('headlessx_debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("="*80)
print("DEBUGGING COCHESNET PARSER")
print("="*80)

# Extract JSON
match = re.search(r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("(.+?)"\)', html, re.DOTALL)

if not match:
    print("ERROR: JSON regex did not match")
    sys.exit(1)

print("[OK] JSON regex matched")

# Decode JSON
json_str = match.group(1).encode().decode('unicode_escape')
data = json.loads(json_str)

print(f"[OK] JSON parsed successfully")
print(f"  Keys: {list(data.keys())}")

# Get items
items = data.get('initialResults', {}).get('items', [])
print(f"[OK] Found {len(items)} items in initialResults")

if not items:
    print("ERROR: No items found")
    sys.exit(1)

# Test mapping first item
item = items[0]
print(f"\n{'='*80}")
print(f"TESTING FIRST ITEM")
print(f"{'='*80}")
print(f"Item ID: {item.get('id')}")
print(f"Item title: {item.get('title')}")
print(f"Item keys: {list(item.keys())}")

# Now test with actual parser
from scraping.sites.cochesnet.parser import CochesNetParser

parser = CochesNetParser()

print(f"\n{'='*80}")
print(f"TESTING WITH PARSER")
print(f"{'='*80}")

# Test _parse_json_items directly
print("\nCalling parser._parse_json_items(data)...")
listings = parser._parse_json_items(data)

print(f"Listings returned: {len(listings)}")

if not listings:
    print("\nERROR: Parser returned 0 listings")
    print("Testing _map_json_to_listing directly...")

    # Test mapping directly
    try:
        listing = parser._map_json_to_listing(item)
        print(f"Direct mapping result: {listing}")

        if listing:
            print(f"  Listing ID: {listing.ad_id}")
            print(f"  Listing title: {listing.title}")
            print(f"  Listing marca: {listing.marca}")
            print(f"  Listing modelo: {listing.modelo}")
        else:
            print("  _map_json_to_listing returned None")

            # Debug why it returned None
            print("\nDebugging fields:")
            print(f"  ad_id: {item.get('id')} (type: {type(item.get('id'))})")
            print(f"  title: {item.get('title')}")
            print(f"  url: {item.get('url')}")
            print(f"  year: {item.get('year')}")
            print(f"  km: {item.get('km')}")

    except Exception as e:
        print(f"ERROR in _map_json_to_listing: {e}")
        import traceback
        traceback.print_exc()

else:
    print(f"\nSUCCESS! Parser returned {len(listings)} listings")
    print(f"\nFirst listing:")
    listing = listings[0]
    print(f"  ID: {listing.ad_id}")
    print(f"  Title: {listing.title}")
    print(f"  Marca: {listing.marca}")
    print(f"  Modelo: {listing.modelo}")
    print(f"  Year: {listing.year}")
    print(f"  Price: {listing.price_text}")

print(f"\n{'='*80}")
print("DEBUG COMPLETED")
print(f"{'='*80}")
