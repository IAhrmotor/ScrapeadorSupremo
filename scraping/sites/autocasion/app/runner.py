"""CLI runner for Autocasion scraper with HeadlessX integration."""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.autocasion.app.scraper_agent import AutocasionScraperAgent
from scraping.sites.autocasion.app.headlessx_client import get_headlessx_client


class AutocasionRunner:
    """
    Command-line runner for Autocasion scraping operations.

    Provides commands for:
    - scrape: Scrape specific brands or from objetivos
    - status: Show current database statistics
    - brands: List available brands
    - export: Export data to JSON/CSV
    """

    def __init__(self):
        self.agent = AutocasionScraperAgent()

    def run_scrape(
        self,
        marcas: Optional[List[str]] = None,
        max_pages: int = 5,
        from_objetivos: bool = False,
        stealth: bool = False
    ):
        """Run scraping operation."""
        async def _scrape():
            all_pages_mode = (max_pages == 0)

            if from_objetivos:
                print("\n" + "=" * 60)
                print("SCRAPING FROM OBJETIVOS")
                if all_pages_mode:
                    print("MODE: ALL PAGES (auto-detect)")
                print("=" * 60)
                results = await self.agent.scrape_from_objetivos(max_pages=max_pages, stealth=stealth)
            elif marcas:
                print("\n" + "=" * 60)
                print(f"SCRAPING {len(marcas)} BRANDS")
                if all_pages_mode:
                    print("MODE: ALL PAGES (auto-detect)")
                if stealth:
                    print("MODE: STEALTH (maximum anti-detection)")
                print("=" * 60)
                results = await self.agent.scrape_batch(marcas, max_pages, stealth=stealth)
            else:
                print("Error: Specify --marcas or --objetivos")
                return

            # Summary
            print("\n" + "=" * 60)
            print("RESULTS SUMMARY")
            print("=" * 60)
            total_listings = 0
            total_saved = 0
            total_errors = 0

            for r in results:
                status = "OK" if not r.errors else "ERRORS"
                print(f"  {r.marca}: {r.total_listings} listings, "
                      f"{r.pages_scraped} pages, {r.duration_seconds:.1f}s [{status}]")
                total_listings += r.total_listings
                total_saved += r.saved_to_db
                total_errors += len(r.errors)

            print("-" * 60)
            print(f"  TOTAL: {total_listings} listings, {total_saved} saved, {total_errors} errors")

        asyncio.run(_scrape())

    def run_status(self):
        """Show current statistics."""
        print("\n" + "=" * 60)
        print("AUTOCASION SCRAPER STATUS")
        print("=" * 60)

        stats = self.agent.get_stats()

        print(f"\n  Total listings in DB: {stats['total_listings']}")
        print(f"  Total objetivos: {stats['total_objetivos']}")
        print(f"  Available brands: {stats['brands_available']}")
        print(f"  HeadlessX: {stats.get('headlessx_status', 'unknown')}")

        # Get detailed objetivo info
        try:
            objetivos = self.agent.supabase.get_objetivos("autocasion", limit=50)
            if objetivos:
                print("\n  Recent objetivos:")
                for obj in objetivos[:10]:
                    marca = obj.get("marca", "?")
                    attempts = obj.get("scraping_attempts", 0)
                    status = obj.get("last_status", "pending")
                    print(f"    - {marca}: {attempts} attempts, status={status}")
        except Exception as e:
            print(f"  Error getting objetivos: {e}")

    def run_brands(self):
        """List available brands."""
        print("\n" + "=" * 60)
        print("AVAILABLE BRANDS")
        print("=" * 60)

        brands = self.agent.site.get_brands_list()
        for i, brand in enumerate(brands, 1):
            print(f"  {i:2}. {brand}")

        print(f"\n  Total: {len(brands)} brands")

    def run_export(self, output_file: str, format: str = "json"):
        """Export data to file."""
        print(f"\nExporting to {output_file} ({format} format)...")

        try:
            # Fetch data from Supabase
            client = self.agent.supabase
            result = client.client.table("autocasion").select("*").execute()

            if not result.data:
                print("No data to export")
                return

            data = result.data

            if format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            elif format == "csv":
                import csv
                if data:
                    with open(output_file, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)

            print(f"Exported {len(data)} records to {output_file}")

        except Exception as e:
            print(f"Export error: {e}")

    def close(self):
        """Clean up resources."""
        self.agent.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autocasion.com Scraper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py scrape --marcas audi bmw --pages 3
  python runner.py scrape --marcas audi --all-pages      # Scrape ALL pages
  python runner.py scrape --objetivos
  python runner.py status
  python runner.py brands
  python runner.py export output.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape car listings")
    scrape_parser.add_argument(
        "--marcas", "-m", nargs="+",
        help="Brands to scrape (e.g., audi bmw mercedes)"
    )
    scrape_parser.add_argument(
        "--objetivos", "-o", action="store_true",
        help="Scrape from objetivo_autocasion table"
    )
    scrape_parser.add_argument(
        "--pages", "-p", type=int, default=5,
        help="Max pages per brand (default: 5)"
    )
    scrape_parser.add_argument(
        "--all-pages", "-a", action="store_true",
        help="Scrape ALL pages (auto-detect total pages)"
    )
    scrape_parser.add_argument(
        "--stealth", "-s", action="store_true",
        help="Use maximum stealth mode (for heavily protected sites)"
    )

    # Status command
    subparsers.add_parser("status", help="Show scraping statistics")

    # Brands command
    subparsers.add_parser("brands", help="List available brands")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to file")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument(
        "--format", "-f", choices=["json", "csv"], default="json",
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    runner = AutocasionRunner()

    try:
        if args.command == "scrape":
            # all_pages mode uses max_pages=0
            max_pages = 0 if args.all_pages else args.pages
            runner.run_scrape(
                marcas=args.marcas,
                max_pages=max_pages,
                from_objetivos=args.objetivos,
                stealth=args.stealth
            )
        elif args.command == "status":
            runner.run_status()
        elif args.command == "brands":
            runner.run_brands()
        elif args.command == "export":
            runner.run_export(args.output, args.format)
    finally:
        runner.close()


if __name__ == "__main__":
    main()
