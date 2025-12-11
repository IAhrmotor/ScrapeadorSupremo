"""Runtime agent for Cochesnet scraping operations."""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import random
import os

import requests
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from agents.base_agent import BaseAgent
from scraping.sites.cochesnet.parser import CochesNetParser
from scraping.sites.cochesnet.site import CochesNetSite
from scraping.storage.supabase_client import get_supabase_client, SupabaseClient


@dataclass
class ScrapeResult:
    """Result from a scraping operation."""
    total_listings: int = 0
    new_listings: int = 0
    updated_listings: int = 0
    errors: int = 0
    duration: float = 0.0


# Profile rotation pools for anti-detection
DEVICE_PROFILES = [
    "mid-range-desktop",
    "high-end-desktop",
    "low-end-desktop",
    "macbook-pro",
    "windows-laptop",
]

GEO_PROFILES = [
    "us-east",
    "us-west",
    "eu-west",
    "eu-central",
]

BEHAVIOR_PROFILES = [
    "natural",
    "cautious",
    "fast",
]


class CochesnetScraperAgent(BaseAgent):
    """
    Runtime agent for scraping Coches.net.

    Features:
    - Year-based scraping (2007-2025)
    - Multi-year batch scraping
    - Progress tracking and error handling
    - Database integration with Supabase
    - Profile rotation for anti-detection
    - True parallelism with async httpx

    URL pattern: https://www.coches.net/citroen/segunda-mano/<year>/?pg=<page>
    (marca="citroen" used as default for general listings)
    """

    def __init__(self):
        super().__init__(
            name="cochesnet-scraper",
            description="Scrapes car listings from Coches.net by year"
        )
        self.site = CochesNetSite()
        self.parser = CochesNetParser()
        self._supabase: Optional[SupabaseClient] = None
        self._session: Optional[requests.Session] = None
        self._async_client: Optional[httpx.AsyncClient] = None
        self._should_stop = False
        self._request_count = 0  # Track requests for rotation
        self._request_lock = asyncio.Lock()  # Thread-safe counter access
        self._profile_index = 0  # Round-robin profile index

    @property
    def supabase(self) -> SupabaseClient:
        """Lazy initialization of Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def session(self) -> requests.Session:
        """Lazy initialization of requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            })
        return self._session

    async def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client (reused for connection pooling)."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(200.0, connect=30.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._async_client

    async def _close_async_client(self):
        """Close async client and release resources."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def _get_next_profiles(self) -> tuple[str, str, str]:
        """Get next profiles using round-robin rotation (thread-safe with lock)."""
        # Round-robin instead of random for better distribution
        device = DEVICE_PROFILES[self._profile_index % len(DEVICE_PROFILES)]
        geo = GEO_PROFILES[self._profile_index % len(GEO_PROFILES)]
        behavior = BEHAVIOR_PROFILES[self._profile_index % len(BEHAVIOR_PROFILES)]
        self._profile_index += 1
        return device, geo, behavior

    def _build_headlessx_payload(self, url: str, device: str, geo: str, behavior: str) -> dict:
        """Build HeadlessX API payload (shared between sync/async methods)."""
        return {
            "url": url,
            "timeout": 180000,  # 3 minutes
            "waitUntil": "networkidle",
            "returnPartialOnTimeout": True,

            # Rotated profiles for anti-detection
            "deviceProfile": device,
            "geoProfile": geo,
            "behaviorProfile": behavior,

            # Anti-detection features
            "enableCanvasSpoofing": True,
            "enableWebGLSpoofing": True,
            "enableAudioSpoofing": True,
            "enableWebRTCBlocking": True,
            "enableAdvancedStealth": True,

            # Behavioral simulation
            "simulateMouseMovement": True,
            "simulateScrolling": True,
            "humanDelays": True,
            "randomizeTimings": True,

            # Page interaction
            "waitForNetworkIdle": True,
            "captureConsole": False
        }

    def _fetch_with_headlessx(self, url: str, log_callback: Optional[Callable] = None) -> str:
        """
        Fetch HTML using HeadlessX API (sync version).

        HeadlessX provides advanced anti-detection features that bypass
        Cochesnet's anti-bot protection.

        Args:
            url: URL to fetch
            log_callback: Optional callback for log messages

        Returns:
            Rendered HTML as string
        """
        import requests as req

        log = log_callback or (lambda msg: print(msg))

        # Get HeadlessX configuration from environment
        api_url = os.getenv('HEADLESSX_URL', 'http://localhost:3000')
        auth_token = os.getenv('HEADLESSX_TOKEN') or os.getenv('HEADLESSX_AUTH_TOKEN')

        if not auth_token:
            raise ValueError(
                "HEADLESSX_TOKEN not set in .env file. "
                "Please configure it to use HeadlessX scraping."
            )

        # Get profiles and increment counter
        self._request_count += 1
        device, geo, behavior = self._get_next_profiles()

        # Build payload using shared helper
        api_endpoint = f"{api_url}/api/render"
        payload = self._build_headlessx_payload(url, device, geo, behavior)
        params = {"token": auth_token}

        log(f"    HeadlessX API: {api_endpoint}")
        log(f"    Profile: {device} | {geo} | {behavior}")
        log(f"    Fetching... (request #{self._request_count})")

        try:
            fetch_start = time.time()
            response = req.post(
                api_endpoint,
                params=params,
                json=payload,
                timeout=200
            )
            fetch_elapsed = time.time() - fetch_start

            response.raise_for_status()
            log(f"    Status: {response.status_code}")

            # Parse response
            data = response.json()
            html = data.get("html", "")

            if not html:
                error_msg = data.get("error", data.get("message", "No HTML returned"))
                raise Exception(f"HeadlessX API error: {error_msg}")

            log(f"    HTML: {len(html):,} bytes")
            log(f"    Tiempo: {fetch_elapsed:.1f}s")

            # Check if page loaded correctly
            if "__INITIAL_PROPS__" in html:
                log(f"    OK: __INITIAL_PROPS__ encontrado")
            else:
                log(f"    WARNING: __INITIAL_PROPS__ no encontrado")

            return html

        except req.RequestException as e:
            log(f"    ERROR: HeadlessX API request failed: {e}")
            raise
        except Exception as e:
            log(f"    ERROR in HeadlessX: {e}")
            raise

    async def _fetch_with_headlessx_async(
        self,
        url: str,
        log_callback: Optional[Callable] = None,
        max_retries: int = 3
    ) -> str:
        """
        Fetch HTML using HeadlessX API (ASYNC version for true parallelism).

        This version uses httpx async client which doesn't block the event loop,
        allowing multiple requests to run truly in parallel.

        Features:
        - Reusable client for connection pooling
        - Exponential backoff retry logic
        - Thread-safe counter updates with asyncio.Lock

        Args:
            url: URL to fetch
            log_callback: Optional callback for log messages
            max_retries: Maximum retry attempts (default 3)

        Returns:
            Rendered HTML as string
        """
        log = log_callback or (lambda msg: print(msg))

        # Get HeadlessX configuration from environment
        api_url = os.getenv('HEADLESSX_URL', 'http://localhost:3000')
        auth_token = os.getenv('HEADLESSX_TOKEN') or os.getenv('HEADLESSX_AUTH_TOKEN')

        if not auth_token:
            raise ValueError(
                "HEADLESSX_TOKEN not set in .env file. "
                "Please configure it to use HeadlessX scraping."
            )

        api_endpoint = f"{api_url}/api/render"
        params = {"token": auth_token}

        # Thread-safe counter increment and profile selection
        async with self._request_lock:
            self._request_count += 1
            request_num = self._request_count
            device, geo, behavior = self._get_next_profiles()

        # Build payload using shared helper
        payload = self._build_headlessx_payload(url, device, geo, behavior)

        log(f"    HeadlessX ASYNC: {api_endpoint}")
        log(f"    Profile: {device} | {geo} | {behavior}")
        log(f"    Fetching... (request #{request_num})")

        last_error = None

        for attempt in range(max_retries):
            try:
                fetch_start = time.time()

                # Use reusable async client for connection pooling
                client = await self._get_async_client()
                response = await client.post(
                    api_endpoint,
                    params=params,
                    json=payload
                )

                fetch_elapsed = time.time() - fetch_start

                response.raise_for_status()
                log(f"    Status: {response.status_code}")

                # Parse response
                data = response.json()
                html = data.get("html", "")

                if not html:
                    error_msg = data.get("error", data.get("message", "No HTML returned"))
                    raise Exception(f"HeadlessX API error: {error_msg}")

                log(f"    HTML: {len(html):,} bytes")
                log(f"    Tiempo: {fetch_elapsed:.1f}s")

                # Check if page loaded correctly
                if "__INITIAL_PROPS__" in html:
                    log(f"    OK: __INITIAL_PROPS__ encontrado")
                else:
                    log(f"    WARNING: __INITIAL_PROPS__ no encontrado")

                return html

            except httpx.TimeoutException as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                log(f"    TIMEOUT (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    log(f"    Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

            except httpx.HTTPStatusError as e:
                last_error = e
                log(f"    HTTP ERROR {e.response.status_code} (attempt {attempt + 1}/{max_retries})")
                # Don't retry on 4xx client errors (except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    log(f"    Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

            except httpx.RequestError as e:
                last_error = e
                wait_time = 2 ** attempt
                log(f"    REQUEST ERROR (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    log(f"    Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

            except Exception as e:
                last_error = e
                log(f"    ERROR in HeadlessX async: {e}")
                raise

        # All retries exhausted
        log(f"    FAILED after {max_retries} attempts")
        raise last_error or Exception("Max retries exhausted")

    def stop(self):
        """Stop the scraping process."""
        self._should_stop = True

    async def scrape_years(
        self,
        years: List[int],
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
        parallel: bool = False,
        max_workers: int = 2
    ) -> ScrapeResult:
        """
        Scrape multiple years.

        Args:
            years: List of years to scrape (e.g., [2020, 2021, 2022])
            progress_callback: Optional callback for progress updates
            log_callback: Optional callback for log messages
            parallel: If True, scrape years in parallel (faster but more resource intensive)
            max_workers: Maximum number of concurrent year scrapers (only used if parallel=True)

        Returns:
            ScrapeResult with aggregated statistics
        """
        if parallel and len(years) > 1:
            return await self._scrape_years_parallel(
                years=years,
                progress_callback=progress_callback,
                log_callback=log_callback,
                max_workers=max_workers
            )
        else:
            return await self._scrape_years_sequential(
                years=years,
                progress_callback=progress_callback,
                log_callback=log_callback
            )

    async def _scrape_years_sequential(
        self,
        years: List[int],
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None
    ) -> ScrapeResult:
        """Scrape years sequentially (original behavior)."""
        start_time = time.time()
        self._should_stop = False

        total_listings = 0
        total_new = 0
        total_updated = 0
        total_errors = 0

        log = log_callback or (lambda msg: print(msg))
        progress = progress_callback or (lambda c, t, m: None)

        log(f"Starting SEQUENTIAL scraping for {len(years)} years")

        for idx, year in enumerate(years, 1):
            if self._should_stop:
                log("Scraping stopped by user")
                break

            progress(idx, len(years), f"Scraping year {year}")
            log(f"[{idx}/{len(years)}] Scraping year {year}...")

            try:
                result = await self.scrape_year(
                    year=year,
                    log_callback=log
                )

                total_listings += result.total_listings
                total_new += result.new_listings
                total_updated += result.updated_listings
                total_errors += result.errors

                log(f"Year {year} completed: {result.total_listings} listings, {result.new_listings} new")

            except Exception as e:
                log(f"ERROR scraping year {year}: {e}")
                total_errors += 1

            # Small delay between years
            if idx < len(years):
                await asyncio.sleep(2)

        duration = time.time() - start_time

        log(f"Scraping completed in {duration:.1f}s")
        log(f"Total: {total_listings} listings ({total_new} new, {total_updated} updated)")

        return ScrapeResult(
            total_listings=total_listings,
            new_listings=total_new,
            updated_listings=total_updated,
            errors=total_errors,
            duration=duration
        )

    async def _scrape_years_parallel(
        self,
        years: List[int],
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
        max_workers: int = 2
    ) -> ScrapeResult:
        """
        Scrape years in parallel using asyncio semaphore.

        Features:
        - True parallelism with async httpx
        - Thread-safe progress tracking
        - Automatic resource cleanup

        Args:
            years: List of years to scrape
            progress_callback: Optional callback for progress updates
            log_callback: Optional callback for log messages
            max_workers: Maximum concurrent year scrapers

        Returns:
            ScrapeResult with aggregated statistics
        """
        start_time = time.time()
        self._should_stop = False

        log = log_callback or (lambda msg: print(msg))
        progress = progress_callback or (lambda c, t, m: None)

        log(f"Starting PARALLEL scraping for {len(years)} years (max {max_workers} workers)")

        # Semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_workers)

        # Thread-safe progress counter
        completed_lock = asyncio.Lock()
        completed_count = 0

        async def scrape_year_with_semaphore(year: int) -> ScrapeResult:
            nonlocal completed_count

            async with semaphore:
                if self._should_stop:
                    return ScrapeResult()

                # Create year-specific logger
                def year_log(msg: str):
                    log(f"[{year}] {msg}")

                year_log(f"Starting year {year}...")

                try:
                    # Use async=True for true parallelism (non-blocking HTTP)
                    result = await self.scrape_year(
                        year=year,
                        log_callback=year_log,
                        use_async=True  # Enable async httpx for parallel mode
                    )

                    # Thread-safe counter increment
                    async with completed_lock:
                        completed_count += 1
                        current = completed_count
                    progress(current, len(years), f"Completed {current}/{len(years)} years")
                    year_log(f"Completed: {result.total_listings} listings, {result.new_listings} new")

                    return result

                except Exception as e:
                    year_log(f"ERROR: {e}")
                    # Thread-safe counter increment on error
                    async with completed_lock:
                        completed_count += 1
                    return ScrapeResult(errors=1)

        try:
            # Create tasks for all years
            tasks = [scrape_year_with_semaphore(year) for year in years]

            # Run all tasks concurrently (limited by semaphore)
            results = await asyncio.gather(*tasks)

            # Aggregate results
            total_listings = sum(r.total_listings for r in results)
            total_new = sum(r.new_listings for r in results)
            total_updated = sum(r.updated_listings for r in results)
            total_errors = sum(r.errors for r in results)

            duration = time.time() - start_time

            log(f"PARALLEL scraping completed in {duration:.1f}s")
            log(f"Total: {total_listings} listings ({total_new} new, {total_updated} updated)")
            log(f"Speed improvement: ~{len(years)/max_workers:.1f}x faster than sequential")

            return ScrapeResult(
                total_listings=total_listings,
                new_listings=total_new,
                updated_listings=total_updated,
                errors=total_errors,
                duration=duration
            )

        finally:
            # Cleanup: close async client to release resources
            await self._close_async_client()
            log("Resources cleaned up")

    async def scrape_year_parallel_pages(
        self,
        year: int,
        log_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        max_workers: int = 3,
        batch_size: int = 50  # Save to Supabase every N pages (increased to reduce DB load)
    ) -> ScrapeResult:
        """
        Scrape ALL pages of a year with parallel page fetching.

        Scrapes all pages of the year, saving to Supabase every batch_size pages
        to balance memory usage and database efficiency.

        Flow:
        1. Fetch page 1 to get total pages
        2. Fetch pages in batches of batch_size (parallel within batch)
        3. Save each batch to Supabase
        4. Continue until all pages are scraped

        Args:
            year: Year to scrape
            log_callback: Optional callback for log messages
            progress_callback: Optional callback for progress updates (current, total, message)
            max_workers: Number of concurrent page fetchers (2-5 recommended)
            batch_size: Number of pages to accumulate before saving (default 20)

        Returns:
            ScrapeResult with statistics
        """
        start_time = time.time()
        log = log_callback or (lambda msg: print(msg))
        progress = progress_callback or (lambda c, t, m: None)

        total_listings = 0
        new_count = 0
        updated_count = 0
        error_count = 0
        pages_processed = 0

        log(f"  Starting PARALLEL PAGES mode for year {year} (max {max_workers} workers, batch every {batch_size} pages)")

        # Step 1: Fetch first page to get pagination info
        try:
            url_page1 = self._build_url(year, 1)
            log(f"  Page 1: {url_page1}")

            html_page1 = await self._fetch_with_headlessx_async(url_page1, log)

            # Get pagination info - NO LIMIT, scrape ALL pages
            pagination = self.parser.get_pagination_info(html_page1)
            total_pages = pagination.get('total_pages', 1) or 1

            log(f"    Total pages detected: {total_pages} (will scrape ALL)")

            # Update progress with total pages known
            pages_processed = 1
            progress(pages_processed, total_pages, f"Year {year}: page 1/{total_pages}")

            # Parse page 1 listings
            listings_page1 = self.parser.parse(html_page1)
            batch_listings = []  # Accumulate listings for current batch

            if listings_page1:
                log(f"    Page 1: {len(listings_page1)} listings")
                batch_listings.extend(listings_page1)
            else:
                log(f"    Page 1: No listings found")
                return ScrapeResult(
                    total_listings=0,
                    new_listings=0,
                    updated_listings=0,
                    errors=0,
                    duration=time.time() - start_time
                )

            # If only 1 page, save and we're done
            if total_pages <= 1:
                log(f"  Only 1 page, saving {len(batch_listings)} listings...")
                saved, _ = await self._save_listings(batch_listings, log)
                return ScrapeResult(
                    total_listings=len(batch_listings),
                    new_listings=saved,
                    updated_listings=0,
                    errors=0,
                    duration=time.time() - start_time
                )

        except Exception as e:
            log(f"  ERROR fetching page 1: {e}")
            return ScrapeResult(errors=1, duration=time.time() - start_time)

        # Step 2: Process remaining pages in batches
        remaining_pages = list(range(2, total_pages + 1))
        pages_in_current_batch = 1  # Page 1 already fetched
        batch_number = 1

        semaphore = asyncio.Semaphore(max_workers)

        async def fetch_page(page_num: int) -> tuple[int, List, Optional[str]]:
            """Fetch a single page and return (page_num, listings, error)."""
            async with semaphore:
                if self._should_stop:
                    return page_num, [], "Stopped by user"

                try:
                    url = self._build_url(year, page_num)
                    html = await self._fetch_with_headlessx_async(url, lambda m: None)
                    listings = self.parser.parse(html)
                    log(f"    [Worker] Page {page_num}/{total_pages}: {len(listings) if listings else 0} listings")
                    return page_num, listings or [], None

                except Exception as e:
                    log(f"    [Worker] Page {page_num}: ERROR - {e}")
                    return page_num, [], str(e)

        # Process pages in chunks of batch_size
        for i in range(0, len(remaining_pages), batch_size - 1):  # -1 because page 1 counts
            if self._should_stop:
                log("  Scraping stopped by user")
                break

            # Get chunk of pages to fetch
            chunk_pages = remaining_pages[i:i + batch_size - 1] if i == 0 else remaining_pages[i:i + batch_size]

            if not chunk_pages:
                break

            log(f"  Batch {batch_number}: fetching pages {chunk_pages[0]}-{chunk_pages[-1]}...")

            # Fetch chunk in parallel
            tasks = [fetch_page(page) for page in chunk_pages]
            page_results = await asyncio.gather(*tasks)

            # Accumulate results
            for page_num, listings, error in sorted(page_results, key=lambda x: x[0]):
                if error:
                    error_count += 1
                elif listings:
                    batch_listings.extend(listings)

            pages_in_current_batch += len(chunk_pages)
            pages_processed += len(chunk_pages)

            # Update progress after each chunk
            progress(pages_processed, total_pages, f"Year {year}: page {pages_processed}/{total_pages}")

            # Save batch when we reach batch_size pages
            if pages_in_current_batch >= batch_size or (i + batch_size >= len(remaining_pages)):
                if batch_listings:
                    log(f"  Batch {batch_number}: saving {len(batch_listings)} listings to Supabase...")
                    saved, _ = await self._save_listings(batch_listings, log)
                    total_listings += len(batch_listings)
                    new_count += saved
                    log(f"  Batch {batch_number}: {saved} new/updated")
                    batch_listings = []  # Clear for next batch
                    pages_in_current_batch = 0
                    batch_number += 1

        # Save any remaining listings
        if batch_listings:
            log(f"  Final batch: saving {len(batch_listings)} remaining listings...")
            saved, _ = await self._save_listings(batch_listings, log)
            total_listings += len(batch_listings)
            new_count += saved

        duration = time.time() - start_time

        log(f"  Year {year} completed: {total_listings} listings, {new_count} saved, {error_count} errors, {duration:.1f}s")

        return ScrapeResult(
            total_listings=total_listings,
            new_listings=new_count,
            updated_listings=updated_count,
            errors=error_count,
            duration=duration
        )

    async def scrape_years_sequential_parallel_pages(
        self,
        years: List[int],
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None,
        max_workers: int = 3
    ) -> ScrapeResult:
        """
        Scrape years SEQUENTIALLY but with PARALLEL page fetching within each year.

        This is a hybrid mode:
        - Years are processed one at a time (sequential)
        - Pages within each year are fetched in parallel (faster)

        Best of both worlds:
        - More controlled than full parallel (years one at a time)
        - Faster than full sequential (pages in parallel)

        Args:
            years: List of years to scrape
            progress_callback: Callback for progress updates
            log_callback: Callback for log messages
            max_workers: Number of concurrent page fetchers per year

        Returns:
            ScrapeResult with aggregated statistics
        """
        start_time = time.time()
        self._should_stop = False

        total_listings = 0
        total_new = 0
        total_updated = 0
        total_errors = 0

        log = log_callback or (lambda msg: print(msg))
        progress = progress_callback or (lambda c, t, m: None)

        log(f"Starting SEQUENTIAL (years) + PARALLEL (pages) mode")
        log(f"Years: {len(years)}, Workers per year: {max_workers}")

        for idx, year in enumerate(years, 1):
            if self._should_stop:
                log("Scraping stopped by user")
                break

            progress(idx, len(years), f"Scraping year {year} ({idx}/{len(years)})")
            log(f"\n[{idx}/{len(years)}] Year {year}")
            log("=" * 50)

            try:
                result = await self.scrape_year_parallel_pages(
                    year=year,
                    log_callback=log,
                    progress_callback=progress,
                    max_workers=max_workers
                )

                total_listings += result.total_listings
                total_new += result.new_listings
                total_updated += result.updated_listings
                total_errors += result.errors

                log(f"Year {year} done: {result.total_listings} listings in {result.duration:.1f}s")

            except Exception as e:
                log(f"ERROR on year {year}: {e}")
                total_errors += 1

            # Small delay between years
            if idx < len(years):
                await asyncio.sleep(2)

        duration = time.time() - start_time

        log(f"\n{'=' * 50}")
        log(f"COMPLETED: {len(years)} years in {duration:.1f}s")
        log(f"Total: {total_listings} listings ({total_new} saved)")
        log(f"Errors: {total_errors}")

        # Cleanup
        await self._close_async_client()

        return ScrapeResult(
            total_listings=total_listings,
            new_listings=total_new,
            updated_listings=total_updated,
            errors=total_errors,
            duration=duration
        )

    async def scrape_year(
        self,
        year: int,
        max_pages: int = 1000,
        log_callback: Optional[Callable] = None,
        use_async: bool = False
    ) -> ScrapeResult:
        """
        Scrape all listings for a specific year.

        Args:
            year: Year to scrape (e.g., 2024)
            max_pages: Maximum number of pages to scrape (default 1000 = essentially unlimited)
            log_callback: Optional callback for log messages
            use_async: If True, use async httpx for true parallelism

        Returns:
            ScrapeResult with statistics
        """
        start_time = time.time()
        log = log_callback or (lambda msg: print(msg))

        total_listings = 0
        new_count = 0
        updated_count = 0
        error_count = 0

        page = 1

        while page <= max_pages:
            if self._should_stop:
                break

            try:
                url = self._build_url(year, page)
                log(f"  Page {page}: {url}")

                # Fetch HTML using HeadlessX (required for bypassing anti-bot)
                # Use async version for true parallelism when in parallel mode
                if use_async:
                    html = await self._fetch_with_headlessx_async(url, log)
                else:
                    html = self._fetch_with_headlessx(url, log)

                # Get pagination info on first page
                if page == 1:
                    pagination = self.parser.get_pagination_info(html)
                    if pagination['total_pages']:
                        log(f"    Pagination: page {pagination['current_page']}/{pagination['total_pages']} ({pagination['total_items']} total items)")

                # Parse listings
                listings = self.parser.parse(html)

                if not listings:
                    log(f"  No listings found on page {page}, stopping")
                    break

                log(f"  Found {len(listings)} listings on page {page}")

                # Log parsing confidence stats
                confidences = [
                    l.extra_fields.get('parsing_confidence', 0)
                    for l in listings if l.extra_fields
                ]
                if confidences:
                    avg_conf = sum(confidences) / len(confidences)
                    perfect = sum(1 for c in confidences if c == 1.0)
                    log(f"    Parsing confidence: {avg_conf:.2f} ({perfect}/{len(confidences)} perfectos)")

                # Log unique marcas found
                marcas = set(l.marca for l in listings if l.marca)
                if marcas:
                    log(f"    Marcas: {', '.join(sorted(marcas)[:5])}{'...' if len(marcas) > 5 else ''}")

                # Save to database
                saved_new, saved_updated = await self._save_listings(listings, log)
                new_count += saved_new
                updated_count += saved_updated
                total_listings += len(listings)

                # Check if has next page
                has_next = self.parser.has_next_page(html, page)

                if not has_next:
                    log(f"  No more pages after page {page}")
                    break

                page += 1

                # Delay between pages
                await asyncio.sleep(1)

            except Exception as e:
                log(f"  ERROR on page {page}: {e}")
                error_count += 1

                if error_count > 5:
                    log(f"  Too many errors, stopping year {year}")
                    break

                page += 1

        duration = time.time() - start_time

        return ScrapeResult(
            total_listings=total_listings,
            new_listings=new_count,
            updated_listings=updated_count,
            errors=error_count,
            duration=duration
        )

    def _build_url(self, year: int, page: int = 1) -> str:
        """
        Build URL for year and page.

        Note: Using "citronen" (misspelled) redirects to general page with ALL marcas.
        This is a workaround to scrape all brands without filtering.
        URL pattern: https://www.coches.net/citronen/segunda-mano/{year}/?pg={page}
        """
        # Use misspelled "citronen" to get ALL brands (redirects to general page)
        base = f"https://www.coches.net/citronen/segunda-mano/{year}/"

        if page > 1:
            return f"{base}?pg={page}"

        return base

    def _listing_to_dict(self, listing) -> dict:
        """Convert a CarListing to database dict (shared helper)."""
        data = {
            'ad_id': listing.ad_id,
            'url': listing.url,
            'title': listing.title,
            'marca': listing.marca,
            'modelo': listing.modelo,
            'year': listing.year,
            'kilometers': listing.kilometers,
            'fuel': listing.fuel,
            'power': listing.power_cv,  # Table uses 'power' not 'power_cv'
            'price': listing.price,
            'location': listing.location,
            'scraped_at': datetime.now().isoformat(),
        }

        # Add transmission from listing if available
        if listing.transmission:
            data['transmission'] = listing.transmission

        # Add optional fields only if they have values
        optional_fields = [
            'version',
            'parsing_confidence',
            'parsing_method',
            'marca_normalizada',
            'modelo_completo',
            'modelo_variante',
            'transmission',
            'combustible_normalizado'
        ]
        if listing.extra_fields:
            for field in optional_fields:
                if field in listing.extra_fields and listing.extra_fields[field]:
                    data[field] = listing.extra_fields[field]

        return data

    async def _save_listings(
        self,
        listings: List,
        log_callback: Optional[Callable] = None,
        batch_size: int = 100,  # Increased from 50 to reduce DB calls
        delay_between_batches: float = 0.3  # Delay to avoid saturating Supabase
    ) -> tuple[int, int]:
        """
        Save listings to database using batch upsert.

        Features:
        - Batch upsert (default 50 records per batch)
        - Much faster than one-by-one inserts
        - Automatic retry on batch failure with fallback to individual inserts

        Args:
            listings: List of CarListing objects
            log_callback: Optional callback for log messages
            batch_size: Number of records per batch (default 50)

        Returns:
            Tuple of (new_count, updated_count)
        """
        log = log_callback or (lambda msg: print(msg))

        if not listings:
            return 0, 0

        log(f"    Guardando {len(listings)} listings en DB (batch size: {batch_size})...")

        # Convert all listings to dicts
        records = []
        for listing in listings:
            try:
                data = self._listing_to_dict(listing)
                records.append(data)
            except Exception as e:
                log(f"      [SKIP] {listing.ad_id}: Error converting: {e}")

        if not records:
            return 0, 0

        saved_count = 0
        error_count = 0

        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(records) + batch_size - 1) // batch_size

            try:
                # Batch upsert - MUCH faster than individual inserts
                result = self.supabase.client.table('cochesnet')\
                    .upsert(batch, on_conflict='ad_id')\
                    .execute()

                saved_count += len(batch)
                log(f"      [BATCH {batch_num}/{total_batches}] {len(batch)} records guardados")

                # Delay between batches to avoid saturating Supabase
                if batch_num < total_batches and delay_between_batches > 0:
                    await asyncio.sleep(delay_between_batches)

            except Exception as e:
                log(f"      [BATCH {batch_num} ERROR] {e}")
                log(f"      Retrying batch individually...")

                # Fallback: try inserting individually
                for record in batch:
                    try:
                        self.supabase.client.table('cochesnet')\
                            .upsert(record, on_conflict='ad_id')\
                            .execute()
                        saved_count += 1
                    except Exception as e2:
                        error_count += 1
                        log(f"        [ERROR] {record.get('ad_id')}: {e2}")

        log(f"    DB: {saved_count} guardados, {error_count} errores")

        return saved_count, 0  # Supabase upsert doesn't distinguish new vs updated

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from database.

        Returns:
            Dict with statistics
        """
        try:
            # Total count
            result = self.supabase.client.table('cochesnet')\
                .select('count', count='exact')\
                .execute()

            total_listings = result.count or 0

            # By year
            year_result = self.supabase.client.table('cochesnet')\
                .select('year')\
                .execute()

            by_year = {}
            for row in year_result.data:
                year = row.get('year')
                if year:
                    by_year[year] = by_year.get(year, 0) + 1

            # Confidence stats (if available)
            confidence_result = self.supabase.client.table('cochesnet')\
                .select('parsing_confidence')\
                .execute()

            confidences = [
                row.get('parsing_confidence', 0)
                for row in confidence_result.data
                if row.get('parsing_confidence') is not None
            ]

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            perfect_matches = sum(1 for c in confidences if c == 1.0)
            perfect_pct = (perfect_matches / len(confidences) * 100) if confidences else 0

            return {
                'total_listings': total_listings,
                'by_year': by_year,
                'avg_confidence': avg_confidence,
                'perfect_matches': perfect_matches,
                'perfect_pct': perfect_pct
            }

        except Exception as e:
            return {
                'error': str(e),
                'total_listings': 0,
                'by_year': {},
                'avg_confidence': 0,
                'perfect_matches': 0,
                'perfect_pct': 0
            }

    def export_data(self, filename: str, format: str = 'csv'):
        """
        Export data to file.

        Args:
            filename: Output filename
            format: Export format ('csv', 'json', 'excel')
        """
        # Fetch all data
        result = self.supabase.client.table('cochesnet')\
            .select('*')\
            .execute()

        data = result.data

        if format == 'csv':
            import csv

            if not data:
                raise ValueError("No data to export")

            keys = data[0].keys()

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)

        elif format == 'json':
            import json

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif format == 'excel':
            try:
                import pandas as pd
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False)
            except ImportError:
                raise ImportError("pandas and openpyxl required for Excel export")

        else:
            raise ValueError(f"Unknown format: {format}")

    # BaseAgent abstract methods implementation
    def can_handle(self, task: str) -> bool:
        """Check if this agent can handle the task."""
        keywords = ['cochesnet', 'coches.net', 'scrape year', 'scrape years']
        return any(keyword in task.lower() for keyword in keywords)

    async def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a scraping task."""
        # Parse years from task or context
        years = []
        if context and 'years' in context:
            years = context['years']
        else:
            # Try to extract years from task string
            import re
            year_matches = re.findall(r'\b(20\d{2})\b', task)
            years = [int(y) for y in year_matches]

        if not years:
            return {
                'success': False,
                'error': 'No years specified in task or context'
            }

        # Execute scraping
        result = await self.scrape_years(years)

        return {
            'success': True,
            'result': {
                'total_listings': result.total_listings,
                'new_listings': result.new_listings,
                'updated_listings': result.updated_listings,
                'errors': result.errors,
                'duration': result.duration
            }
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            'name': 'cochesnet-scraper',
            'description': 'Scrapes car listings from Coches.net by year',
            'supported_years': list(range(2007, 2026)),
            'features': [
                'Year-based scraping',
                'Multi-year batch scraping',
                'Progress tracking',
                'Database integration',
                'Title parsing with confidence scoring'
            ],
            'url_pattern': 'https://www.coches.net/coches-segunda-mano/?year=<year>&pg=<page>'
        }
