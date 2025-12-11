"""Cochesnet desktop application module."""

from .gui import CochesnetApp, main
from .scraper_agent import CochesnetScraperAgent, ScrapeResult

__all__ = [
    'CochesnetApp',
    'CochesnetScraperAgent',
    'ScrapeResult',
    'main'
]
