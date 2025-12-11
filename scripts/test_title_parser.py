"""
Test script for TitleParser with real Cochesnet title examples.

This script tests the TitleParser with various title patterns from Cochesnet
to verify parsing accuracy and confidence scoring.

Usage:
    python scripts/test_title_parser.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.base.title_parser import get_title_parser
from scraping.storage.supabase_client import get_supabase_client


# Real title examples from Cochesnet
TEST_TITLES = [
    # Common brands - should have high confidence (DB match)
    "OPEL Corsa 1.5D DT 74kW 100CV Edition 5p.",
    "BMW Serie 3 320d 140 kW (190 CV)",
    "Mercedes-Benz Clase A A 200 CDI",
    "SEAT Leon 1.4 TSI 110kW 150CV StSp Style",
    "Volkswagen Golf 2.0 TDI 110kW 150CV DSG",
    "Audi A4 2.0 TDI 110kW 150CV Advanced edition",
    "Renault Clio 1.5 dCi Energy Zen 90",
    "Peugeot 308 1.6 BlueHDi 88kW 120CV Active",

    # Edge cases
    "Tesla Model 3 Long Range AWD",
    "Mini Cooper S 1.6 192cv",

    # Potential parsing challenges
    "Ford Focus 1.0 EcoBoost 92kW 125CV STLine 5p",
    "Nissan Qashqai 1.5dCi Acenta 4x2",

    # Hyphenated brands
    "Mercedes-Benz GLC 220 d 4MATIC",
    "Land Rover Range Rover Evoque 2.0D 150CV SE Dynamic",
]


def print_separator():
    print("=" * 80)


def test_parser():
    """Test TitleParser with example titles."""
    print_separator()
    print("TITLE PARSER TEST - Cochesnet")
    print_separator()

    # Initialize parser
    print("\nInitializing TitleParser...")
    try:
        client = get_supabase_client()
        parser = get_title_parser(client)
        print("Parser initialized with Supabase client")
    except Exception as e:
        print(f"Warning: Failed to initialize with DB: {e}")
        parser = get_title_parser()
        print("Parser initialized with fallback mode only")

    print(f"\nTesting {len(TEST_TITLES)} titles...\n")

    # Test each title
    results = []
    for i, title in enumerate(TEST_TITLES, 1):
        print(f"\n[{i}/{len(TEST_TITLES)}] Testing:")
        print(f"  Title: {title}")

        parsed = parser.parse(title)

        print(f"  Marca: {parsed.marca or '(none)'}")
        print(f"  Modelo: {parsed.modelo or '(none)'}")
        print(f"  Version: {parsed.version or '(none)'}")
        print(f"  Confidence: {parsed.confidence:.2f}")

        # More detailed method classification
        if parsed.confidence == 1.0:
            method = "DB_EXACT"
        elif parsed.confidence >= 0.7:
            method = "DB_MARCA_ONLY"
        else:
            method = "HEURISTIC"

        print(f"  Method: {method}")

        results.append({
            'title': title,
            'parsed': parsed
        })

    # Summary statistics
    print_separator()
    print("SUMMARY STATISTICS")
    print_separator()

    total = len(results)
    db_matches = sum(1 for r in results if r['parsed'].confidence >= 0.7)
    heuristic = total - db_matches

    avg_confidence = sum(r['parsed'].confidence for r in results) / total

    print(f"\nTotal titles tested: {total}")
    print(f"Database matches (confidence >= 0.7): {db_matches} ({db_matches/total*100:.1f}%)")
    print(f"Heuristic fallback: {heuristic} ({heuristic/total*100:.1f}%)")
    print(f"Average confidence: {avg_confidence:.2f}")

    # Show low confidence titles
    low_confidence = [r for r in results if r['parsed'].confidence < 0.7]
    if low_confidence:
        print(f"\nLow confidence titles ({len(low_confidence)}):")
        for r in low_confidence:
            print(f"  - [{r['parsed'].confidence:.2f}] {r['title']}")
            print(f"    Parsed as: {r['parsed'].marca} / {r['parsed'].modelo}")

    # Show successful DB matches
    high_confidence = [r for r in results if r['parsed'].confidence >= 0.7]
    if high_confidence:
        print(f"\nSuccessful DB matches ({len(high_confidence)}):")
        for r in high_confidence:
            print(f"  - [{r['parsed'].confidence:.2f}] {r['parsed'].marca} {r['parsed'].modelo}")

    print("\nTest completed!")


if __name__ == "__main__":
    test_parser()
