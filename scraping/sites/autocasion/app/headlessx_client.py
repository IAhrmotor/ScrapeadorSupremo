"""
HeadlessX API Client for anti-detection web scraping.

HeadlessX is an advanced anti-detection browser service that uses:
- Fingerprint spoofing (Canvas, WebGL, Audio, WebRTC)
- Behavioral simulation (mouse, keyboard, scroll)
- WAF bypass (Cloudflare, DataDome, Akamai)
- Device/Geo profiles for realistic sessions

Server must be running at http://localhost:3000 (default)
See: https://github.com/user/headlessx for setup
"""

import os
import time
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, field
import requests
from dotenv import load_dotenv

load_dotenv()


# Configuration
HEADLESSX_BASE_URL = os.getenv("HEADLESSX_URL", "http://localhost:3000")
HEADLESSX_TOKEN = os.getenv("HEADLESSX_TOKEN", "")


@dataclass
class HeadlessXConfig:
    """Configuration for HeadlessX render requests."""

    # Timeouts
    timeout: int = 90000  # 90 seconds
    extra_wait_time: int = 5000  # 5 seconds after load
    wait_until: Literal["domcontentloaded", "load", "networkidle"] = "networkidle"
    return_partial_on_timeout: bool = True

    # Device profiles
    device_profile: Literal[
        "high-end-desktop",
        "mid-range-desktop",
        "business-laptop",
        "gaming-laptop"
    ] = "mid-range-desktop"

    # Geo profiles
    geo_profile: Literal[
        "us-east", "us-west", "us-central",
        "uk", "germany", "france",
        "canada", "australia"
    ] = "us-east"

    # Behavior profiles
    behavior_profile: Literal[
        "natural", "cautious", "confident", "elderly"
    ] = "natural"

    # Anti-detection features
    enable_canvas_spoofing: bool = True
    enable_webgl_spoofing: bool = True
    enable_audio_spoofing: bool = True
    enable_webrtc_blocking: bool = True
    enable_advanced_stealth: bool = True

    # Behavioral simulation
    simulate_mouse_movement: bool = True
    simulate_scrolling: bool = True
    simulate_typing: bool = False
    human_delays: bool = True
    randomize_timings: bool = True

    # Content extraction
    scroll_to_bottom: bool = True
    wait_for_selectors: List[str] = field(default_factory=list)
    click_selectors: List[str] = field(default_factory=list)
    remove_elements: List[str] = field(default_factory=list)

    # Custom headers/cookies
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to API request body."""
        return {
            "timeout": self.timeout,
            "extraWaitTime": self.extra_wait_time,
            "waitUntil": self.wait_until,
            "returnPartialOnTimeout": self.return_partial_on_timeout,
            "deviceProfile": self.device_profile,
            "geoProfile": self.geo_profile,
            "behaviorProfile": self.behavior_profile,
            "enableCanvasSpoofing": self.enable_canvas_spoofing,
            "enableWebGLSpoofing": self.enable_webgl_spoofing,
            "enableAudioSpoofing": self.enable_audio_spoofing,
            "enableWebRTCBlocking": self.enable_webrtc_blocking,
            "enableAdvancedStealth": self.enable_advanced_stealth,
            "simulateMouseMovement": self.simulate_mouse_movement,
            "simulateScrolling": self.simulate_scrolling,
            "simulateTyping": self.simulate_typing,
            "humanDelays": self.human_delays,
            "randomizeTimings": self.randomize_timings,
            "scrollToBottom": self.scroll_to_bottom,
            "waitForSelectors": self.wait_for_selectors,
            "clickSelectors": self.click_selectors,
            "removeElements": self.remove_elements,
            "headers": self.headers,
            "cookies": self.cookies,
        }


@dataclass
class RenderResult:
    """Result from a HeadlessX render request."""
    success: bool
    html: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    content_length: int = 0
    was_timeout: bool = False
    is_emergency_content: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0


class HeadlessXClient:
    """
    Client for HeadlessX anti-detection browser API.

    Usage:
        client = HeadlessXClient()
        if client.is_available():
            result = client.render("https://example.com")
            print(result.html)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None
    ):
        self.base_url = (base_url or HEADLESSX_BASE_URL).rstrip("/")
        self.token = token or HEADLESSX_TOKEN
        self._session: Optional[requests.Session] = None
        self._is_available: Optional[bool] = None

    @property
    def session(self) -> requests.Session:
        """Lazy initialization of requests session."""
        if self._session is None:
            self._session = requests.Session()
            if self.token:
                self._session.headers["Authorization"] = f"Bearer {self.token}"
            self._session.headers["Content-Type"] = "application/json"
        return self._session

    def is_available(self, force_check: bool = False) -> bool:
        """Check if HeadlessX server is running."""
        if self._is_available is not None and not force_check:
            return self._is_available

        try:
            # /api/health does not require authentication
            r = requests.get(f"{self.base_url}/api/health", timeout=5)
            if r.status_code == 200:
                data = r.json()
                self._is_available = data.get("status") == "OK"
            else:
                self._is_available = False
        except Exception as e:
            self._is_available = False

        return self._is_available

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get detailed server status from health endpoint (no auth required)."""
        try:
            # Use /api/health which doesn't require auth
            r = requests.get(f"{self.base_url}/api/health", timeout=5)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

    def get_profiles(self) -> Optional[Dict[str, Any]]:
        """Get available device/behavior profiles."""
        try:
            r = self.session.get(f"{self.base_url}/api/profiles", timeout=5)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

    def render(
        self,
        url: str,
        config: Optional[HeadlessXConfig] = None
    ) -> RenderResult:
        """
        Render a page with full anti-detection.

        Args:
            url: URL to render
            config: Optional HeadlessXConfig for customization

        Returns:
            RenderResult with HTML content and metadata
        """
        if config is None:
            config = HeadlessXConfig()

        # Build request body
        body = config.to_dict()
        body["url"] = url

        start_time = time.time()

        try:
            response = self.session.post(
                f"{self.base_url}/api/render",
                json=body,
                timeout=config.timeout / 1000 + 30  # Add buffer
            )

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return RenderResult(
                    success=data.get("success", True),
                    html=data.get("html"),
                    url=data.get("url", url),
                    title=data.get("title"),
                    content_length=data.get("contentLength", 0),
                    was_timeout=data.get("wasTimeout", False),
                    is_emergency_content=data.get("isEmergencyContent", False),
                    metadata=data.get("metadata", {}),
                    response_time_ms=response_time
                )
            else:
                return RenderResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                    response_time_ms=response_time
                )

        except requests.Timeout:
            return RenderResult(
                success=False,
                error="Request timeout",
                was_timeout=True,
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return RenderResult(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000
            )

    def render_stealth(
        self,
        url: str,
        config: Optional[HeadlessXConfig] = None
    ) -> RenderResult:
        """
        Render with maximum stealth settings.

        Uses the /api/render/stealth endpoint optimized for
        heavily protected sites (Cloudflare, DataDome, etc).
        """
        if config is None:
            config = HeadlessXConfig(
                behavior_profile="cautious",
                enable_advanced_stealth=True,
                simulate_mouse_movement=True,
                simulate_scrolling=True,
                human_delays=True,
                randomize_timings=True,
                extra_wait_time=10000
            )

        body = config.to_dict()
        body["url"] = url

        start_time = time.time()

        try:
            response = self.session.post(
                f"{self.base_url}/api/render/stealth",
                json=body,
                timeout=config.timeout / 1000 + 30
            )

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return RenderResult(
                    success=data.get("success", True),
                    html=data.get("html"),
                    url=data.get("url", url),
                    title=data.get("title"),
                    content_length=data.get("contentLength", 0),
                    was_timeout=data.get("wasTimeout", False),
                    is_emergency_content=data.get("isEmergencyContent", False),
                    metadata=data.get("metadata", {}),
                    response_time_ms=response_time
                )
            else:
                return RenderResult(
                    success=False,
                    error=f"HTTP {response.status_code}",
                    response_time_ms=response_time
                )

        except Exception as e:
            return RenderResult(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000
            )

    def get_html(self, url: str, timeout: int = 30000) -> Optional[str]:
        """
        Quick HTML extraction without full rendering.

        Uses /api/html endpoint for faster extraction.
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/html",
                json={"url": url, "timeout": timeout},
                timeout=timeout / 1000 + 10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("html")
        except:
            pass
        return None

    def batch_render(
        self,
        urls: List[str],
        config: Optional[HeadlessXConfig] = None,
        concurrency: int = 2
    ) -> Dict[str, RenderResult]:
        """
        Batch render multiple URLs.

        Args:
            urls: List of URLs to render
            config: Optional shared config
            concurrency: Number of concurrent renders

        Returns:
            Dict mapping URL to RenderResult
        """
        if config is None:
            config = HeadlessXConfig()

        body = config.to_dict()
        body["urls"] = urls
        body["concurrency"] = concurrency

        try:
            # Start batch
            response = self.session.post(
                f"{self.base_url}/api/batch",
                json=body,
                timeout=300
            )

            if response.status_code == 200:
                data = response.json()
                results = {}

                # Process results
                for item in data.get("results", []):
                    url = item.get("url", "")
                    results[url] = RenderResult(
                        success=item.get("success", False),
                        html=item.get("html"),
                        url=url,
                        title=item.get("title"),
                        content_length=item.get("contentLength", 0),
                        error=item.get("error")
                    )

                return results

        except Exception as e:
            # Return error for all URLs
            return {url: RenderResult(success=False, error=str(e)) for url in urls}

        return {}

    def test_fingerprint(self) -> Optional[Dict[str, Any]]:
        """Test fingerprint consistency."""
        try:
            r = self.session.post(
                f"{self.base_url}/api/test-fingerprint",
                json={},
                timeout=60
            )
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

    def run_detection_test(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Run bot detection test on a URL.

        Returns detection results and confidence scores.
        """
        try:
            r = self.session.post(
                f"{self.base_url}/api/detection/test",
                json={"url": url},
                timeout=120
            )
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

    def close(self):
        """Clean up resources."""
        if self._session:
            self._session.close()
            self._session = None


# Global client instance
_client: Optional[HeadlessXClient] = None


def get_headlessx_client() -> HeadlessXClient:
    """Get global HeadlessX client instance."""
    global _client
    if _client is None:
        _client = HeadlessXClient()
    return _client


# Convenience functions
def is_headlessx_available() -> bool:
    """Check if HeadlessX server is available."""
    return get_headlessx_client().is_available()


def fetch_with_headlessx(url: str, stealth: bool = False) -> Optional[str]:
    """
    Fetch a URL using HeadlessX.

    Args:
        url: URL to fetch
        stealth: Use maximum stealth mode

    Returns:
        HTML content or None if failed
    """
    client = get_headlessx_client()

    if not client.is_available():
        return None

    if stealth:
        result = client.render_stealth(url)
    else:
        result = client.render(url)

    if result.success:
        return result.html

    return None
