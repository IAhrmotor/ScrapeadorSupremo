"""DNS management module with rotation, caching, and health monitoring."""

from .cache import DNSCache, CacheEntry
from .resolver import SmartDNSResolver, DNSConfig, DNSResolutionError, RotationStrategy
from .monitor import DNSMonitor, DNSHealthStatus, HealthCheckResult

__all__ = [
    # Cache
    "DNSCache",
    "CacheEntry",
    # Resolver
    "SmartDNSResolver",
    "DNSConfig",
    "DNSResolutionError",
    "RotationStrategy",
    # Monitor
    "DNSMonitor",
    "DNSHealthStatus",
    "HealthCheckResult",
]
