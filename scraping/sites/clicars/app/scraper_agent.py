"""Runtime agent for Clicars scraping operations with Playwright for infinite scroll."""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from agents.base_agent import BaseAgent, AgentCapability, AgentResponse
from scraping.sites.clicars.parser import ClicarsParser
from scraping.sites.clicars.site import ClicarsSite, ClicarsConfig
from scraping.storage.supabase_client import get_supabase_client, SupabaseClient
from scraping.sites.clicars.app.playwright_scraper import PlaywrightClicarsScaper


@dataclass
class ScrapeResult:
    """Result from a scraping operation."""
    total_listings: int
    scroll_iterations: int
    saved_to_db: int
    errors: List[str]
    duration_seconds: float
    method_used: str = "playwright"


class ClicarsScraperAgent(BaseAgent):
    """
    Runtime agent for scraping Clicars.com.

    Uses Playwright for INFINITE SCROLL pattern:
    - Single URL with all cars loaded dynamically
    - Scroll to bottom + click "Ver más" button repeatedly
    - Parse accumulated HTML after each load
    - Headless mode for stealth
    """

    def __init__(self, headless: bool = True):
        super().__init__(
            name="clicars-scraper",
            description="Scrapes car listings from Clicars.com with infinite scroll support using Playwright"
        )
        self.site = ClicarsSite()
        self.parser = ClicarsParser()
        self._supabase: Optional[SupabaseClient] = None
        self._playwright_scraper: Optional[PlaywrightClicarsScaper] = None
        self.headless = headless

    @property
    def supabase(self) -> SupabaseClient:
        """Lazy initialization of Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="scrape_clicars",
                description="Scrape car listings from Clicars.com with infinite scroll",
                keywords=["clicars", "scrape", "cars", "listings", "coches", "infinite scroll"],
                priority=10
            ),
        ]

    def can_handle(self, task: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Score how well this agent can handle the task."""
        task_lower = task.lower()
        score = 0.0

        # High confidence for clicars-specific tasks
        if "clicars" in task_lower or "clickcars" in task_lower:
            score += 0.5

        # Scraping keywords
        scrape_keywords = ["scrape", "scrap", "extract", "fetch", "get"]
        if any(k in task_lower for k in scrape_keywords):
            score += 0.3

        # Car-related keywords
        car_keywords = ["coche", "car", "vehiculo", "auto", "listing"]
        if any(k in task_lower for k in car_keywords):
            score += 0.2

        return min(score, 1.0)

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Execute scraping task."""
        context = context or {}

        max_iterations = context.get("max_iterations", 200)  # ~200 * 12 = 2400 cars
        save_to_db = context.get("save_to_db", True)

        result = await self.scrape_all(
            max_iterations=max_iterations,
            save_to_db=save_to_db
        )

        return AgentResponse(
            success=len(result.errors) == 0,
            result=result,
            message=f"Scraped {result.total_listings} listings from Clicars using {result.method_used}",
            metadata={
                "iterations": result.scroll_iterations,
                "method": result.method_used
            }
        )

    async def scrape_all(
        self,
        max_iterations: int = 200,
        save_to_db: bool = True,
        log_callback: Optional[callable] = None
    ) -> ScrapeResult:
        """
        Scrape all listings from Clicars using infinite scroll with Playwright.

        Args:
            max_iterations: Maximum scroll+click iterations
            save_to_db: Whether to save to Supabase
            log_callback: Optional callback function for GUI logging

        Returns:
            ScrapeResult with statistics
        """
        def log(msg: str):
            print(msg)
            if log_callback:
                log_callback(msg)

        start_time = time.time()
        errors = []
        saved = 0
        scroll_iterations = 0

        log(f"\n{'='*60}")
        log(f"[ClicarsScaper] Starting Playwright infinite scroll scrape")
        log(f"  Max iterations: {max_iterations}")
        log(f"  Headless: {self.headless}")
        log(f"{'='*60}")

        # Get search URL (single URL for infinite scroll)
        url = self.site.get_search_url()
        log(f"\n  URL: {url}")

        # Create Playwright scraper
        scraper = PlaywrightClicarsScaper(headless=self.headless)

        try:
            # Start browser
            await scraper.start()
            log("  Playwright browser started")

            # Scrape with infinite scroll
            html = await scraper.scrape_with_infinite_scroll(
                url=url,
                button_selector=self.site.config.load_more_button_selector,
                max_iterations=max_iterations,
                scroll_delay=self.site.config.delay_between_scrolls,
                click_delay=self.site.config.delay_between_clicks,
                log_callback=log_callback
            )

            if not html:
                log(f"  ERROR: Failed to fetch page")
                return ScrapeResult(
                    total_listings=0,
                    scroll_iterations=0,
                    saved_to_db=0,
                    errors=["Failed to fetch page"],
                    duration_seconds=time.time() - start_time,
                    method_used="playwright"
                )

            # Check for blocks
            is_blocked, block_type, msg = self.site.detect_block(html)
            if is_blocked:
                log(f"  ERROR: Page blocked: {block_type} - {msg}")
                errors.append(f"Blocked: {block_type}")
                return ScrapeResult(
                    total_listings=0,
                    scroll_iterations=0,
                    saved_to_db=0,
                    errors=errors,
                    duration_seconds=time.time() - start_time,
                    method_used="playwright"
                )

            # Parse all listings
            log(f"\n  Parsing HTML...")
            listings = self.parser.parse(html)
            log(f"  Found {len(listings)} total listings")

            # Set source for each listing
            for listing in listings:
                listing.source = "clicars"
                if not listing.url:
                    listing.url = url

            # Save to database
            if save_to_db and listings:
                try:
                    log(f"\n  Saving to Supabase...")
                    stats = self.supabase.save_listings(listings)
                    saved = stats.get("clicars", 0)
                    log(f"  Saved {saved} listings to Supabase")
                except Exception as e:
                    log(f"  DB error: {e}")
                    errors.append(f"DB error: {e}")

            duration = time.time() - start_time

            log(f"\n{'='*60}")
            log(f"  COMPLETED: CLICARS")
            log(f"  Listings: {len(listings)} | Duration: {duration:.1f}s")
            log(f"  Method: playwright (headless={self.headless})")
            if errors:
                log(f"  Errors: {len(errors)}")
            log(f"{'='*60}")

            return ScrapeResult(
                total_listings=len(listings),
                scroll_iterations=scroll_iterations,
                saved_to_db=saved,
                errors=errors,
                duration_seconds=duration,
                method_used="playwright"
            )

        except Exception as e:
            log(f"  EXCEPTION: {e}")
            errors.append(str(e))
            return ScrapeResult(
                total_listings=0,
                scroll_iterations=0,
                saved_to_db=0,
                errors=errors,
                duration_seconds=time.time() - start_time,
                method_used="playwright"
            )

        finally:
            # Close browser
            await scraper.close()
            log("  Playwright browser closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics."""
        stats = self.supabase.get_stats()
        clicars_stats = stats.get("clicars", {})

        return {
            "total_listings": clicars_stats.get("total", 0),
            "scraping_pattern": "infinite_scroll",
            "method": "playwright"
        }

    def close(self):
        """Clean up resources."""
        # Playwright scraper handles its own cleanup in context manager
        pass
