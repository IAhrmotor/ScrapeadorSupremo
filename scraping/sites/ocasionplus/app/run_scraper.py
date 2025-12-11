"""
Run OcasionPlus scraper and save to database.

Usage:
    python scraping/sites/ocasionplus/app/run_scraper.py

Options:
    --headlessx     Use HeadlessX (default, requires server running)
    --playwright    Use Playwright instead of HeadlessX
    --no-save       Don't save to database (test mode)
    --iterations N  Number of scroll iterations (default: 10)
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.ocasionplus.app.scraper_agent import OcasionPlusScraperAgent


async def main():
    parser = argparse.ArgumentParser(description="Scrape OcasionPlus listings")
    parser.add_argument("--headlessx", action="store_true", default=True,
                        help="Use HeadlessX for scraping (default)")
    parser.add_argument("--playwright", action="store_true",
                        help="Use Playwright instead of HeadlessX")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save to database")
    parser.add_argument("--iterations", type=int, default=10,
                        help="Number of scroll iterations")
    parser.add_argument("--year-from", type=int, default=2007,
                        help="Start year for filtering")
    parser.add_argument("--year-to", type=int, default=2025,
                        help="End year for filtering")

    args = parser.parse_args()

    # Determine method
    use_headlessx = not args.playwright

    print("\n" + "="*60)
    print("OCASIONPLUS SCRAPER")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Method: {'HeadlessX' if use_headlessx else 'Playwright'}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Year range: {args.year_from} - {args.year_to}")
    print(f"  Save to DB: {not args.no_save}")
    print("="*60)

    # Create agent
    agent = OcasionPlusScraperAgent(
        headless=True,
        use_headlessx=use_headlessx
    )

    # Run scraper
    result = await agent.scrape_all(
        max_iterations=args.iterations,
        save_to_db=not args.no_save,
        year_from=args.year_from,
        year_to=args.year_to
    )

    # Print results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"  Total listings: {result.total_listings}")
    print(f"  Saved to DB: {result.saved_to_db}")
    print(f"  Duration: {result.duration_seconds:.1f}s")
    print(f"  Method used: {result.method_used}")
    if result.errors:
        print(f"  Errors: {result.errors}")
    print("="*60)

    return result


if __name__ == "__main__":
    result = asyncio.run(main())

    # Exit with error code if failed
    if result.total_listings == 0:
        sys.exit(1)
