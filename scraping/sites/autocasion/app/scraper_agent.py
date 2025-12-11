"""Runtime agent for Autocasion scraping operations with HeadlessX integration."""

import asyncio
import time
import random
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, replace

import requests
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from agents.base_agent import BaseAgent, AgentCapability, AgentResponse
from scraping.sites.autocasion.parser import AutocasionParser
from scraping.sites.autocasion.site import AutocasionSite
from scraping.storage.supabase_client import get_supabase_client, SupabaseClient
from scraping.sites.autocasion.app.headlessx_client import (
    HeadlessXClient,
    HeadlessXConfig,
    RenderResult,
    get_headlessx_client
)


@dataclass
class ScrapeResult:
    """Result from a scraping operation."""
    marca: str
    total_listings: int
    pages_scraped: int
    saved_to_db: int
    errors: List[str]
    duration_seconds: float
    method_used: str = "unknown"  # "headlessx", "headlessx_stealth", "requests"


class AutocasionScraperAgent(BaseAgent):
    """
    Runtime agent for scraping Autocasion.com.

    Integrates with the orchestrator system and provides:
    - Single brand scraping
    - Multi-brand batch scraping
    - Objetivo-based scraping (from Supabase)
    - Progress tracking and error handling
    - Profile rotation between brands

    Uses HeadlessX for anti-detection when available:
    - Full fingerprint spoofing (Canvas, WebGL, Audio, WebRTC)
    - Behavioral simulation (mouse, keyboard, scroll)
    - WAF bypass (Cloudflare, DataDome)
    - Device/Geo profiles for realistic sessions
    """

    # Available profiles for rotation
    DEVICE_PROFILES = [
        "high-end-desktop", "mid-range-desktop", "low-end-desktop",
        "high-end-laptop", "mid-range-laptop", "macbook-pro", "macbook-air"
    ]
    GEO_PROFILES = ["spain", "us-east", "us-west", "uk", "germany", "france"]
    BEHAVIOR_PROFILES = ["natural", "cautious", "confident"]

    def __init__(self):
        super().__init__(
            name="autocasion-scraper",
            description="Scrapes car listings from Autocasion.com with anti-detection"
        )
        self.site = AutocasionSite()
        self.parser = AutocasionParser()
        self._supabase: Optional[SupabaseClient] = None
        self._session: Optional[requests.Session] = None
        self._headlessx: Optional[HeadlessXClient] = None
        self._current_profile_index = 0
        self._should_stop = False
        self._async_client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._request_lock = asyncio.Lock()

        # HeadlessX base configuration optimized for Autocasion
        self._headlessx_config = HeadlessXConfig(
            timeout=60000,
            extra_wait_time=3000,
            wait_until="networkidle",
            device_profile="mid-range-desktop",
            geo_profile="spain",
            behavior_profile="natural",
            enable_canvas_spoofing=True,
            enable_webgl_spoofing=True,
            enable_audio_spoofing=True,
            enable_webrtc_blocking=True,
            enable_advanced_stealth=True,
            simulate_mouse_movement=True,
            simulate_scrolling=True,
            human_delays=True,
            randomize_timings=True,
            scroll_to_bottom=True,
            remove_elements=[".cookie-banner", ".popup", ".modal"]
        )

    def _rotate_profile(self) -> HeadlessXConfig:
        """
        Rotate to a new random profile for anti-detection.
        Returns a new HeadlessXConfig with different device/geo/behavior profiles.
        """
        device = random.choice(self.DEVICE_PROFILES)
        geo = random.choice(self.GEO_PROFILES)
        behavior = random.choice(self.BEHAVIOR_PROFILES)

        new_config = replace(
            self._headlessx_config,
            device_profile=device,
            geo_profile=geo,
            behavior_profile=behavior
        )

        return new_config

    def _get_current_profile_info(self, config: HeadlessXConfig) -> str:
        """Get human-readable profile info."""
        return f"{config.device_profile} | {config.geo_profile} | {config.behavior_profile}"

    @property
    def supabase(self) -> SupabaseClient:
        """Lazy initialization of Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    @property
    def headlessx(self) -> HeadlessXClient:
        """Lazy initialization of HeadlessX client."""
        if self._headlessx is None:
            self._headlessx = get_headlessx_client()
        return self._headlessx

    @property
    def session(self) -> requests.Session:
        """Lazy initialization of requests session (fallback)."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })
        return self._session

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="scrape_autocasion",
                description="Scrape car listings from Autocasion.com with anti-detection",
                keywords=["autocasion", "scrape", "cars", "listings", "coches"],
                priority=10
            ),
            AgentCapability(
                name="batch_scrape",
                description="Batch scrape multiple brands from Autocasion",
                keywords=["batch", "multiple", "brands", "marcas"],
                priority=8
            ),
            AgentCapability(
                name="stealth_scrape",
                description="Scrape with maximum stealth for blocked sites",
                keywords=["stealth", "cloudflare", "bypass", "blocked"],
                priority=9
            ),
        ]

    def can_handle(self, task: str, context: Optional[Dict[str, Any]] = None) -> float:
        """Score how well this agent can handle the task."""
        task_lower = task.lower()
        score = 0.0

        # High confidence for autocasion-specific tasks
        if "autocasion" in task_lower:
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

        # Determine what to scrape
        marca = context.get("marca")
        marcas = context.get("marcas", [])
        max_pages = context.get("max_pages", 5)
        save_to_db = context.get("save_to_db", True)
        stealth = context.get("stealth", False)

        if marca:
            result = await self.scrape_marca(marca, max_pages, save_to_db, stealth)
            return AgentResponse(
                success=len(result.errors) == 0,
                result=result,
                message=f"Scraped {result.total_listings} listings from {marca} using {result.method_used}",
                metadata={"marca": marca, "pages": result.pages_scraped, "method": result.method_used}
            )
        elif marcas:
            results = await self.scrape_batch(marcas, max_pages, save_to_db, stealth)
            total = sum(r.total_listings for r in results)
            return AgentResponse(
                success=True,
                result=results,
                message=f"Batch scraped {total} listings from {len(marcas)} brands",
                metadata={"brands": len(marcas), "total_listings": total}
            )
        else:
            results = await self.scrape_from_objetivos(max_pages=max_pages, stealth=stealth)
            total = sum(r.total_listings for r in results)
            return AgentResponse(
                success=True,
                result=results,
                message=f"Scraped {total} listings from objetivos",
                metadata={"brands_scraped": len(results)}
            )

    def _fetch_with_headlessx(
        self,
        url: str,
        stealth: bool = False,
        config: Optional[HeadlessXConfig] = None
    ) -> tuple[Optional[str], str]:
        """
        Fetch page using HeadlessX with full anti-detection.

        Args:
            url: URL to fetch
            stealth: Use stealth mode
            config: Optional custom config (for profile rotation)

        Returns:
            Tuple of (html, method_used)
        """
        use_config = config or self._headlessx_config

        if stealth:
            print(f"  Using HeadlessX STEALTH mode...")
            result = self.headlessx.render_stealth(url, use_config)
            method = "headlessx_stealth"
        else:
            print(f"  Using HeadlessX...")
            result = self.headlessx.render(url, use_config)
            method = "headlessx"

        if result.success and result.html:
            print(f"    Response: {result.content_length} bytes in {result.response_time_ms:.0f}ms")
            if result.was_timeout:
                print(f"    Warning: Response was partial (timeout)")
            return result.html, method

        if result.error:
            print(f"    HeadlessX error: {result.error}")

        return None, method

    def _fetch_with_requests(self, url: str) -> Optional[str]:
        """Fetch page using standard requests (fallback)."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"    Requests error: {e}")
        return None

    def _fetch_page(
        self,
        url: str,
        stealth: bool = False,
        config: Optional[HeadlessXConfig] = None
    ) -> tuple[Optional[str], str]:
        """
        Fetch a page with automatic fallback.

        Priority:
        1. HeadlessX (stealth mode if requested)
        2. HeadlessX (normal mode)
        3. Requests (may be blocked)

        Args:
            url: URL to fetch
            stealth: Use stealth mode
            config: Optional custom config (for profile rotation)

        Returns:
            Tuple of (html, method_used)
        """
        method_used = "none"

        # Check HeadlessX availability
        if self.headlessx.is_available():
            # Try HeadlessX with rotated profile
            html, method_used = self._fetch_with_headlessx(url, stealth, config)

            if html:
                # Verify not blocked
                is_blocked, block_type, _ = self.site.detect_block(html)
                if not is_blocked:
                    return html, method_used
                print(f"    Page blocked ({block_type}), trying stealth...")

                # If blocked with normal mode, try stealth
                if not stealth:
                    html, method_used = self._fetch_with_headlessx(url, stealth=True, config=config)
                    if html:
                        is_blocked, block_type, _ = self.site.detect_block(html)
                        if not is_blocked:
                            return html, method_used
                        print(f"    Still blocked after stealth: {block_type}")
        else:
            print(f"  HeadlessX not available")

        # Fallback to requests
        print(f"  Falling back to requests...")
        html = self._fetch_with_requests(url)
        method_used = "requests"

        if html:
            is_blocked, block_type, _ = self.site.detect_block(html)
            if not is_blocked:
                return html, method_used
            print(f"    Blocked by {block_type}")
            return None, method_used

        return None, method_used

    async def scrape_marca(
        self,
        marca: str,
        max_pages: int = 10,
        save_to_db: bool = True,
        stealth: bool = False,
        log_callback: Optional[callable] = None
    ) -> ScrapeResult:
        """
        Scrape all listings for a single brand.

        Args:
            marca: Brand slug (e.g., "audi", "bmw")
            max_pages: Maximum pages to scrape (0 = ALL pages)
            save_to_db: Whether to save to Supabase
            stealth: Use maximum stealth mode
            log_callback: Optional callback function for GUI logging

        Returns:
            ScrapeResult with statistics
        """
        def log(msg: str):
            """Log to both console and callback if provided."""
            print(msg)
            if log_callback:
                log_callback(msg)

        start_time = time.time()
        all_listings = []
        errors = []
        pages_scraped = 0
        saved = 0
        method_used = "none"
        all_pages_mode = (max_pages == 0)
        detected_total_pages = None

        # Rotate profile for this brand
        current_config = self._rotate_profile()
        profile_info = self._get_current_profile_info(current_config)

        log(f"\n{'='*60}")
        log(f"[AutocasionScraper] Starting scrape for: {marca.upper()}")
        log(f"  Profile: {profile_info}")
        if all_pages_mode:
            log(f"  Mode: ALL PAGES (auto-detect)")
        else:
            log(f"  Max pages: {max_pages}")
        log(f"{'='*60}")

        # Report HeadlessX status
        if self.headlessx.is_available():
            status = self.headlessx.get_status()
            if status:
                log(f"  HeadlessX v{status.get('version', '?')} ready")
                log(f"  Stealth mode: {'ENABLED' if stealth else 'auto'}")
        else:
            log(f"  WARNING: HeadlessX not available")
            log(f"  Using requests (may be blocked by Cloudflare)")

        page = 1
        consecutive_empty_pages = 0  # Track empty pages to detect end
        while True:
            # Check page limit BEFORE fetching
            if not all_pages_mode and page > max_pages:
                log(f"  Reached max pages limit ({max_pages})")
                break
            # Check against detected total - stop if we exceed it
            if detected_total_pages and page > detected_total_pages:
                log(f"  Page {page} exceeds detected total ({detected_total_pages}), stopping")
                break

            url = self.site.build_search_url(marca, page=page)

            # Display progress
            if detected_total_pages:
                log(f"\n  Page {page}/{detected_total_pages}: {url}")
            elif all_pages_mode:
                log(f"\n  Page {page}/?: {url}")
            else:
                log(f"\n  Page {page}/{max_pages}: {url}")

            html, method_used = self._fetch_page(url, stealth, current_config)
            if not html:
                log(f"  ERROR: Failed to fetch page {page}")
                errors.append(f"Failed to fetch page {page}")
                break

            # On first page, detect total pages if in all_pages_mode
            if page == 1 and all_pages_mode:
                detected_total_pages = self.parser.get_total_pages(html)
                total_count = self.parser.get_total_count(html)
                if total_count:
                    log(f"  Total listings detected: {total_count}")
                    log(f"  Estimated pages: {detected_total_pages}")

            # Parse listings
            listings = self.parser.parse(html)
            if not listings:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 2:
                    log(f"  No listings found on page {page} (2 consecutive empty pages), stopping")
                    break
                log(f"  No listings found on page {page}, trying next page...")
                page += 1
                continue

            # Reset empty counter when we find listings
            consecutive_empty_pages = 0

            # Set source and URL for each listing
            for listing in listings:
                listing.source = "autocasion"
                if not listing.url:
                    listing.url = url

            all_listings.extend(listings)
            pages_scraped += 1
            log(f"  Found {len(listings)} listings (total: {len(all_listings)})")

            # Save page to database immediately (don't wait until end)
            if save_to_db and listings:
                try:
                    stats = self.supabase.save_listings(listings)
                    page_saved = stats.get("autocasion", 0)
                    saved += page_saved
                    log(f"  Saved {page_saved} to Supabase (total saved: {saved})")
                except Exception as e:
                    log(f"  DB error on page {page}: {e}")
                    errors.append(f"DB error page {page}: {e}")

            # Check for next page using multiple methods
            has_next = self.parser.has_next_page(html, page)
            next_url = self.parser.get_next_page_url(html)

            # Also check if we've reached or exceeded detected total
            if detected_total_pages and page >= detected_total_pages:
                log(f"  Reached detected last page ({detected_total_pages})")
                break

            if not next_url or not has_next:
                log(f"  No more pages available")
                break

            page += 1

            # Delay between pages (human-like)
            delay = self.site.config.delay_between_pages
            log(f"  Waiting {delay}s...")
            await asyncio.sleep(delay)

        # Final summary and update objetivo status
        if save_to_db and all_listings:
            log(f"\n  Total saved to Supabase: {saved}")
            try:
                duration = time.time() - start_time
                self.supabase.update_objetivo_status(
                    source="autocasion",
                    marca=marca,
                    status="completed" if not errors else "partial",
                    cars_scraped=len(all_listings),
                    pages_scraped=pages_scraped,
                    duration_seconds=duration
                )
            except Exception as e:
                errors.append(f"Objetivo update error: {e}")
                log(f"  Objetivo update error: {e}")

        duration = time.time() - start_time

        log(f"\n{'='*60}")
        log(f"  COMPLETED: {marca.upper()}")
        log(f"  Listings: {len(all_listings)} | Pages: {pages_scraped} | Time: {duration:.1f}s")
        log(f"  Method: {method_used} | Profile: {profile_info}")
        if errors:
            log(f"  Errors: {len(errors)}")
        log(f"{'='*60}")

        return ScrapeResult(
            marca=marca,
            total_listings=len(all_listings),
            pages_scraped=pages_scraped,
            saved_to_db=saved,
            errors=errors,
            duration_seconds=duration,
            method_used=method_used
        )

    async def scrape_batch(
        self,
        marcas: List[str],
        max_pages: int = 5,
        save_to_db: bool = True,
        stealth: bool = False
    ) -> List[ScrapeResult]:
        """Scrape multiple brands sequentially."""
        results = []

        print(f"\n{'#'*60}")
        print(f"# BATCH SCRAPE: {len(marcas)} brands")
        print(f"# Brands: {', '.join(marcas)}")
        print(f"# Max pages per brand: {max_pages}")
        print(f"{'#'*60}")

        for i, marca in enumerate(marcas, 1):
            print(f"\n[{i}/{len(marcas)}] Processing {marca}...")
            result = await self.scrape_marca(marca, max_pages, save_to_db, stealth)
            results.append(result)

            # Delay between brands
            if i < len(marcas):
                delay = self.site.config.delay_between_requests
                print(f"  Waiting {delay}s before next brand...")
                await asyncio.sleep(delay)

        # Summary
        total_listings = sum(r.total_listings for r in results)
        total_saved = sum(r.saved_to_db for r in results)
        total_errors = sum(len(r.errors) for r in results)

        print(f"\n{'#'*60}")
        print(f"# BATCH COMPLETE")
        print(f"# Total listings: {total_listings}")
        print(f"# Total saved: {total_saved}")
        print(f"# Total errors: {total_errors}")
        print(f"{'#'*60}")

        return results

    async def scrape_from_objetivos(
        self,
        limit: int = 10,
        max_pages: int = 5,
        stealth: bool = False
    ) -> List[ScrapeResult]:
        """
        Scrape brands from the objetivo_autocasion table.

        Prioritizes by prioridad field and scraping_attempts.
        """
        print(f"\nFetching pending objetivos from Supabase...")
        objetivos = self.supabase.get_pending_objetivos("autocasion", limit)

        if not objetivos:
            print("No pending objetivos found")
            return []

        marcas = [obj["marca"] for obj in objetivos]
        print(f"Found {len(marcas)} pending objetivos: {marcas}")

        return await self.scrape_batch(marcas, max_pages, stealth=stealth)

    def get_stats(self) -> Dict[str, Any]:
        """Get current scraping statistics."""
        stats = self.supabase.get_stats()
        autocasion_stats = stats.get("autocasion", {})
        objetivos = self.supabase.get_objetivos("autocasion", limit=100)

        # HeadlessX status
        headlessx_status = "unavailable"
        if self.headlessx.is_available():
            server_status = self.headlessx.get_status()
            if server_status:
                headlessx_status = f"v{server_status.get('version', '?')}"

        return {
            "total_listings": autocasion_stats.get("total", 0),
            "total_objetivos": len(objetivos),
            "brands_available": len(self.site.get_brands_list()),
            "headlessx_status": headlessx_status,
        }

    def close(self):
        """Clean up resources."""
        if self._session:
            self._session.close()
            self._session = None
        if self._headlessx:
            self._headlessx.close()
            self._headlessx = None

    def stop(self):
        """Stop the scraping process."""
        self._should_stop = True

    async def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client for parallel requests."""
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

    async def _fetch_with_headlessx_async(
        self,
        url: str,
        config: HeadlessXConfig,
        log_callback: Optional[Callable] = None,
        max_retries: int = 3
    ) -> tuple[Optional[str], str]:
        """
        Fetch HTML using HeadlessX API (ASYNC version for parallel scraping).

        Uses httpx async client for true parallelism without blocking.
        """
        import os
        log = log_callback or (lambda msg: print(msg))

        api_url = os.getenv('HEADLESSX_URL', 'http://localhost:3000')
        auth_token = os.getenv('HEADLESSX_TOKEN') or os.getenv('HEADLESSX_AUTH_TOKEN')

        if not auth_token:
            log("  ERROR: HEADLESSX_TOKEN not configured")
            return None, "headlessx_async"

        api_endpoint = f"{api_url}/api/render"

        # Thread-safe counter increment
        async with self._request_lock:
            self._request_count += 1
            request_num = self._request_count

        # Build payload from config
        payload = config.to_dict()
        payload["url"] = url

        profile_info = f"{config.device_profile} | {config.geo_profile} | {config.behavior_profile}"
        log(f"    HeadlessX ASYNC #{request_num}: {profile_info}")

        last_error = None

        for attempt in range(max_retries):
            try:
                fetch_start = time.time()

                client = await self._get_async_client()
                response = await client.post(
                    api_endpoint,
                    params={"token": auth_token},
                    json=payload
                )

                fetch_elapsed = time.time() - fetch_start
                response.raise_for_status()

                data = response.json()
                html = data.get("html", "")

                if not html:
                    error_msg = data.get("error", "No HTML returned")
                    raise Exception(f"HeadlessX error: {error_msg}")

                log(f"    OK: {len(html):,} bytes in {fetch_elapsed:.1f}s")
                return html, "headlessx_async"

            except httpx.TimeoutException as e:
                last_error = e
                wait_time = 2 ** attempt
                log(f"    TIMEOUT (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)

            except httpx.HTTPStatusError as e:
                last_error = e
                log(f"    HTTP ERROR {e.response.status_code}")
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                last_error = e
                log(f"    ERROR: {e}")
                break

        return None, "headlessx_async"

    async def scrape_batch_parallel(
        self,
        marcas: List[str],
        max_pages: int = 5,
        save_to_db: bool = True,
        stealth: bool = False,
        max_workers: int = 3,
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None
    ) -> List[ScrapeResult]:
        """
        Scrape multiple brands in PARALLEL using asyncio.

        Args:
            marcas: List of brand slugs to scrape
            max_pages: Max pages per brand (0 = all pages)
            save_to_db: Save to Supabase
            stealth: Use stealth mode
            max_workers: Number of concurrent brand scrapers (2-5 recommended)
            progress_callback: Callback for progress updates (current, total, message)
            log_callback: Callback for log messages

        Returns:
            List of ScrapeResult for each brand
        """
        start_time = time.time()
        self._should_stop = False

        log = log_callback or (lambda msg: print(msg))
        progress = progress_callback or (lambda c, t, m: None)

        log(f"\n{'#'*60}")
        log(f"# PARALLEL SCRAPE: {len(marcas)} brands")
        log(f"# Workers: {max_workers}")
        log(f"# Max pages per brand: {max_pages if max_pages > 0 else 'ALL'}")
        log(f"{'#'*60}")

        # Semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_workers)

        # Thread-safe progress counter
        completed_lock = asyncio.Lock()
        completed_count = 0

        async def scrape_marca_with_semaphore(marca: str) -> ScrapeResult:
            nonlocal completed_count

            async with semaphore:
                if self._should_stop:
                    return ScrapeResult(
                        marca=marca,
                        total_listings=0,
                        pages_scraped=0,
                        saved_to_db=0,
                        errors=["Stopped by user"],
                        duration_seconds=0,
                        method_used="cancelled"
                    )

                # Create brand-specific logger
                def marca_log(msg: str):
                    log(f"[{marca.upper()}] {msg}")

                marca_log(f"Starting...")

                try:
                    result = await self.scrape_marca(
                        marca=marca,
                        max_pages=max_pages,
                        save_to_db=save_to_db,
                        stealth=stealth,
                        log_callback=marca_log
                    )

                    # Thread-safe counter increment
                    async with completed_lock:
                        completed_count += 1
                        current = completed_count

                    progress(current, len(marcas), f"Completed {marca} ({current}/{len(marcas)})")
                    marca_log(f"Done: {result.total_listings} listings")

                    return result

                except Exception as e:
                    marca_log(f"ERROR: {e}")
                    async with completed_lock:
                        completed_count += 1
                    return ScrapeResult(
                        marca=marca,
                        total_listings=0,
                        pages_scraped=0,
                        saved_to_db=0,
                        errors=[str(e)],
                        duration_seconds=0,
                        method_used="error"
                    )

        try:
            # Create tasks for all brands
            tasks = [scrape_marca_with_semaphore(marca) for marca in marcas]

            # Run all tasks concurrently (limited by semaphore)
            results = await asyncio.gather(*tasks)

            # Summary
            duration = time.time() - start_time
            total_listings = sum(r.total_listings for r in results)
            total_saved = sum(r.saved_to_db for r in results)
            total_errors = sum(len(r.errors) for r in results)

            log(f"\n{'#'*60}")
            log(f"# PARALLEL SCRAPE COMPLETE")
            log(f"# Duration: {duration:.1f}s")
            log(f"# Total listings: {total_listings}")
            log(f"# Total saved: {total_saved}")
            log(f"# Total errors: {total_errors}")
            log(f"# Speed: ~{len(marcas)/max_workers:.1f}x faster than sequential")
            log(f"{'#'*60}")

            return results

        finally:
            await self._close_async_client()
            log("Resources cleaned up")
