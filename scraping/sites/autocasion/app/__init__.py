"""
Autocasion Desktop Application Module.

Components:
- AutocasionScraperAgent: Runtime agent for orchestrator integration
- AutocasionRunner: CLI interface for scraping operations
- HeadlessXClient: Anti-detection browser API client

Usage:
    # CLI
    python -m scraping.sites.autocasion.app.main cli scrape --marcas audi
    python -m scraping.sites.autocasion.app.main cli status

    # GUI
    python -m scraping.sites.autocasion.app.main

    # Programmatic
    from scraping.sites.autocasion.app import AutocasionScraperAgent
    agent = AutocasionScraperAgent()
    result = await agent.scrape_marca("audi", max_pages=5)
"""

from .scraper_agent import AutocasionScraperAgent, ScrapeResult
from .runner import AutocasionRunner
from .headlessx_client import (
    HeadlessXClient,
    HeadlessXConfig,
    RenderResult,
    get_headlessx_client,
    is_headlessx_available,
    fetch_with_headlessx
)

__all__ = [
    "AutocasionScraperAgent",
    "AutocasionRunner",
    "ScrapeResult",
    "HeadlessXClient",
    "HeadlessXConfig",
    "RenderResult",
    "get_headlessx_client",
    "is_headlessx_available",
    "fetch_with_headlessx",
]
