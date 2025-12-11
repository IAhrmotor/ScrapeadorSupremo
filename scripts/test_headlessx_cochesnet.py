"""Test Cochesnet scraping with HeadlessX."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import requests
from scraping.sites.cochesnet.parser import CochesNetParser

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Get HeadlessX config
api_url = os.getenv('HEADLESSX_URL', 'http://localhost:3000')
auth_token = os.getenv('HEADLESSX_TOKEN') or os.getenv('HEADLESSX_AUTH_TOKEN')

print("="*80)
print("TESTING COCHESNET WITH HEADLESSX")
print("="*80)
print(f"API URL: {api_url}")
print(f"Auth token: {'configured' if auth_token else 'MISSING'}")

if not auth_token:
    print("\nERROR: HEADLESSX_TOKEN not found in .env")
    sys.exit(1)

# Test URL
url = "https://www.coches.net/citroen/segunda-mano/2025/"

print(f"\nURL: {url}")
print("Sending request to HeadlessX API...")

try:
    # Prepare API request
    api_endpoint = f"{api_url}/api/render"

    payload = {
        "url": url,
        "timeout": 180000,
        "waitUntil": "networkidle",
        "returnPartialOnTimeout": True,
        "deviceProfile": "mid-range-desktop",
        "geoProfile": "us-east",
        "behaviorProfile": "natural",
        "enableCanvasSpoofing": True,
        "enableWebGLSpoofing": True,
        "enableAudioSpoofing": True,
        "enableWebRTCBlocking": True,
        "enableAdvancedStealth": True,
        "simulateMouseMovement": True,
        "simulateScrolling": True,
        "humanDelays": True,
        "randomizeTimings": True,
        "waitForNetworkIdle": True,
        "captureConsole": False
    }

    params = {"token": auth_token}

    response = requests.post(
        api_endpoint,
        params=params,
        json=payload,
        timeout=200
    )

    print(f"Response status: {response.status_code}")

    response.raise_for_status()

    # Parse response
    data = response.json()
    html = data.get("html", "")

    print(f"HTML size: {len(html):,} bytes")
    print(f"Has __INITIAL_PROPS__: {'__INITIAL_PROPS__' in html}")

    # Parse with Cochesnet parser
    parser = CochesNetParser()
    listings = parser.parse(html)

    print(f"\nListings found: {len(listings)}")

    if listings:
        print("\nFirst 5 listings:")
        for i, listing in enumerate(listings[:5], 1):
            print(f"{i}. {listing.marca} {listing.modelo} ({listing.year}) - {listing.price_text}")
            if listing.extra_fields:
                conf = listing.extra_fields.get('parsing_confidence', 0)
                method = listing.extra_fields.get('parsing_method', 'unknown')
                print(f"   Confidence: {conf:.2f} ({method})")

        # Statistics
        confidences = [l.extra_fields.get('parsing_confidence', 0) for l in listings if l.extra_fields]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            perfect = sum(1 for c in confidences if c == 1.0)
            print(f"\nParsing stats:")
            print(f"  Average confidence: {avg_conf:.2f}")
            print(f"  Perfect matches: {perfect}/{len(listings)} ({perfect/len(listings)*100:.1f}%)")

    else:
        print("\nNo listings found - saving HTML for debugging")
        with open('headlessx_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved to: headlessx_debug.html")
        print(f"\nHTML snippet:\n{html[:500]}")

    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)

except requests.RequestException as e:
    print(f"\nERROR: HeadlessX API request failed: {e}")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
