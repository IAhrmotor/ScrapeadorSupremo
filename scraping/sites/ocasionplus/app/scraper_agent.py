"""Runtime agent for OcasionPlus scraping operations with HeadlessX/Playwright support."""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from agents.base_agent import BaseAgent, AgentCapability, AgentResponse
from scraping.sites.ocasionplus.parser import OcasionPlusParser
from scraping.sites.ocasionplus.site import OcasionPlusSite, OcasionPlusConfig
from scraping.storage.supabase_client import get_supabase_client, SupabaseClient


@dataclass
class ScrapeResult:
    """Result from a scraping operation."""
    total_listings: int
    scroll_iterations: int
    saved_to_db: int
    errors: List[str]
    duration_seconds: float
    method_used: str = "headlessx"


class OcasionPlusScraperAgent(BaseAgent):
    """
    Runtime agent for scraping OcasionPlus.com.

    Supports two scraping methods:
    1. HeadlessX (preferred) - Anti-detection with fingerprint spoofing
    2. Playwright (fallback) - Direct browser automation

    Uses INFINITE SCROLL pattern:
    - Single URL with all cars loaded dynamically
    - Scroll to bottom repeatedly to load more
    - Parse accumulated HTML after each load
    """

    def __init__(self, headless: bool = True, use_headlessx: bool = True):
        super().__init__(
            name="ocasionplus-scraper",
            description="Scrapes car listings from OcasionPlus.com with anti-detection"
        )
        self.site = OcasionPlusSite()
        self._supabase: Optional[SupabaseClient] = None
        self._parser: Optional[OcasionPlusParser] = None
        self.headless = headless
        self.use_headlessx = use_headlessx

    @property
    def supabase(self) -> SupabaseClient:
        """Lazy initialization of Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def parser(self) -> OcasionPlusParser:
        """Lazy initialization of parser with Supabase for marca/modelo validation."""
        if self._parser is None:
            # Pass supabase client to parser for marca/modelo validation
            self._parser = OcasionPlusParser(supabase_client=self.supabase)
        return self._parser

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="scrape_ocasionplus",
                description="Scrape car listings from OcasionPlus.com with infinite scroll",
                keywords=["ocasionplus", "scrape", "cars", "listings", "coches", "infinite scroll"],
                priority=10
            ),
        ]

    def can_handle(self, task: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Score how well this agent can handle the task."""
        task_lower = task.lower()
        score = 0.0

        if "ocasionplus" in task_lower or "ocasion plus" in task_lower:
            score += 0.5

        scrape_keywords = ["scrape", "scrap", "extract", "fetch", "get"]
        if any(k in task_lower for k in scrape_keywords):
            score += 0.3

        car_keywords = ["coche", "car", "vehiculo", "auto", "listing"]
        if any(k in task_lower for k in car_keywords):
            score += 0.2

        return min(score, 1.0)

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Execute scraping task."""
        context = context or {}

        max_iterations = context.get("max_iterations", 50)
        save_to_db = context.get("save_to_db", True)
        year_from = context.get("year_from", 2007)
        year_to = context.get("year_to", 2025)

        result = await self.scrape_all(
            max_iterations=max_iterations,
            save_to_db=save_to_db,
            year_from=year_from,
            year_to=year_to
        )

        return AgentResponse(
            success=len(result.errors) == 0,
            result=result,
            message=f"Scraped {result.total_listings} listings from OcasionPlus using {result.method_used}",
            metadata={
                "iterations": result.scroll_iterations,
                "method": result.method_used
            }
        )

    def scrape_with_headlessx(
        self,
        url: str,
        max_iterations: int = 50,
        log_callback: Optional[callable] = None
    ) -> Optional[str]:
        """
        Scrape using HeadlessX with anti-detection.

        Args:
            url: URL to scrape
            max_iterations: Max scroll iterations
            log_callback: Optional logging callback

        Returns:
            HTML content or None
        """
        from scraping.sites.ocasionplus.app.headlessx_scraper import (
            HeadlessXOcasionPlusScraper,
            HeadlessXOcasionPlusConfig
        )

        config = HeadlessXOcasionPlusConfig(
            scroll_iterations=max_iterations,
            device_profile="mid-range-desktop",
            geo_profile="spain",
        )

        scraper = HeadlessXOcasionPlusScraper(config=config)
        return scraper.scrape_with_scroll(
            url=url,
            max_iterations=max_iterations,
            log_callback=log_callback
        )

    async def scrape_with_playwright(
        self,
        url: str,
        max_iterations: int = 50,
        log_callback: Optional[callable] = None
    ) -> Optional[str]:
        """
        Scrape using Playwright (fallback method).

        Args:
            url: URL to scrape
            max_iterations: Max scroll iterations
            log_callback: Optional logging callback

        Returns:
            HTML content or None
        """
        from scraping.sites.ocasionplus.app.playwright_scraper import PlaywrightOcasionPlusScraper

        scraper = PlaywrightOcasionPlusScraper(headless=self.headless)

        try:
            await scraper.start()
            html = await scraper.scrape_with_infinite_scroll(
                url=url,
                max_iterations=max_iterations,
                scroll_delay=self.site.config.delay_between_scrolls,
                click_delay=self.site.config.delay_between_clicks,
                button_selector=self.site.config.load_more_button_selector,
                log_callback=log_callback
            )
            return html
        finally:
            await scraper.close()

    async def scrape_all(
        self,
        max_iterations: int = 50,
        save_to_db: bool = True,
        year_from: int = 2007,
        year_to: int = 2025,
        log_callback: Optional[callable] = None
    ) -> ScrapeResult:
        """
        Scrape all listings from OcasionPlus.

        Strategy:
        - For infinite scroll (max_iterations > 5): Use Playwright (real scroll loop)
        - For quick scrape (max_iterations <= 5): Use HeadlessX (single page load)

        HeadlessX doesn't support custom scripts, so Playwright is required
        for true infinite scroll with iteration control.

        Args:
            max_iterations: Maximum scroll iterations
            save_to_db: Whether to save to Supabase
            year_from: Year range start
            year_to: Year range end
            log_callback: Optional callback function for logging

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
        method_used = "unknown"

        # Decide method based on iterations needed
        # HeadlessX only does ~20-30 items with scrollToBottom
        # For more items, we need Playwright's real scroll loop
        use_playwright_for_scroll = max_iterations > 5

        log(f"\n{'='*60}")
        log(f"[OcasionPlusScraper] Starting scrape")
        log(f"  Max iterations: {max_iterations}")
        log(f"  Year range: {year_from} - {year_to}")
        if use_playwright_for_scroll:
            log(f"  Method: Playwright (infinite scroll with {max_iterations} iterations)")
        else:
            log(f"  Method: HeadlessX (quick scrape)")
        log(f"{'='*60}")

        # Get search URL
        url = self.site.get_search_url(year_from=year_from, year_to=year_to)
        log(f"\n  URL: {url}")

        html = None

        # Use Playwright for real infinite scroll
        if use_playwright_for_scroll:
            try:
                log("\n  Using Playwright for infinite scroll...")
                html = await self.scrape_with_playwright(
                    url=url,
                    max_iterations=max_iterations,
                    log_callback=log_callback
                )
                if html:
                    method_used = "playwright"
                    log("  Playwright scrape successful")
            except Exception as e:
                log(f"  Playwright failed: {e}")
                errors.append(f"Playwright error: {e}")

        # Try HeadlessX for quick scrape or as fallback
        if not html and self.use_headlessx:
            try:
                log("\n  Attempting HeadlessX scrape...")
                html = self.scrape_with_headlessx(
                    url=url,
                    max_iterations=max_iterations,
                    log_callback=log_callback
                )
                if html:
                    method_used = "headlessx"
                    log("  HeadlessX scrape successful")
            except Exception as e:
                log(f"  HeadlessX failed: {e}")
                errors.append(f"HeadlessX error: {e}")

        # Final fallback to Playwright if HeadlessX also failed
        if not html and not use_playwright_for_scroll:
            try:
                log("\n  Falling back to Playwright...")
                html = await self.scrape_with_playwright(
                    url=url,
                    max_iterations=max_iterations,
                    log_callback=log_callback
                )
                if html:
                    method_used = "playwright"
                    log("  Playwright scrape successful")
            except Exception as e:
                log(f"  Playwright failed: {e}")
                errors.append(f"Playwright error: {e}")

        if not html:
            log("  ERROR: All scraping methods failed")
            return ScrapeResult(
                total_listings=0,
                scroll_iterations=0,
                saved_to_db=0,
                errors=errors or ["All scraping methods failed"],
                duration_seconds=time.time() - start_time,
                method_used=method_used
            )

        # Check for blocks
        is_blocked, block_type, msg = self.site.detect_block(html)
        if is_blocked:
            log(f"  WARNING: Page may be blocked: {block_type} - {msg}")
            errors.append(f"Possible block: {block_type}")

        # Parse all listings
        log(f"\n  Parsing HTML ({len(html):,} bytes)...")
        listings = self.parser.parse_listings(html)
        log(f"  Found {len(listings)} total listings")

        # Save to database
        if save_to_db and listings:
            try:
                log(f"\n  Saving to Supabase...")
                listings_data = [l.to_dict() for l in listings]
                stats = self.supabase.save_ocasionplus_listings(listings_data)
                saved = stats.get("ocasionplus", 0)
                log(f"  Saved {saved} listings to Supabase")
            except Exception as e:
                log(f"  DB error: {e}")
                errors.append(f"DB error: {e}")

        duration = time.time() - start_time

        log(f"\n{'='*60}")
        log(f"  COMPLETED: OCASIONPLUS")
        log(f"  Listings: {len(listings)} | Saved: {saved} | Duration: {duration:.1f}s")
        log(f"  Method: {method_used}")
        if errors:
            log(f"  Warnings/Errors: {len(errors)}")
        log(f"{'='*60}")

        return ScrapeResult(
            total_listings=len(listings),
            scroll_iterations=max_iterations,
            saved_to_db=saved,
            errors=errors,
            duration_seconds=duration,
            method_used=method_used
        )

    async def scrape_all_progressive(
        self,
        max_iterations: int = 200,
        save_to_db: bool = True,
        year_from: int = 2007,
        year_to: int = 2025,
        save_every: int = 10,
        log_callback: Optional[callable] = None
    ) -> ScrapeResult:
        """
        Scrape all listings with PROGRESSIVE SAVES every N iterations.

        This method saves to Supabase every N iterations instead of at the end,
        so data is preserved even if the scraping is interrupted.

        Args:
            max_iterations: Maximum scroll iterations
            save_to_db: Whether to save to Supabase
            year_from: Year range start
            year_to: Year range end
            save_every: Save to DB every N iterations (default: 10)
            log_callback: Optional callback function for logging

        Returns:
            ScrapeResult with statistics
        """
        from scraping.sites.ocasionplus.app.playwright_scraper import PlaywrightOcasionPlusScraper

        def log(msg: str):
            print(msg)
            if log_callback:
                log_callback(msg)

        start_time = time.time()
        errors = []
        total_saved = 0
        seen_listing_ids = set()  # Track already saved IDs to avoid duplicates

        log(f"\n{'='*60}")
        log(f"[OcasionPlusScraper] Starting PROGRESSIVE scrape")
        log(f"  Max iterations: {max_iterations}")
        log(f"  Save every: {save_every} iterations")
        log(f"  Year range: {year_from} - {year_to}")
        log(f"{'='*60}")

        url = self.site.get_search_url(year_from=year_from, year_to=year_to)
        log(f"\n  URL: {url}")

        # Create save callback that parses and saves
        def save_progress(html: str, iteration: int) -> int:
            nonlocal total_saved, seen_listing_ids

            try:
                # Parse HTML
                listings = self.parser.parse_listings(html)

                # Filter out already saved listings
                new_listings = [l for l in listings if l.listing_id not in seen_listing_ids]

                if not new_listings:
                    return 0

                # Mark as seen
                for l in new_listings:
                    seen_listing_ids.add(l.listing_id)

                # Save to Supabase
                if save_to_db:
                    listings_data = [l.to_dict() for l in new_listings]
                    stats = self.supabase.save_ocasionplus_listings(listings_data)
                    saved = stats.get("ocasionplus", 0)
                    return saved

                return len(new_listings)

            except Exception as e:
                log(f"  Save error: {e}")
                errors.append(f"Save error at iteration {iteration}: {e}")
                return 0

        scraper = PlaywrightOcasionPlusScraper(headless=self.headless)

        try:
            await scraper.start()
            log("\n  Using Playwright with progressive saves...")

            html, saved_count = await scraper.scrape_with_progressive_save(
                url=url,
                max_iterations=max_iterations,
                scroll_delay=self.site.config.delay_between_scrolls,
                click_delay=self.site.config.delay_between_clicks,
                button_selector=self.site.config.load_more_button_selector,
                log_callback=log_callback,
                save_callback=save_progress if save_to_db else None,
                save_every=save_every
            )

            total_saved = saved_count

            if not html:
                log("  ERROR: Scraping failed")
                return ScrapeResult(
                    total_listings=0,
                    scroll_iterations=0,
                    saved_to_db=total_saved,
                    errors=errors or ["Scraping failed"],
                    duration_seconds=time.time() - start_time,
                    method_used="playwright_progressive"
                )

            # Parse final HTML to get total count
            final_listings = self.parser.parse_listings(html)

            duration = time.time() - start_time

            log(f"\n{'='*60}")
            log(f"  COMPLETED: OCASIONPLUS (Progressive)")
            log(f"  Total in page: {len(final_listings)} | Saved: {total_saved} | Duration: {duration:.1f}s")
            log(f"{'='*60}")

            return ScrapeResult(
                total_listings=len(final_listings),
                scroll_iterations=max_iterations,
                saved_to_db=total_saved,
                errors=errors,
                duration_seconds=duration,
                method_used="playwright_progressive"
            )

        except Exception as e:
            log(f"  EXCEPTION: {e}")
            errors.append(str(e))
            return ScrapeResult(
                total_listings=0,
                scroll_iterations=0,
                saved_to_db=total_saved,
                errors=errors,
                duration_seconds=time.time() - start_time,
                method_used="playwright_progressive"
            )

        finally:
            await scraper.close()

    async def scrape_by_segments(
        self,
        max_iterations_per_segment: int = 100,
        save_to_db: bool = True,
        delay_between_segments: float = 10.0,
        log_callback: Optional[callable] = None
    ):
        """
        Scrape all listings using year segmentation strategy.

        This method divides the scraping into year segments to overcome
        the ~1000 listing limit when loading all cars at once.

        Args:
            max_iterations_per_segment: Max scroll iterations per segment
            save_to_db: Whether to save to Supabase
            delay_between_segments: Delay in seconds between segments
            log_callback: Optional callback function for logging

        Returns:
            FullScrapeResult with aggregated statistics from all segments
        """
        from scraping.sites.ocasionplus.app.segmented_orchestrator import (
            SegmentedScrapingOrchestrator
        )

        orchestrator = SegmentedScrapingOrchestrator(headless=self.headless)

        result = await orchestrator.scrape_all_segments(
            max_iterations_per_segment=max_iterations_per_segment,
            save_to_db=save_to_db,
            delay_between_segments=delay_between_segments,
            log_callback=log_callback
        )

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics."""
        stats = self.supabase.get_stats()
        ocasionplus_stats = stats.get("ocasionplus", {})

        return {
            "total_listings": ocasionplus_stats.get("total", 0),
            "scraping_pattern": "infinite_scroll",
            "method": "headlessx" if self.use_headlessx else "playwright"
        }

    def close(self):
        """Clean up resources."""
        pass
