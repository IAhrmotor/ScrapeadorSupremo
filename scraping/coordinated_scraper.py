"""
Coordinated scraper that runs multiple scrapers with DNS protection.

This module provides a CLI and programmatic interface for running
Coches.net, Autocasion, and OcasionPlus scrapers in a coordinated
manner that prevents DNS saturation.

Usage:
    # CLI
    python coordinated_scraper.py --all
    python coordinated_scraper.py --scrapers cochesnet autocasion
    python coordinated_scraper.py --status

    # Programmatic
    from scraping.coordinated_scraper import run_coordinated_scrape
    results = await run_coordinated_scrape(["cochesnet", "autocasion"])
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import OrchestratorAgent
from core.network import CoordinatorConfig


# Default configuration for coordinated scraping
DEFAULT_CONFIG = {
    "max_global_connections": 6,
    "scrapers": {
        "cochesnet": {
            "max_concurrent": 3,
            "max_pages": 0,  # All pages
            "save_to_db": True
        },
        "autocasion": {
            "max_concurrent": 2,
            "max_pages": 0,
            "save_to_db": True
        },
        "ocasionplus": {
            "max_concurrent": 1,
            "max_iterations": 50,
            "save_to_db": True
        }
    }
}


async def create_scraper_func(
    scraper_name: str,
    coordinator,
    config: Dict[str, Any]
) -> callable:
    """
    Create a scraper function that uses the coordinator.

    Args:
        scraper_name: Name of the scraper
        coordinator: ScrapingCoordinator instance
        config: Scraper-specific configuration

    Returns:
        Async function that runs the scraper
    """
    if scraper_name == "cochesnet":
        from scraping.sites.cochesnet.app.scraper_agent import CochesNetScraperAgent

        async def run_cochesnet():
            agent = CochesNetScraperAgent()
            results = []

            # Use coordinator slots
            async with coordinator.slot("cochesnet"):
                # Run with reduced workers
                result = await agent.scrape_batch_parallel(
                    year_ranges=None,  # All years
                    max_pages=config.get("max_pages", 0),
                    save_to_db=config.get("save_to_db", True),
                    max_workers=config.get("max_concurrent", 3)
                )
                results.extend(result)

            return {
                "total_listings": sum(r.total_listings for r in results),
                "total_saved": sum(r.saved_to_db for r in results),
                "pages_scraped": sum(r.pages_scraped for r in results)
            }

        return run_cochesnet

    elif scraper_name == "autocasion":
        from scraping.sites.autocasion.app.scraper_agent import AutocasionScraperAgent

        async def run_autocasion():
            agent = AutocasionScraperAgent()

            # Get all brands
            brands = agent.site.get_brands_list()

            async with coordinator.slot("autocasion"):
                results = await agent.scrape_batch_parallel(
                    marcas=brands,
                    max_pages=config.get("max_pages", 0),
                    save_to_db=config.get("save_to_db", True),
                    max_workers=config.get("max_concurrent", 2)
                )

            return {
                "total_listings": sum(r.total_listings for r in results),
                "total_saved": sum(r.saved_to_db for r in results),
                "brands_scraped": len(results)
            }

        return run_autocasion

    elif scraper_name == "ocasionplus":
        from scraping.sites.ocasionplus.app.scraper_agent import OcasionPlusScraperAgent

        async def run_ocasionplus():
            agent = OcasionPlusScraperAgent()

            async with coordinator.slot("ocasionplus"):
                result = await agent.scrape_all(
                    max_iterations=config.get("max_iterations", 50),
                    save_to_db=config.get("save_to_db", True)
                )

            return {
                "total_listings": result.total_listings,
                "total_saved": result.saved_to_db
            }

        return run_ocasionplus

    else:
        raise ValueError(f"Unknown scraper: {scraper_name}")


async def run_coordinated_scrape(
    scrapers: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run multiple scrapers in a coordinated manner.

    Args:
        scrapers: List of scraper names to run
        config: Optional configuration override

    Returns:
        Dict with results from all scrapers
    """
    config = config or DEFAULT_CONFIG

    # Create orchestrator and setup coordinator
    orchestrator = OrchestratorAgent()
    orchestrator.setup_coordinator(
        max_global_connections=config.get("max_global_connections", 6),
        scraper_slots={
            name: cfg.get("max_concurrent", 2)
            for name, cfg in config.get("scrapers", {}).items()
        }
    )

    coordinator = orchestrator.coordinator

    # Create scraper functions
    scraper_funcs = {}
    for name in scrapers:
        scraper_config = config.get("scrapers", {}).get(name, {})
        try:
            scraper_funcs[name] = await create_scraper_func(
                name, coordinator, scraper_config
            )
        except ImportError as e:
            print(f"Warning: Could not load scraper {name}: {e}")
            continue

    if not scraper_funcs:
        return {"error": "No scrapers could be loaded"}

    # Run coordinated scrape
    try:
        results = await orchestrator.coordinate_scrapers(
            scrapers=list(scraper_funcs.keys()),
            scraper_funcs=scraper_funcs,
            config=config
        )
        return results
    finally:
        await orchestrator.close_coordinator()


async def check_status() -> Dict[str, Any]:
    """Check the current status of the coordinator."""
    orchestrator = OrchestratorAgent()
    orchestrator.setup_coordinator()

    coordinator = orchestrator.coordinator

    # Start monitoring briefly to get status
    await coordinator.start_monitoring()
    await asyncio.sleep(2)  # Let it do one check

    status = {
        "dns_status": coordinator.dns_status.value,
        "is_paused": coordinator.is_paused,
        "stats": coordinator.get_stats()
    }

    await coordinator.stop_monitoring()
    await orchestrator.close_coordinator()

    return status


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Coordinated scraper with DNS protection"
    )
    parser.add_argument(
        "--scrapers",
        nargs="+",
        choices=["cochesnet", "autocasion", "ocasionplus"],
        help="Scrapers to run"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scrapers"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check coordinator status"
    )
    parser.add_argument(
        "--max-connections",
        type=int,
        default=6,
        help="Maximum global connections (default: 6)"
    )

    args = parser.parse_args()

    if args.status:
        status = asyncio.run(check_status())
        print("\n=== Coordinator Status ===")
        print(f"DNS Status: {status['dns_status']}")
        print(f"Is Paused: {status['is_paused']}")
        print(f"\nDNS Monitor:")
        for key, value in status['stats'].get('dns_monitor', {}).items():
            print(f"  {key}: {value}")
        return

    if args.all:
        scrapers = ["cochesnet", "autocasion", "ocasionplus"]
    elif args.scrapers:
        scrapers = args.scrapers
    else:
        parser.print_help()
        return

    config = DEFAULT_CONFIG.copy()
    config["max_global_connections"] = args.max_connections

    print(f"\n{'='*60}")
    print(f"COORDINATED SCRAPE")
    print(f"Scrapers: {', '.join(scrapers)}")
    print(f"Max connections: {args.max_connections}")
    print(f"{'='*60}\n")

    results = asyncio.run(run_coordinated_scrape(scrapers, config))

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Success: {results.get('success', False)}")
    print(f"Duration: {results.get('duration_seconds', 0):.1f}s")

    if results.get('results'):
        print("\nScraper Results:")
        for name, data in results['results'].items():
            print(f"  {name}:")
            for key, value in data.items():
                print(f"    {key}: {value}")

    if results.get('errors'):
        print("\nErrors:")
        for name, error in results['errors'].items():
            print(f"  {name}: {error}")

    stats = results.get('coordinator_stats', {})
    if stats:
        print(f"\nDNS Cache Stats:")
        cache = stats.get('dns', {}).get('cache', {})
        print(f"  Hits: {cache.get('hits', 0)}")
        print(f"  Misses: {cache.get('misses', 0)}")
        print(f"  Hit Rate: {cache.get('hit_rate', '0%')}")


if __name__ == "__main__":
    main()
