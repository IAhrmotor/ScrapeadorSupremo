"""Check what's actually in the parser cache."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.base.title_parser import get_title_parser
from scraping.storage.supabase_client import get_supabase_client


def main():
    print("Checking parser cache...")

    client = get_supabase_client()
    parser = get_title_parser(client, force_reload=True)

    print(f"\nTotal marcas in _marcas_normalized: {len(parser._marcas_normalized)}")
    print(f"Total marcas in _marca_modelos_cache: {len(parser._marca_modelos_cache)}")

    print("\n\nAll marcas in _marcas_normalized:")
    for i, (marca_norm, marca_orig) in enumerate(parser._marcas_normalized, 1):
        print(f"  {i}. '{marca_orig}' (normalized: '{marca_norm}')")

    print("\n\nAll marcas in _marca_modelos_cache:")
    for i, (marca_norm, modelos) in enumerate(parser._marca_modelos_cache.items(), 1):
        print(f"  {i}. '{marca_norm}' - {len(modelos)} modelos")

    # Check for specific marcas
    print("\n\nSearching for specific marcas:")

    search_marcas = ["BMW", "Volkswagen", "Audi", "Renault", "SEAT", "OPEL"]

    for search_marca in search_marcas:
        marca_norm = parser._normalize(search_marca)
        found_in_normalized = any(m[0] == marca_norm for m in parser._marcas_normalized)
        found_in_cache = marca_norm in parser._marca_modelos_cache

        print(f"  {search_marca} (normalized: '{marca_norm}')")
        print(f"    In _marcas_normalized: {found_in_normalized}")
        print(f"    In _marca_modelos_cache: {found_in_cache}")


if __name__ == "__main__":
    main()
