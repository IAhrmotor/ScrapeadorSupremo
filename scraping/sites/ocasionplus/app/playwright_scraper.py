"""Playwright-based scraper for OcasionPlus infinite scroll."""

import asyncio
import logging
from typing import Optional, Callable
from playwright.async_api import (
    async_playwright,
    Page,
    Browser,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError
)

logger = logging.getLogger(__name__)


class PlaywrightOcasionPlusScraper:
    """
    Playwright scraper for OcasionPlus.com infinite scroll pattern.

    Handles:
    - Initial page load
    - Scroll to bottom to load more cars
    - Click "load more" button if present
    - Repeat until all cars loaded or max iterations reached
    """

    # Selector for vehicle cards on OcasionPlus
    CARD_SELECTOR = "div.cardVehicle_card__LwFCi"
    LINK_SELECTOR = "a.cardVehicle_link__l8xYT"

    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: Optional[str] = None
    ):
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def start(self):
        """Start Playwright browser."""
        self.playwright = await async_playwright().start()

        # Launch Chromium with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

        # Create context with stealth settings
        self.context = await self.browser.new_context(
            viewport={'width': self.viewport_width, 'height': self.viewport_height},
            user_agent=self.user_agent,
            locale='es-ES',
            timezone_id='Europe/Madrid',
            permissions=[],
            ignore_https_errors=True,
            java_script_enabled=True,
        )

        # Add stealth scripts
        await self.context.add_init_script("""
            // Remove webdriver flag
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });

            // Mock chrome object
            window.chrome = {
                runtime: {}
            };

            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en']
            });
        """)

        logger.info("Playwright browser started for OcasionPlus")

    async def close(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")

    async def scrape_with_infinite_scroll(
        self,
        url: str,
        max_iterations: int = 200,
        scroll_delay: float = 2.0,
        click_delay: float = 3.0,
        button_selector: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Scrape page with infinite scroll.

        Args:
            url: Page URL to scrape
            max_iterations: Maximum number of scroll/click iterations
            scroll_delay: Delay after scrolling (seconds)
            click_delay: Delay after clicking button (seconds)
            button_selector: CSS selector for "load more" button (optional)
            log_callback: Optional callback for logging progress

        Returns:
            Final HTML content with all loaded cars, or None on error
        """
        def log(msg: str):
            logger.info(msg)
            if log_callback:
                log_callback(msg)

        if not self.context:
            log("ERROR: Browser not started. Call start() first.")
            return None

        page = await self.context.new_page()

        try:
            log(f"Loading page: {url}")

            # Navigate to page
            await page.goto(url, wait_until='networkidle', timeout=60000)
            log("Page loaded successfully")

            # Wait for initial cards to render
            try:
                await page.wait_for_selector(self.CARD_SELECTOR, timeout=15000)
            except PlaywrightTimeoutError:
                log("Warning: Initial cards not found, trying alternate selector...")
                await page.wait_for_selector(self.LINK_SELECTOR, timeout=10000)

            # Count initial cars
            initial_count = await page.locator(self.CARD_SELECTOR).count()
            log(f"Initial cars loaded: {initial_count}")

            iteration = 0
            total_loaded = initial_count
            no_new_cars_count = 0

            while iteration < max_iterations:
                iteration += 1

                # Scroll to bottom
                log(f"\n[Iteration {iteration}/{max_iterations}] Scrolling to bottom...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(scroll_delay)

                # Try to click load more button if selector provided
                if button_selector:
                    try:
                        button = page.locator(button_selector)
                        button_count = await button.count()

                        if button_count > 0 and await button.is_visible():
                            log("  Clicking 'load more' button...")
                            await button.click()
                            await asyncio.sleep(click_delay)
                    except Exception as e:
                        log(f"  Button click failed: {e}")

                # Wait for potential new content to load
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeoutError:
                    pass

                # Count total cars now
                current_count = await page.locator(self.CARD_SELECTOR).count()
                new_cars = current_count - total_loaded
                total_loaded = current_count

                log(f"  Loaded {new_cars} new cars (total: {total_loaded})")

                # Check if we're done loading
                if new_cars == 0:
                    no_new_cars_count += 1
                    log(f"  No new cars (attempt {no_new_cars_count}/3)")

                    if no_new_cars_count >= 3:
                        log("  No more cars to load - stopping")
                        break
                else:
                    no_new_cars_count = 0

            # Get final HTML
            log(f"\n[OK] Scraping complete!")
            log(f"  Total iterations: {iteration}")
            log(f"  Total cars loaded: {total_loaded}")

            html = await page.content()
            return html

        except Exception as e:
            log(f"ERROR during scraping: {e}")
            logger.exception(e)
            return None

        finally:
            await page.close()

    async def scrape_with_progressive_save(
        self,
        url: str,
        max_iterations: int = 200,
        scroll_delay: float = 2.0,
        click_delay: float = 3.0,
        button_selector: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        save_callback: Optional[Callable[[str, int], int]] = None,
        save_every: int = 10
    ) -> tuple[Optional[str], int]:
        """
        Scrape page with infinite scroll, saving progressively every N iterations.

        Args:
            url: Page URL to scrape
            max_iterations: Maximum number of scroll/click iterations
            scroll_delay: Delay after scrolling (seconds)
            click_delay: Delay after clicking button (seconds)
            button_selector: CSS selector for "load more" button (optional)
            log_callback: Optional callback for logging progress
            save_callback: Callback to save HTML and iteration, returns saved count
            save_every: Save every N iterations

        Returns:
            Tuple of (final HTML content, total saved count)
        """
        def log(msg: str):
            logger.info(msg)
            if log_callback:
                log_callback(msg)

        if not self.context:
            log("ERROR: Browser not started. Call start() first.")
            return None, 0

        page = await self.context.new_page()
        total_saved = 0

        try:
            log(f"Loading page: {url}")

            # Navigate to page
            await page.goto(url, wait_until='networkidle', timeout=60000)
            log("Page loaded successfully")

            # Wait for initial cards to render
            try:
                await page.wait_for_selector(self.CARD_SELECTOR, timeout=15000)
            except PlaywrightTimeoutError:
                log("Warning: Initial cards not found, trying alternate selector...")
                await page.wait_for_selector(self.LINK_SELECTOR, timeout=10000)

            # Count initial cars
            initial_count = await page.locator(self.CARD_SELECTOR).count()
            log(f"Initial cars loaded: {initial_count}")

            iteration = 0
            total_loaded = initial_count
            no_new_cars_count = 0

            while iteration < max_iterations:
                iteration += 1

                # Scroll to bottom
                log(f"\n[Iteration {iteration}/{max_iterations}] Scrolling to bottom...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(scroll_delay)

                # Try to click load more button if selector provided
                if button_selector:
                    try:
                        button = page.locator(button_selector)
                        button_count = await button.count()

                        if button_count > 0 and await button.is_visible():
                            log("  Clicking 'load more' button...")
                            await button.click()
                            await asyncio.sleep(click_delay)
                    except Exception as e:
                        log(f"  Button click failed: {e}")

                # Wait for potential new content to load
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeoutError:
                    pass

                # Count total cars now
                current_count = await page.locator(self.CARD_SELECTOR).count()
                new_cars = current_count - total_loaded
                total_loaded = current_count

                log(f"  Loaded {new_cars} new cars (total: {total_loaded})")

                # Progressive save every N iterations
                if save_callback and iteration % save_every == 0:
                    log(f"  [SAVE] Saving at iteration {iteration}...")
                    html = await page.content()
                    saved = save_callback(html, iteration)
                    total_saved += saved
                    log(f"  [SAVE] Saved {saved} new listings (total saved: {total_saved})")

                # Check if we're done loading
                if new_cars == 0:
                    no_new_cars_count += 1
                    log(f"  No new cars (attempt {no_new_cars_count}/3)")

                    if no_new_cars_count >= 3:
                        log("  No more cars to load - stopping")
                        break
                else:
                    no_new_cars_count = 0

            # Final save
            log(f"\n[OK] Scraping complete!")
            log(f"  Total iterations: {iteration}")
            log(f"  Total cars loaded: {total_loaded}")

            html = await page.content()

            # Final save if callback provided
            if save_callback:
                log(f"  [FINAL SAVE] Saving remaining listings...")
                saved = save_callback(html, iteration)
                total_saved += saved
                log(f"  [FINAL SAVE] Saved {saved} new listings (total saved: {total_saved})")

            return html, total_saved

        except Exception as e:
            log(f"ERROR during scraping: {e}")
            logger.exception(e)
            return None, total_saved

        finally:
            await page.close()

    async def scrape_simple(self, url: str) -> Optional[str]:
        """
        Simple page scrape without infinite scroll (for testing).

        Args:
            url: Page URL to scrape

        Returns:
            HTML content or None on error
        """
        if not self.context:
            logger.error("Browser not started")
            return None

        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_selector(self.CARD_SELECTOR, timeout=15000)
            html = await page.content()
            return html

        except Exception as e:
            logger.error(f"Error during simple scrape: {e}")
            return None

        finally:
            await page.close()
