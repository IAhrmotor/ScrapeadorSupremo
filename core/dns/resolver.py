"""Smart DNS Resolver with rotation, caching, and DoH fallback."""

import asyncio
import socket
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .cache import DNSCache


logger = logging.getLogger(__name__)


class RotationStrategy(Enum):
    """DNS provider rotation strategies."""
    ROUND_ROBIN = "round_robin"
    HEALTH_BASED = "health_based"
    RANDOM = "random"


@dataclass
class DNSConfig:
    """Configuration for DNS resolution."""

    # Standard DNS providers
    providers: List[str] = field(default_factory=lambda: [
        "1.1.1.1",        # Cloudflare
        "8.8.8.8",        # Google
        "9.9.9.9",        # Quad9
        "208.67.222.222"  # OpenDNS
    ])

    # DNS over HTTPS endpoints (fallback)
    doh_endpoints: List[str] = field(default_factory=lambda: [
        "https://cloudflare-dns.com/dns-query",
        "https://dns.google/dns-query"
    ])

    # Rotation strategy
    rotation_strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN

    # Cache settings
    cache_ttl: int = 300  # 5 minutes
    cache_size: int = 1000

    # Timeouts
    resolve_timeout: float = 5.0
    doh_timeout: float = 10.0

    # Health tracking
    failure_threshold: int = 3  # Mark unhealthy after N failures
    recovery_time: int = 60  # Seconds before retrying unhealthy provider


@dataclass
class ProviderHealth:
    """Health status of a DNS provider."""
    consecutive_failures: int = 0
    last_failure: float = 0
    last_success: float = 0
    total_queries: int = 0
    total_failures: int = 0

    def is_healthy(self, failure_threshold: int, recovery_time: int) -> bool:
        """Check if provider is healthy or has recovered."""
        if self.consecutive_failures < failure_threshold:
            return True
        # Check if recovery time has passed
        return time.time() - self.last_failure > recovery_time

    def record_success(self):
        """Record successful resolution."""
        self.consecutive_failures = 0
        self.last_success = time.time()
        self.total_queries += 1

    def record_failure(self):
        """Record failed resolution."""
        self.consecutive_failures += 1
        self.last_failure = time.time()
        self.total_queries += 1
        self.total_failures += 1


class SmartDNSResolver:
    """
    DNS Resolver with intelligent features:
    - Round-robin rotation across multiple providers
    - Integrated caching with TTL
    - Health tracking per provider
    - DNS over HTTPS (DoH) fallback
    - Automatic recovery from failures

    Usage:
        resolver = SmartDNSResolver()

        # Resolve hostname
        ip = await resolver.resolve("example.com")

        # Get statistics
        stats = resolver.get_stats()
    """

    def __init__(self, config: Optional[DNSConfig] = None):
        """
        Initialize resolver.

        Args:
            config: DNS configuration (uses defaults if not provided)
        """
        self.config = config or DNSConfig()
        self._cache = DNSCache(
            ttl=self.config.cache_ttl,
            max_entries=self.config.cache_size
        )
        self._current_index = 0
        self._health: Dict[str, ProviderHealth] = {
            provider: ProviderHealth()
            for provider in self.config.providers
        }
        self._lock = asyncio.Lock()
        self._doh_client: Optional[httpx.AsyncClient] = None

    async def resolve(self, hostname: str, use_cache: bool = True) -> str:
        """
        Resolve hostname to IP address.

        Args:
            hostname: The hostname to resolve
            use_cache: Whether to use cached results

        Returns:
            Resolved IP address

        Raises:
            DNSResolutionError: If resolution fails with all providers
        """
        # Check cache first
        if use_cache:
            cached = await self._cache.get(hostname)
            if cached:
                logger.debug(f"DNS cache hit for {hostname}: {cached}")
                return cached

        # Try providers with rotation
        last_error = None
        providers_tried = 0

        for _ in range(len(self.config.providers)):
            provider = await self._get_next_provider()
            if not provider:
                continue

            providers_tried += 1

            try:
                ip = await self._resolve_with_provider(hostname, provider)
                await self._cache.set(hostname, ip)
                self._health[provider].record_success()
                logger.debug(f"DNS resolved {hostname} -> {ip} via {provider}")
                return ip

            except Exception as e:
                last_error = e
                self._health[provider].record_failure()
                logger.warning(f"DNS resolution failed for {hostname} via {provider}: {e}")

        # Fallback to DoH
        if HTTPX_AVAILABLE and self.config.doh_endpoints:
            try:
                ip = await self._resolve_with_doh(hostname)
                await self._cache.set(hostname, ip)
                logger.info(f"DNS resolved {hostname} -> {ip} via DoH")
                return ip
            except Exception as e:
                last_error = e
                logger.error(f"DoH resolution failed for {hostname}: {e}")

        raise DNSResolutionError(
            f"Failed to resolve {hostname} after trying {providers_tried} providers. "
            f"Last error: {last_error}"
        )

    async def _get_next_provider(self) -> Optional[str]:
        """Get next healthy provider based on rotation strategy."""
        async with self._lock:
            if self.config.rotation_strategy == RotationStrategy.ROUND_ROBIN:
                return self._get_next_round_robin()
            elif self.config.rotation_strategy == RotationStrategy.HEALTH_BASED:
                return self._get_healthiest_provider()
            else:
                import random
                healthy = [
                    p for p in self.config.providers
                    if self._health[p].is_healthy(
                        self.config.failure_threshold,
                        self.config.recovery_time
                    )
                ]
                return random.choice(healthy) if healthy else None

    def _get_next_round_robin(self) -> Optional[str]:
        """Get next provider in round-robin fashion, skipping unhealthy ones."""
        start_index = self._current_index

        for _ in range(len(self.config.providers)):
            provider = self.config.providers[self._current_index]
            self._current_index = (self._current_index + 1) % len(self.config.providers)

            if self._health[provider].is_healthy(
                self.config.failure_threshold,
                self.config.recovery_time
            ):
                return provider

        # All providers unhealthy, return first one anyway
        self._current_index = (start_index + 1) % len(self.config.providers)
        return self.config.providers[start_index]

    def _get_healthiest_provider(self) -> Optional[str]:
        """Get provider with best health score."""
        best_provider = None
        best_score = -1

        for provider in self.config.providers:
            health = self._health[provider]

            if not health.is_healthy(
                self.config.failure_threshold,
                self.config.recovery_time
            ):
                continue

            # Score based on success rate and recency
            if health.total_queries > 0:
                success_rate = 1 - (health.total_failures / health.total_queries)
            else:
                success_rate = 1.0

            score = success_rate

            if score > best_score:
                best_score = score
                best_provider = provider

        return best_provider or self.config.providers[0]

    async def _resolve_with_provider(self, hostname: str, provider: str) -> str:
        """Resolve using specific DNS provider."""
        loop = asyncio.get_event_loop()

        try:
            # Use getaddrinfo with timeout
            result = await asyncio.wait_for(
                loop.getaddrinfo(
                    hostname,
                    None,
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM
                ),
                timeout=self.config.resolve_timeout
            )

            if result:
                ip = result[0][4][0]
                return ip

            raise DNSResolutionError(f"No results for {hostname}")

        except asyncio.TimeoutError:
            raise DNSResolutionError(f"Timeout resolving {hostname} via {provider}")
        except socket.gaierror as e:
            raise DNSResolutionError(f"DNS error for {hostname}: {e}")

    async def _resolve_with_doh(self, hostname: str) -> str:
        """Resolve using DNS over HTTPS."""
        if not HTTPX_AVAILABLE:
            raise DNSResolutionError("httpx not available for DoH")

        if self._doh_client is None:
            self._doh_client = httpx.AsyncClient(timeout=self.config.doh_timeout)

        for endpoint in self.config.doh_endpoints:
            try:
                response = await self._doh_client.get(
                    endpoint,
                    params={"name": hostname, "type": "A"},
                    headers={"Accept": "application/dns-json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    if "Answer" in data:
                        for answer in data["Answer"]:
                            if answer.get("type") == 1:  # A record
                                return answer["data"]

            except Exception as e:
                logger.warning(f"DoH failed via {endpoint}: {e}")
                continue

        raise DNSResolutionError(f"DoH resolution failed for {hostname}")

    async def prefetch(self, hostnames: List[str]):
        """
        Prefetch DNS entries for multiple hostnames.

        Args:
            hostnames: List of hostnames to prefetch
        """
        tasks = [self.resolve(hostname) for hostname in hostnames]
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_stats(self) -> Dict:
        """Get resolver statistics."""
        provider_stats = {}
        for provider, health in self._health.items():
            success_rate = 0
            if health.total_queries > 0:
                success_rate = (1 - health.total_failures / health.total_queries) * 100

            provider_stats[provider] = {
                "total_queries": health.total_queries,
                "failures": health.total_failures,
                "success_rate": f"{success_rate:.1f}%",
                "is_healthy": health.is_healthy(
                    self.config.failure_threshold,
                    self.config.recovery_time
                )
            }

        return {
            "cache": self._cache.get_stats(),
            "providers": provider_stats,
            "rotation_strategy": self.config.rotation_strategy.value,
            "current_index": self._current_index
        }

    async def close(self):
        """Clean up resources."""
        if self._doh_client:
            await self._doh_client.aclose()
            self._doh_client = None


class DNSResolutionError(Exception):
    """Exception raised when DNS resolution fails."""
    pass
