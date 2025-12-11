"""Scraping Coordinator for managing multiple scrapers with DNS protection."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Awaitable
from enum import Enum

from ..dns import SmartDNSResolver, DNSConfig, DNSMonitor, DNSHealthStatus
from .limiter import DomainRateLimiter, AdaptiveRateLimiter


logger = logging.getLogger(__name__)


class ScraperStatus(Enum):
    """Status of a registered scraper."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class ScraperSlot:
    """Slot configuration for a scraper."""
    name: str
    max_concurrent: int
    current: int = 0
    status: ScraperStatus = ScraperStatus.IDLE
    semaphore: Optional[asyncio.Semaphore] = None
    total_requests: int = 0
    total_errors: int = 0

    def __post_init__(self):
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(self.max_concurrent)


@dataclass
class CoordinatorConfig:
    """Configuration for the scraping coordinator."""

    # Global connection limits
    max_global_connections: int = 6

    # Per-scraper defaults
    scraper_defaults: Dict[str, int] = field(default_factory=lambda: {
        "cochesnet": 3,
        "autocasion": 2,
        "ocasionplus": 1
    })

    # DNS configuration
    dns_providers: List[str] = field(default_factory=lambda: [
        "1.1.1.1",
        "8.8.8.8",
        "9.9.9.9",
        "208.67.222.222"
    ])
    dns_cache_ttl: int = 300
    dns_cache_size: int = 1000

    # Health monitoring
    health_check_interval: float = 30.0
    failure_threshold: int = 3
    recovery_threshold: int = 2

    # Rate limiting
    rate_limits: Dict[str, float] = field(default_factory=lambda: {
        "coches.net": 1.5,
        "autocasion.com": 2.0,
        "ocasionplus.com": 1.0,
        "supabase.co": 0.5
    })

    # Auto-pause on DNS issues
    auto_pause_on_dns_issues: bool = True


class ScrapingCoordinator:
    """
    Central coordinator for multiple scrapers with DNS protection.

    Features:
    - Global connection limit across all scrapers
    - Per-scraper slot allocation
    - Integrated DNS resolver with rotation
    - DNS health monitoring with auto-pause
    - Domain-based rate limiting

    Usage:
        coordinator = ScrapingCoordinator()

        # Register scrapers
        coordinator.register_scraper("cochesnet", max_concurrent=3)
        coordinator.register_scraper("autocasion", max_concurrent=2)

        # Start DNS monitoring
        await coordinator.start_monitoring()

        # Use in scraper
        async with coordinator.slot("cochesnet"):
            # Scraping code here
            await coordinator.rate_limit("https://coches.net/...")
            ...

        # Stop monitoring
        await coordinator.stop_monitoring()
    """

    def __init__(self, config: Optional[CoordinatorConfig] = None):
        """
        Initialize coordinator.

        Args:
            config: Coordinator configuration (uses defaults if not provided)
        """
        self.config = config or CoordinatorConfig()

        # Global semaphore
        self._global_semaphore = asyncio.Semaphore(self.config.max_global_connections)

        # Scrapers registry
        self._scrapers: Dict[str, ScraperSlot] = {}

        # DNS components
        self._dns_resolver = SmartDNSResolver(DNSConfig(
            providers=self.config.dns_providers,
            cache_ttl=self.config.dns_cache_ttl,
            cache_size=self.config.dns_cache_size
        ))

        self._dns_monitor = DNSMonitor(
            check_interval=self.config.health_check_interval,
            failure_threshold=self.config.failure_threshold,
            recovery_threshold=self.config.recovery_threshold
        )

        # Rate limiter
        self._rate_limiter = AdaptiveRateLimiter(
            delays=self.config.rate_limits
        )

        # State
        self._is_paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially

        # Register DNS callbacks
        if self.config.auto_pause_on_dns_issues:
            self._dns_monitor.on_unhealthy(self._on_dns_unhealthy)
            self._dns_monitor.on_recovered(self._on_dns_recovered)

        # Statistics
        self._start_time: Optional[float] = None
        self._total_slots_acquired = 0
        self._total_slots_released = 0

    def register_scraper(
        self,
        name: str,
        max_concurrent: Optional[int] = None
    ) -> ScraperSlot:
        """
        Register a scraper with the coordinator.

        Args:
            name: Unique name for the scraper
            max_concurrent: Max concurrent connections (uses default if not specified)

        Returns:
            The created ScraperSlot
        """
        if name in self._scrapers:
            logger.warning(f"Scraper '{name}' already registered, updating config")

        concurrent = max_concurrent or self.config.scraper_defaults.get(name, 2)

        slot = ScraperSlot(
            name=name,
            max_concurrent=concurrent
        )
        self._scrapers[name] = slot

        logger.info(f"Registered scraper '{name}' with {concurrent} slots")
        return slot

    async def start_monitoring(self):
        """Start DNS health monitoring."""
        self._start_time = time.time()
        await self._dns_monitor.start()
        logger.info("Coordinator monitoring started")

    async def stop_monitoring(self):
        """Stop DNS health monitoring."""
        await self._dns_monitor.stop()
        logger.info("Coordinator monitoring stopped")

    async def acquire_slot(self, scraper_name: str) -> bool:
        """
        Acquire a slot for the specified scraper.

        Waits if paused due to DNS issues.

        Args:
            scraper_name: Name of the scraper

        Returns:
            True if slot acquired

        Raises:
            ValueError: If scraper not registered
        """
        if scraper_name not in self._scrapers:
            raise ValueError(f"Scraper '{scraper_name}' not registered")

        slot = self._scrapers[scraper_name]

        # Wait if paused
        await self._pause_event.wait()

        # Acquire scraper-specific semaphore
        await slot.semaphore.acquire()

        # Acquire global semaphore
        await self._global_semaphore.acquire()

        slot.current += 1
        slot.total_requests += 1
        slot.status = ScraperStatus.RUNNING
        self._total_slots_acquired += 1

        logger.debug(f"Slot acquired for {scraper_name} ({slot.current}/{slot.max_concurrent})")
        return True

    async def release_slot(self, scraper_name: str):
        """
        Release a slot for the specified scraper.

        Args:
            scraper_name: Name of the scraper
        """
        if scraper_name not in self._scrapers:
            return

        slot = self._scrapers[scraper_name]

        slot.current -= 1
        if slot.current == 0:
            slot.status = ScraperStatus.IDLE

        slot.semaphore.release()
        self._global_semaphore.release()
        self._total_slots_released += 1

        logger.debug(f"Slot released for {scraper_name} ({slot.current}/{slot.max_concurrent})")

    def slot(self, scraper_name: str) -> "SlotContext":
        """
        Context manager for acquiring/releasing slots.

        Usage:
            async with coordinator.slot("cochesnet"):
                # Scraping code here
                ...
        """
        return SlotContext(self, scraper_name)

    async def rate_limit(self, url: str) -> float:
        """
        Wait for rate limit before making request.

        Args:
            url: URL to request

        Returns:
            Wait time in seconds
        """
        return await self._rate_limiter.acquire(url)

    async def resolve_dns(self, hostname: str) -> str:
        """
        Resolve hostname using smart DNS resolver.

        Args:
            hostname: Hostname to resolve

        Returns:
            Resolved IP address
        """
        return await self._dns_resolver.resolve(hostname)

    async def report_error(self, scraper_name: str, url: str, status_code: int):
        """
        Report an error from a scraper.

        Args:
            scraper_name: Name of the scraper
            url: URL that caused error
            status_code: HTTP status code
        """
        if scraper_name in self._scrapers:
            self._scrapers[scraper_name].total_errors += 1

        await self._rate_limiter.report_error(url, status_code)

    async def report_success(self, url: str):
        """Report successful request."""
        await self._rate_limiter.report_success(url)

    def pause_all(self):
        """Pause all scrapers."""
        self._is_paused = True
        self._pause_event.clear()

        for slot in self._scrapers.values():
            if slot.status == ScraperStatus.RUNNING:
                slot.status = ScraperStatus.PAUSED

        logger.warning("All scrapers paused")

    def resume_all(self):
        """Resume all scrapers."""
        self._is_paused = False
        self._pause_event.set()

        for slot in self._scrapers.values():
            if slot.status == ScraperStatus.PAUSED:
                slot.status = ScraperStatus.IDLE

        logger.info("All scrapers resumed")

    async def _on_dns_unhealthy(self):
        """Callback when DNS becomes unhealthy."""
        logger.error("DNS unhealthy - pausing all scrapers")
        self.pause_all()

    async def _on_dns_recovered(self):
        """Callback when DNS recovers."""
        logger.info("DNS recovered - resuming all scrapers")
        self.resume_all()

    @property
    def is_paused(self) -> bool:
        """Whether scrapers are paused."""
        return self._is_paused

    @property
    def dns_status(self) -> DNSHealthStatus:
        """Current DNS health status."""
        return self._dns_monitor.status

    def get_scraper_status(self, scraper_name: str) -> Optional[Dict]:
        """Get status for a specific scraper."""
        if scraper_name not in self._scrapers:
            return None

        slot = self._scrapers[scraper_name]
        return {
            "name": slot.name,
            "status": slot.status.value,
            "current": slot.current,
            "max_concurrent": slot.max_concurrent,
            "total_requests": slot.total_requests,
            "total_errors": slot.total_errors,
            "error_rate": f"{slot.total_errors / max(slot.total_requests, 1) * 100:.1f}%"
        }

    def get_stats(self) -> Dict:
        """Get coordinator statistics."""
        uptime = time.time() - self._start_time if self._start_time else 0

        scraper_stats = {
            name: self.get_scraper_status(name)
            for name in self._scrapers
        }

        global_current = sum(s.current for s in self._scrapers.values())

        return {
            "uptime_seconds": uptime,
            "is_paused": self._is_paused,
            "global_connections": {
                "current": global_current,
                "max": self.config.max_global_connections
            },
            "total_slots_acquired": self._total_slots_acquired,
            "total_slots_released": self._total_slots_released,
            "scrapers": scraper_stats,
            "dns": self._dns_resolver.get_stats(),
            "dns_monitor": self._dns_monitor.get_stats(),
            "rate_limiter": self._rate_limiter.get_stats()
        }

    async def close(self):
        """Clean up resources."""
        await self.stop_monitoring()
        await self._dns_resolver.close()


class SlotContext:
    """Context manager for slot acquisition."""

    def __init__(self, coordinator: ScrapingCoordinator, scraper_name: str):
        self._coordinator = coordinator
        self._scraper_name = scraper_name

    async def __aenter__(self):
        await self._coordinator.acquire_slot(self._scraper_name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._coordinator.release_slot(self._scraper_name)
        return False


# Singleton instance for global coordination
_global_coordinator: Optional[ScrapingCoordinator] = None


def get_coordinator(config: Optional[CoordinatorConfig] = None) -> ScrapingCoordinator:
    """
    Get or create global coordinator instance.

    Args:
        config: Configuration (only used on first call)

    Returns:
        Global ScrapingCoordinator instance
    """
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = ScrapingCoordinator(config)
    return _global_coordinator


def reset_coordinator():
    """Reset global coordinator (for testing)."""
    global _global_coordinator
    _global_coordinator = None
