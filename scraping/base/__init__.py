"""Base classes for scraping system."""

from .parser import BaseParser
from .site import BaseSite, SiteRegistry

__all__ = ["BaseParser", "BaseSite", "SiteRegistry"]
