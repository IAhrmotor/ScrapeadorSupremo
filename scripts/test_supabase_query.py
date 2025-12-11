"""Test Supabase query to see how many rows it returns."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.storage.supabase_client import get_supabase_client


def main():
    print("Testing Supabase query...")

    client = get_supabase_client()

    # Same query as in title_parser.py
    result = client.client.table('marcas_modelos_validos').select('marca, modelo').execute()

    print(f"\nTotal rows returned: {len(result.data)}")
    print(f"Result count attribute: {result.count}")

    # Count unique marcas
    marcas = set(row['marca'] for row in result.data)
    print(f"Unique marcas: {len(marcas)}")

    print("\nFirst 20 rows:")
    for i, row in enumerate(result.data[:20], 1):
        print(f"  {i}. {row['marca']} / {row['modelo']}")

    print("\n\nUnique marcas found:")
    for marca in sorted(marcas):
        print(f"  - {marca}")

    # Check if BMW exists
    print("\n\nSearching for BMW specifically:")
    bmw_result = client.client.table('marcas_modelos_validos').select('*').eq('marca', 'BMW').execute()
    print(f"BMW records found: {len(bmw_result.data)}")

    if bmw_result.data:
        print("Sample BMW models:")
        for row in bmw_result.data[:5]:
            print(f"  - {row['marca']} / {row['modelo']}")


if __name__ == "__main__":
    main()
