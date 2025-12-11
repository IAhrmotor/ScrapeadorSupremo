"""Domain-based rate limiter for web scraping."""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


@dataclass
class DomainStats:
    """Statistics for a single domain."""
    total_requests: int = 0
    last_request: float = 0
    blocked_count: int = 0


class DomainRateLimiter:
    """
    Rate limiter that enforces delays between requests per domain.

    Features:
    - Configurable delays per domain
    - Automatic domain extraction from URLs
    - Statistics tracking
    - Thread-safe with asyncio.Lock

    Usage:
        limiter = DomainRateLimiter()

        # Wait for rate limit
        await limiter.acquire("https://example.com/page1")

        # Or with domain directly
        await limiter.acquire_domain("example.com")

        # Get stats
        stats = limiter.get_stats()
    """

    # Default delays per domain (seconds)
    DEFAULT_DELAYS = {
        "coches.net": 1.5,
        "www.coches.net": 1.5,
        "autocasion.com": 2.0,
        "www.autocasion.com": 2.0,
        "ocasionplus.com": 1.0,
        "www.ocasionplus.com": 1.0,
        # Supabase needs protection
        "supabase.co": 0.5,
        # Default for unknown domains
        "_default": 1.0
    }

    def __init__(
        self,
        delays: Optional[Dict[str, float]] = None,
        default_delay: float = 1.0
    ):
        """
        Initialize rate limiter.

        Args:
            delays: Custom delays per domain (overrides defaults)
            default_delay: Delay for domains not in the delays dict
        """
        self._delays = {**self.DEFAULT_DELAYS}
        if delays:
            self._delays.update(delays)
        self._delays["_default"] = default_delay

        self._stats: Dict[str, DomainStats] = {}
        self._lock = asyncio.Lock()

    def get_delay(self, domain: str) -> float:
        """Get configured delay for domain."""
        # Try exact match
        if domain in self._delays:
            return self._delays[domain]

        # Try without www prefix
        if domain.startswith("www."):
            base_domain = domain[4:]
            if base_domain in self._delays:
                return self._delays[base_domain]

        # Try with www prefix
        www_domain = f"www.{domain}"
        if www_domain in self._delays:
            return self._delays[www_domain]

        # Check for subdomain matches (e.g., api.example.com matches example.com)
        parts = domain.split(".")
        if len(parts) > 2:
            parent = ".".join(parts[-2:])
            if parent in self._delays:
                return self._delays[parent]

        return self._delays["_default"]

    async def acquire(self, url: str) -> float:
        """
        Wait for rate limit before making request.

        Args:
            url: Full URL to request

        Returns:
            Actual wait time in seconds
        """
        domain = self._extract_domain(url)
        return await self.acquire_domain(domain)

    async def acquire_domain(self, domain: str) -> float:
        """
        Wait for rate limit for specific domain.

        Args:
            domain: Domain name

        Returns:
            Actual wait time in seconds
        """
        async with self._lock:
            delay = self.get_delay(domain)
            stats = self._get_or_create_stats(domain)

            # Calculate wait time
            elapsed = time.time() - stats.last_request
            wait_time = max(0, delay - elapsed)

            if wait_time > 0:
                stats.blocked_count += 1

        # Wait outside lock to allow other domains
        if wait_time > 0:
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s for {domain}")
            await asyncio.sleep(wait_time)

        # Update stats after wait
        async with self._lock:
            stats = self._get_or_create_stats(domain)
            stats.total_requests += 1
            stats.last_request = time.time()

        return wait_time

    async def try_acquire(self, url: str) -> bool:
        """
        Try to acquire without waiting.

        Args:
            url: Full URL to request

        Returns:
            True if acquired, False if would need to wait
        """
        domain = self._extract_domain(url)
        return await self.try_acquire_domain(domain)

    async def try_acquire_domain(self, domain: str) -> bool:
        """
        Try to acquire for domain without waiting.

        Args:
            domain: Domain name

        Returns:
            True if acquired, False if would need to wait
        """
        async with self._lock:
            delay = self.get_delay(domain)
            stats = self._get_or_create_stats(domain)

            elapsed = time.time() - stats.last_request
            if elapsed >= delay:
                stats.total_requests += 1
                stats.last_request = time.time()
                return True

            return False

    def set_delay(self, domain: str, delay: float):
        """
        Set delay for a domain.

        Args:
            domain: Domain name
            delay: Delay in seconds
        """
        self._delays[domain] = delay

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url

    def _get_or_create_stats(self, domain: str) -> DomainStats:
        """Get or create stats for domain."""
        if domain not in self._stats:
            self._stats[domain] = DomainStats()
        return self._stats[domain]

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        domain_stats = {}
        for domain, stats in self._stats.items():
            domain_stats[domain] = {
                "total_requests": stats.total_requests,
                "blocked_count": stats.blocked_count,
                "configured_delay": self.get_delay(domain),
                "last_request": stats.last_request
            }

        return {
            "total_domains": len(self._stats),
            "total_requests": sum(s.total_requests for s in self._stats.values()),
            "total_blocked": sum(s.blocked_count for s in self._stats.values()),
            "domains": domain_stats
        }

    def reset_stats(self):
        """Reset all statistics."""
        self._stats.clear()


class AdaptiveRateLimiter(DomainRateLimiter):
    """
    Rate limiter that adapts delays based on response codes.

    Increases delay when receiving 429 (Too Many Requests),
    decreases delay on successful requests.
    """

    def __init__(
        self,
        delays: Optional[Dict[str, float]] = None,
        default_delay: float = 1.0,
        min_delay: float = 0.5,
        max_delay: float = 10.0,
        increase_factor: float = 1.5,
        decrease_factor: float = 0.9
    ):
        super().__init__(delays, default_delay)
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._increase_factor = increase_factor
        self._decrease_factor = decrease_factor
        self._current_delays: Dict[str, float] = {}

    def get_delay(self, domain: str) -> float:
        """Get current adaptive delay for domain."""
        if domain in self._current_delays:
            return self._current_delays[domain]
        return super().get_delay(domain)

    async def report_success(self, url_or_domain: str):
        """Report successful request, may decrease delay."""
        domain = self._extract_domain(url_or_domain)

        async with self._lock:
            current = self.get_delay(domain)
            base = super().get_delay(domain)

            # Only decrease if above base delay
            if current > base:
                new_delay = max(base, current * self._decrease_factor)
                self._current_delays[domain] = new_delay
                logger.debug(f"Decreased delay for {domain}: {current:.2f}s -> {new_delay:.2f}s")

    async def report_rate_limited(self, url_or_domain: str):
        """Report 429 response, increases delay."""
        domain = self._extract_domain(url_or_domain)

        async with self._lock:
            current = self.get_delay(domain)
            new_delay = min(self._max_delay, current * self._increase_factor)
            self._current_delays[domain] = new_delay
            logger.warning(f"Rate limited! Increased delay for {domain}: {current:.2f}s -> {new_delay:.2f}s")

    async def report_error(self, url_or_domain: str, status_code: int):
        """Report response status code."""
        if status_code == 429:
            await self.report_rate_limited(url_or_domain)
        elif 200 <= status_code < 300:
            await self.report_success(url_or_domain)
