"""Coordinated multi-scraper module with DNS protection."""

from ..coordinated_scraper import (
    run_coordinated_scrape,
    check_status,
    DEFAULT_CONFIG
)

__all__ = [
    "run_coordinated_scrape",
    "check_status",
    "DEFAULT_CONFIG"
]
