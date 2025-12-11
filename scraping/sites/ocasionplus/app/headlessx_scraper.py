"""
HeadlessX-based scraper for OcasionPlus.

Uses HeadlessX API for anti-detection with same configuration as cochesnet/autocasion.
"""

import os
import time
import random
import requests
from typing import Optional, Callable, List
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()


# Profiles for rotation (same as cochesnet)
DEVICE_PROFILES = ["high-end-desktop", "mid-range-desktop", "business-laptop"]
GEO_PROFILES = ["spain", "france", "germany", "uk", "us-east"]
BEHAVIOR_PROFILES = ["natural", "cautious", "confident"]


@dataclass
class HeadlessXOcasionPlusConfig:
    """Configuration optimized for OcasionPlus scraping."""

    timeout: int = 180000  # 3 minutes
    extra_wait_time: int = 5000
    scroll_to_bottom: bool = True

    # Default profiles
    device_profile: str = "mid-range-desktop"
    geo_profile: str = "spain"
    behavior_profile: str = "natural"

    # Scroll settings
    scroll_iterations: int = 50
    scroll_delay_min: float = 2.0
    scroll_delay_max: float = 4.0


class HeadlessXOcasionPlusScraper:
    """
    Scraper for OcasionPlus using HeadlessX API.

    Uses the same configuration pattern as cochesnet and autocasion scrapers.
    """

    CARD_SELECTOR = "div.cardVehicle_card__LwFCi"

    def __init__(self, config: Optional[HeadlessXOcasionPlusConfig] = None):
        self.config = config or HeadlessXOcasionPlusConfig()
        self._request_count = 0
        self._profile_index = 0

    def _get_next_profiles(self) -> tuple:
        """Get next set of profiles with rotation."""
        device = DEVICE_PROFILES[self._profile_index % len(DEVICE_PROFILES)]
        geo = GEO_PROFILES[self._profile_index % len(GEO_PROFILES)]
        behavior = BEHAVIOR_PROFILES[self._profile_index % len(BEHAVIOR_PROFILES)]
        self._profile_index += 1
        return device, geo, behavior

    def _build_infinite_scroll_script(self, max_iterations: int) -> str:
        """
        Build JavaScript for infinite scroll with card counting.

        This script scrolls to bottom repeatedly until:
        - No new cards are loaded for 3 consecutive attempts
        - Max iterations reached
        """
        scroll_delay = int(self.config.scroll_delay_min * 1000)
        return f"""
        (async () => {{
            const cardSelector = '{self.CARD_SELECTOR}';
            const maxIterations = {max_iterations};
            const scrollDelay = {scroll_delay};

            let lastCount = 0;
            let noNewCardsCount = 0;
            let iteration = 0;

            // Wait for initial cards
            await new Promise(r => setTimeout(r, 2000));
            lastCount = document.querySelectorAll(cardSelector).length;
            console.log('Initial cards: ' + lastCount);

            while (iteration < maxIterations && noNewCardsCount < 3) {{
                iteration++;

                // Scroll to bottom with human-like behavior
                window.scrollTo({{
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                }});

                // Wait for content to load
                await new Promise(r => setTimeout(r, scrollDelay + Math.random() * 1000));

                // Count current cards
                const currentCount = document.querySelectorAll(cardSelector).length;
                const newCards = currentCount - lastCount;

                if (newCards === 0) {{
                    noNewCardsCount++;
                    console.log('Scroll ' + iteration + ': ' + currentCount + ' cards (no new, attempt ' + noNewCardsCount + '/3)');
                }} else {{
                    noNewCardsCount = 0;
                    console.log('Scroll ' + iteration + ': ' + currentCount + ' cards (+' + newCards + ' new)');
                }}

                lastCount = currentCount;
            }}

            // Final count
            const finalCount = document.querySelectorAll(cardSelector).length;
            console.log('DONE: ' + finalCount + ' total cards after ' + iteration + ' scrolls');

            return finalCount;
        }})()
        """

    def _build_payload(self, url: str, device: str, geo: str, behavior: str, max_iterations: int = 50) -> dict:
        """Build HeadlessX API payload with infinite scroll script."""
        return {
            "url": url,
            "timeout": self.config.timeout,
            "waitUntil": "networkidle",
            "returnPartialOnTimeout": True,

            # Rotated profiles for anti-detection
            "deviceProfile": device,
            "geoProfile": geo,
            "behaviorProfile": behavior,

            # Anti-detection features (all enabled)
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

            # Page interaction - use custom script for infinite scroll
            "scrollToBottom": False,  # We handle this in customScript
            "extraWaitTime": 2000,  # Initial wait before script
            "waitForNetworkIdle": True,
            "captureConsole": True,  # For debugging scroll progress

            # Custom infinite scroll script
            "customScript": self._build_infinite_scroll_script(max_iterations)
        }

    def scrape_with_scroll(
        self,
        url: str,
        max_iterations: Optional[int] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Scrape OcasionPlus using HeadlessX API.

        Args:
            url: URL to scrape
            max_iterations: Max scroll iterations (for compatibility, uses config)
            log_callback: Optional callback for progress logging

        Returns:
            HTML content or None on error
        """
        def log(msg: str):
            print(msg)
            if log_callback:
                log_callback(msg)

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

        # Build payload with max_iterations for infinite scroll
        iterations = max_iterations or self.config.scroll_iterations
        api_endpoint = f"{api_url}/api/render"
        payload = self._build_payload(url, device, geo, behavior, iterations)
        params = {"token": auth_token}

        log(f"\n{'='*60}")
        log(f"[HeadlessX OcasionPlus] Starting infinite scroll scrape")
        log(f"  URL: {url}")
        log(f"  API: {api_endpoint}")
        log(f"  Profile: {device} | {geo} | {behavior}")
        log(f"  Max scroll iterations: {iterations}")
        log(f"  Request #{self._request_count}")
        log(f"{'='*60}")

        try:
            fetch_start = time.time()
            response = requests.post(
                api_endpoint,
                params=params,
                json=payload,
                timeout=200
            )
            fetch_elapsed = time.time() - fetch_start

            response.raise_for_status()
            log(f"  Status: {response.status_code}")

            # Parse response
            data = response.json()
            html = data.get("html", "")

            if not html:
                error_msg = data.get("error", data.get("message", "No HTML returned"))
                log(f"  ERROR: {error_msg}")
                return None

            log(f"  HTML: {len(html):,} bytes")
            log(f"  Tiempo: {fetch_elapsed:.1f}s")

            # Count listings found
            listing_count = html.count(self.CARD_SELECTOR.split(".")[-1])
            log(f"  Listings encontrados: ~{listing_count}")

            log(f"\n  Scraping complete!")
            return html

        except requests.Timeout:
            log(f"  ERROR: Request timeout")
            return None
        except requests.RequestException as e:
            log(f"  ERROR: {e}")
            return None
        except Exception as e:
            log(f"  ERROR: {e}")
            return None

    def scrape_simple(self, url: str) -> Optional[str]:
        """Simple scrape without logging."""
        return self.scrape_with_scroll(url)

    def close(self):
        """Clean up resources."""
        pass
