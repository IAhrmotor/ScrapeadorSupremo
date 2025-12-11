"""Network management module with coordination and rate limiting."""

from .coordinator import (
    ScrapingCoordinator,
    CoordinatorConfig,
    ScraperSlot,
    ScraperStatus,
    SlotContext,
    get_coordinator,
    reset_coordinator
)
from .limiter import (
    DomainRateLimiter,
    AdaptiveRateLimiter,
    DomainStats
)

__all__ = [
    # Coordinator
    "ScrapingCoordinator",
    "CoordinatorConfig",
    "ScraperSlot",
    "ScraperStatus",
    "SlotContext",
    "get_coordinator",
    "reset_coordinator",
    # Limiter
    "DomainRateLimiter",
    "AdaptiveRateLimiter",
    "DomainStats",
]
