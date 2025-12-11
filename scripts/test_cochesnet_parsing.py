"""
Test real scraping y parsing de Cochesnet.

Este script scrapea una página real de Cochesnet y muestra
cómo se parsean los anuncios con el sistema optimizado.

Usage:
    python scripts/test_cochesnet_parsing.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from scraping.sites.cochesnet.parser import CochesNetParser


def test_cochesnet_real():
    """Test parsing with real Cochesnet page."""

    print("="*80)
    print("TEST REAL - COCHESNET PARSING")
    print("="*80)

    # URL de listado real con anuncios (página 2 para asegurar resultados)
    url = "https://www.coches.net/citroen/segunda-mano/2025/?pg=2"

    print(f"\nScraping: {url}")
    print("Fetching HTML...")

    try:
        # Fetch page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        html = response.text
        print(f"HTML fetched: {len(html):,} bytes")

        # Parse
        print("\nInitializing CochesNetParser...")
        parser = CochesNetParser()

        print("Parsing listings...")
        listings = parser.parse(html)

        print(f"\nTotal listings parsed: {len(listings)}")

        if not listings:
            print("\nNo listings found. Page might require JavaScript or has changed structure.")
            print("Saving HTML for inspection...")
            with open('cochesnet_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("Saved to: cochesnet_debug.html")
            return

        # Statistics
        print("\n" + "="*80)
        print("PARSING STATISTICS")
        print("="*80)

        confidences = [l.extra_fields.get('parsing_confidence', 0) for l in listings if l.extra_fields]
        methods = [l.extra_fields.get('parsing_method', 'unknown') for l in listings if l.extra_fields]

        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            perfect_matches = sum(1 for c in confidences if c == 1.0)
            db_matches = sum(1 for c in confidences if c >= 0.7)

            print(f"\nTotal anuncios: {len(listings)}")
            print(f"Confidence promedio: {avg_confidence:.2f}")
            print(f"Perfect DB matches (1.0): {perfect_matches} ({perfect_matches/len(listings)*100:.1f}%)")
            print(f"DB matches (>=0.7): {db_matches} ({db_matches/len(listings)*100:.1f}%)")
            print(f"Heuristic fallback: {len(listings)-db_matches} ({(len(listings)-db_matches)/len(listings)*100:.1f}%)")

        # Show first 10 listings
        print("\n" + "="*80)
        print("PRIMEROS 10 ANUNCIOS PARSEADOS")
        print("="*80)

        for i, listing in enumerate(listings[:10], 1):
            print(f"\n[{i}] {listing.title}")
            print(f"    Marca: {listing.marca or '(none)'}")
            print(f"    Modelo: {listing.modelo or '(none)'}")

            if listing.extra_fields:
                version = listing.extra_fields.get('version')
                confidence = listing.extra_fields.get('parsing_confidence', 0)
                method = listing.extra_fields.get('parsing_method', 'unknown')

                print(f"    Version: {version or '(none)'}")
                print(f"    Confidence: {confidence:.2f} ({method.upper()})")

            print(f"    Precio: {listing.price_text or listing.price or '(none)'}")
            print(f"    Año: {listing.year or '(none)'}")
            print(f"    KM: {listing.kilometers or '(none)'}")
            print(f"    Combustible: {listing.fuel or '(none)'}")
            print(f"    URL: {listing.url or '(none)'}")

        # Group by marca
        print("\n" + "="*80)
        print("ANUNCIOS POR MARCA")
        print("="*80)

        marca_counts = {}
        for listing in listings:
            if listing.marca:
                marca_counts[listing.marca] = marca_counts.get(listing.marca, 0) + 1

        print(f"\nTotal marcas únicas: {len(marca_counts)}")
        print("\nTop 10 marcas:")

        for i, (marca, count) in enumerate(sorted(marca_counts.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            print(f"  {i}. {marca}: {count} anuncios")

        # Show low confidence samples
        low_confidence = [l for l in listings if l.extra_fields and l.extra_fields.get('parsing_confidence', 1) < 0.7]

        if low_confidence:
            print("\n" + "="*80)
            print(f"ANUNCIOS CON BAJA CONFIDENCE ({len(low_confidence)})")
            print("="*80)

            for listing in low_confidence[:5]:
                confidence = listing.extra_fields.get('parsing_confidence', 0)
                print(f"\n  [{confidence:.2f}] {listing.title}")
                print(f"      Parseado como: {listing.marca} / {listing.modelo}")

        print("\n" + "="*80)
        print("TEST COMPLETADO")
        print("="*80)

    except requests.exceptions.RequestException as e:
        print(f"\nError fetching page: {e}")
        print("\nTrying alternative URL...")

        # Try alternative URL
        url2 = "https://www.coches.net/coches-segunda-mano/"
        print(f"Trying: {url2}")

        try:
            response = requests.get(url2, headers=headers, timeout=30)
            response.raise_for_status()
            print(f"Success! Got {len(response.text):,} bytes")
            print("(Re-run with this URL for full test)")
        except Exception as e2:
            print(f"Also failed: {e2}")

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_cochesnet_real()
