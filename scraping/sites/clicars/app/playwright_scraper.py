"""Playwright-based scraper for Clicars infinite scroll."""

import asyncio
import logging
from typing import Optional, Callable
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class PlaywrightClicarsScaper:
    """
    Playwright scraper for Clicars.com infinite scroll pattern.

    Handles:
    - Initial page load
    - Scroll to bottom to reveal "Ver más" button
    - Click button to load more cars
    - Repeat until all cars loaded or max iterations reached
    """

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

        logger.info("Playwright browser started")

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
        button_selector: str,
        max_iterations: int = 200,
        scroll_delay: float = 2.0,
        click_delay: float = 3.0,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Scrape page with infinite scroll by clicking "Ver más" button repeatedly.

        Args:
            url: Page URL to scrape
            button_selector: CSS selector for "Ver más" button
            max_iterations: Maximum number of clicks (stops early if button disappears)
            scroll_delay: Delay after scrolling (seconds)
            click_delay: Delay after clicking button (seconds)
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

            # Wait for initial cars to render
            await page.wait_for_selector('a[data-vehicle-web-id]', timeout=10000)

            # Close cookie consent popup (Cookiebot) if present
            try:
                cookie_accept = page.locator('#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')
                if await cookie_accept.count() > 0 and await cookie_accept.is_visible():
                    log("Closing cookie consent popup...")
                    await cookie_accept.click()
                    await asyncio.sleep(1)
            except Exception as e:
                log(f"Cookie popup handling: {e}")

            # Also try to close via JavaScript if dialog still exists
            try:
                await page.evaluate("""
                    const dialog = document.getElementById('CybotCookiebotDialog');
                    if (dialog) dialog.remove();
                    const underlay = document.getElementById('CybotCookiebotDialogBodyUnderlay');
                    if (underlay) underlay.remove();
                """)
            except:
                pass

            # Count initial cars
            initial_count = await page.locator('a[data-vehicle-web-id]').count()
            log(f"Initial cars loaded: {initial_count}")

            iteration = 0
            total_loaded = initial_count
            no_button_count = 0
            no_new_cars_count = 0

            while iteration < max_iterations:
                iteration += 1

                # Scroll to bottom to reveal button
                log(f"\n[Iteration {iteration}/{max_iterations}] Scrolling to bottom...")

                # Scroll in steps to trigger lazy loading
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(0.5)

                # Final scroll to very bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(scroll_delay)

                # Check if button exists and is visible
                try:
                    button = page.locator(button_selector)
                    button_count = await button.count()

                    if button_count == 0:
                        no_button_count += 1
                        log(f"  'Ver mas' button not found (attempt {no_button_count}/5)")

                        # If button not found 5 times in a row, we're done
                        if no_button_count >= 5:
                            log("  Button disappeared - all cars loaded!")
                            break

                        # Try scrolling up and down to trigger button
                        await page.evaluate("window.scrollBy(0, -500)")
                        await asyncio.sleep(0.5)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(1)
                        continue

                    # Reset counter if we found the button
                    no_button_count = 0

                    # Check if button is visible
                    is_visible = await button.is_visible()
                    if not is_visible:
                        log("  Button exists but not visible, scrolling more...")
                        await page.evaluate("window.scrollBy(0, 500)")
                        await asyncio.sleep(1)
                        continue

                    # Click the button with force option to bypass interceptors
                    log("  Clicking 'Ver mas' button...")
                    await button.click(force=True, timeout=5000)

                    # Wait for new content
                    await asyncio.sleep(click_delay)

                    # Count total cars now
                    current_count = await page.locator('a[data-vehicle-web-id]').count()
                    new_cars = current_count - total_loaded
                    total_loaded = current_count

                    log(f"  Loaded {new_cars} new cars (total: {total_loaded})")

                    # If no new cars loaded multiple times, we might be done
                    if new_cars == 0:
                        no_new_cars_count += 1
                        if no_new_cars_count >= 5:
                            log("  No new cars 5 times - stopping")
                            break
                    else:
                        no_new_cars_count = 0

                except PlaywrightTimeoutError as e:
                    log(f"  Timeout (continuing): {e}")
                    continue
                except Exception as e:
                    log(f"  Error during iteration: {e}")
                    # Don't break, try to continue
                    continue

            # Get final HTML
            log(f"\nScraping complete!")
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
            await page.wait_for_selector('a[data-vehicle-web-id]', timeout=10000)
            html = await page.content()
            return html

        except Exception as e:
            logger.error(f"Error during simple scrape: {e}")
            return None

        finally:
            await page.close()
