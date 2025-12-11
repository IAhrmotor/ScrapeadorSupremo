"""Autocasion scraper agent wrapper for orchestrator registration."""

import sys
from pathlib import Path

# Ensure scraping module is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Re-export the agent from its actual location
from scraping.sites.autocasion.app.scraper_agent import AutocasionScraperAgent

# This allows the registry to auto-discover this agent
__all__ = ["AutocasionScraperAgent"]
