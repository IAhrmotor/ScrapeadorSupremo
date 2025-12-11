"""
Segmented Orchestrator for OcasionPlus scraping.

Divides scraping into year segments to overcome the ~1000 listing limit
when loading all cars at once. Each segment scrapes a specific year range.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Callable

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.ocasionplus.app.playwright_scraper import PlaywrightOcasionPlusScraper
from scraping.sites.ocasionplus.parser import OcasionPlusParser
from scraping.sites.ocasionplus.site import OcasionPlusSite, OcasionPlusConfig
from scraping.storage.supabase_client import get_supabase_client, SupabaseClient


@dataclass
class SegmentResult:
    """Result from scraping a single year segment."""
    year_from: int
    year_to: int
    total_listings: int
    saved_to_db: int
    duration_seconds: float
    success: bool
    error: Optional[str] = None


@dataclass
class FullScrapeResult:
    """Aggregated result from all segments."""
    total_listings: int
    total_saved: int
    total_duplicates: int
    segments_completed: int
    segments_failed: int
    segment_results: List[SegmentResult]
    duration_seconds: float
    errors: List[str] = field(default_factory=list)


class SegmentedScrapingOrchestrator:
    """
    Orchestrates scraping across multiple year segments.

    Instead of trying to load all 14,000+ cars at once (which stops at ~1,000),
    we divide into 7 year segments and scrape each separately.

    Each segment typically has 1,000-3,500 cars, which loads successfully.
    """

    # Year segments designed to balance load (~1,500-3,500 per segment)
    YEAR_SEGMENTS = [
        (2007, 2010),  # Older cars ~1,500
        (2011, 2014),  # ~2,000
        (2015, 2017),  # ~2,500
        (2018, 2019),  # ~2,500
        (2020, 2021),  # ~3,000
        (2022, 2023),  # ~3,500
        (2024, 2025),  # Recent ~1,000
    ]

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.site = OcasionPlusSite()
        self._supabase: Optional[SupabaseClient] = None
        self._parser: Optional[OcasionPlusParser] = None

    @property
    def supabase(self) -> SupabaseClient:
        """Lazy initialization of Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def parser(self) -> OcasionPlusParser:
        """Lazy initialization of parser."""
        if self._parser is None:
            self._parser = OcasionPlusParser(supabase_client=self.supabase)
        return self._parser

    async def scrape_segment(
        self,
        year_from: int,
        year_to: int,
        max_iterations: int = 100,
        save_to_db: bool = True,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> SegmentResult:
        """
        Scrape a single year segment.

        Args:
            year_from: Start year
            year_to: End year
            max_iterations: Max scroll iterations per segment
            save_to_db: Whether to save to Supabase
            log_callback: Optional callback for logging

        Returns:
            SegmentResult with statistics
        """
        def log(msg: str):
            print(msg)
            if log_callback:
                log_callback(msg)

        start_time = time.time()

        log(f"\n{'='*60}")
        log(f"[Segment {year_from}-{year_to}] Starting...")
        log(f"{'='*60}")

        # Build URL for this segment
        url = self.site.get_search_url(year_from=year_from, year_to=year_to)
        log(f"  URL: {url}")

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

            if not html:
                return SegmentResult(
                    year_from=year_from,
                    year_to=year_to,
                    total_listings=0,
                    saved_to_db=0,
                    duration_seconds=time.time() - start_time,
                    success=False,
                    error="No HTML returned"
                )

            # Check for blocks
            is_blocked, block_type, msg = self.site.detect_block(html)
            if is_blocked:
                log(f"  WARNING: Possible block: {block_type} - {msg}")

            # Parse listings
            log(f"  Parsing HTML ({len(html):,} bytes)...")
            listings = self.parser.parse_listings(html)
            log(f"  Found {len(listings)} listings")

            # Save to database
            saved = 0
            if save_to_db and listings:
                try:
                    log(f"  Saving to Supabase...")
                    listings_data = [l.to_dict() for l in listings]
                    stats = self.supabase.save_ocasionplus_listings(listings_data)
                    saved = stats.get("ocasionplus", 0)
                    log(f"  Saved {saved} listings")
                except Exception as e:
                    log(f"  DB error: {e}")

            duration = time.time() - start_time

            log(f"\n[Segment {year_from}-{year_to}] COMPLETED")
            log(f"  Listings: {len(listings)} | Saved: {saved} | Duration: {duration:.1f}s")

            return SegmentResult(
                year_from=year_from,
                year_to=year_to,
                total_listings=len(listings),
                saved_to_db=saved,
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            log(f"  ERROR in segment {year_from}-{year_to}: {e}")
            return SegmentResult(
                year_from=year_from,
                year_to=year_to,
                total_listings=0,
                saved_to_db=0,
                duration_seconds=time.time() - start_time,
                success=False,
                error=str(e)
            )
        finally:
            await scraper.close()

    async def scrape_all_segments(
        self,
        max_iterations_per_segment: int = 100,
        save_to_db: bool = True,
        delay_between_segments: float = 10.0,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> FullScrapeResult:
        """
        Scrape all year segments sequentially.

        Args:
            max_iterations_per_segment: Max scroll iterations per segment
            save_to_db: Whether to save to Supabase
            delay_between_segments: Delay in seconds between segments
            log_callback: Optional callback for logging

        Returns:
            FullScrapeResult with aggregated statistics
        """
        def log(msg: str):
            print(msg)
            if log_callback:
                log_callback(msg)

        start_time = time.time()
        segment_results = []
        errors = []

        log("\n" + "="*70)
        log("  OCASIONPLUS - SCRAPEO SEGMENTADO COMPLETO")
        log("="*70)
        log(f"  Total segments: {len(self.YEAR_SEGMENTS)}")
        log(f"  Max iterations per segment: {max_iterations_per_segment}")
        log(f"  Delay between segments: {delay_between_segments}s")
        log("="*70)

        for i, (year_from, year_to) in enumerate(self.YEAR_SEGMENTS):
            log(f"\n>>> Processing segment {i+1}/{len(self.YEAR_SEGMENTS)}: {year_from}-{year_to}")

            result = await self.scrape_segment(
                year_from=year_from,
                year_to=year_to,
                max_iterations=max_iterations_per_segment,
                save_to_db=save_to_db,
                log_callback=log_callback
            )

            segment_results.append(result)

            if not result.success:
                errors.append(f"Segment {year_from}-{year_to}: {result.error}")

            # Delay between segments (except last one)
            if i < len(self.YEAR_SEGMENTS) - 1:
                log(f"\n  Waiting {delay_between_segments}s before next segment...")
                await asyncio.sleep(delay_between_segments)

        # Aggregate results
        total_listings = sum(r.total_listings for r in segment_results)
        total_saved = sum(r.saved_to_db for r in segment_results)
        segments_completed = sum(1 for r in segment_results if r.success)
        segments_failed = sum(1 for r in segment_results if not r.success)
        duration = time.time() - start_time

        log("\n" + "="*70)
        log("  RESULTADO FINAL - SCRAPEO SEGMENTADO")
        log("="*70)
        log(f"  Total listings scraped: {total_listings:,}")
        log(f"  Total saved to DB: {total_saved:,}")
        log(f"  Duplicates (approx): {total_listings - total_saved:,}")
        log(f"  Segments completed: {segments_completed}/{len(self.YEAR_SEGMENTS)}")
        log(f"  Segments failed: {segments_failed}")
        log(f"  Total duration: {duration:.1f}s ({duration/60:.1f} min)")

        if errors:
            log(f"\n  Errors:")
            for err in errors:
                log(f"    - {err}")

        log("="*70)

        return FullScrapeResult(
            total_listings=total_listings,
            total_saved=total_saved,
            total_duplicates=total_listings - total_saved,
            segments_completed=segments_completed,
            segments_failed=segments_failed,
            segment_results=segment_results,
            duration_seconds=duration,
            errors=errors
        )

    def get_segment_count(self) -> int:
        """Get total number of segments."""
        return len(self.YEAR_SEGMENTS)

    def get_segments(self) -> List[tuple]:
        """Get list of year segments."""
        return self.YEAR_SEGMENTS.copy()


async def main():
    """Test the segmented orchestrator."""
    orchestrator = SegmentedScrapingOrchestrator(headless=True)

    # Test with all segments
    result = await orchestrator.scrape_all_segments(
        max_iterations_per_segment=100,
        save_to_db=True,
        delay_between_segments=10.0
    )

    print(f"\nFinal: {result.total_listings} listings, {result.total_saved} saved")


if __name__ == "__main__":
    asyncio.run(main())
