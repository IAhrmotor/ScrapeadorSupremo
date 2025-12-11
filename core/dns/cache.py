"""DNS Cache with LRU eviction and TTL support."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from collections import OrderedDict


@dataclass
class CacheEntry:
    """Single DNS cache entry with TTL."""
    ip: str
    created_at: float
    ttl: int

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl

    def time_remaining(self) -> float:
        """Get seconds until expiration."""
        remaining = self.ttl - (time.time() - self.created_at)
        return max(0, remaining)


class DNSCache:
    """
    LRU Cache with TTL for DNS resolutions.

    Features:
    - Thread-safe with asyncio.Lock
    - Automatic LRU eviction when max_entries reached
    - TTL-based expiration
    - Statistics tracking

    Usage:
        cache = DNSCache(ttl=300, max_entries=1000)

        # Set entry
        await cache.set("example.com", "93.184.216.34")

        # Get entry (returns None if expired or not found)
        ip = await cache.get("example.com")

        # Get stats
        stats = cache.get_stats()
    """

    def __init__(self, ttl: int = 300, max_entries: int = 1000):
        """
        Initialize DNS cache.

        Args:
            ttl: Time-to-live in seconds for each entry (default: 5 minutes)
            max_entries: Maximum number of entries before LRU eviction
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._ttl = ttl
        self._max_entries = max_entries
        self._lock = asyncio.Lock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0

    async def get(self, hostname: str) -> Optional[str]:
        """
        Get cached IP for hostname.

        Args:
            hostname: The hostname to look up

        Returns:
            Cached IP address or None if not found/expired
        """
        async with self._lock:
            if hostname not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[hostname]

            if entry.is_expired():
                del self._cache[hostname]
                self._expirations += 1
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(hostname)
            self._hits += 1
            return entry.ip

    async def set(self, hostname: str, ip: str, ttl: Optional[int] = None):
        """
        Cache IP for hostname.

        Args:
            hostname: The hostname to cache
            ip: The resolved IP address
            ttl: Optional custom TTL (uses default if not specified)
        """
        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self._max_entries:
                self._evict_oldest()

            self._cache[hostname] = CacheEntry(
                ip=ip,
                created_at=time.time(),
                ttl=ttl or self._ttl
            )
            # Move to end (most recently used)
            self._cache.move_to_end(hostname)

    async def remove(self, hostname: str) -> bool:
        """
        Remove entry from cache.

        Args:
            hostname: The hostname to remove

        Returns:
            True if entry was removed, False if not found
        """
        async with self._lock:
            if hostname in self._cache:
                del self._cache[hostname]
                return True
            return False

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired = [
                hostname for hostname, entry in self._cache.items()
                if entry.is_expired()
            ]
            for hostname in expired:
                del self._cache[hostname]
                self._expirations += 1
            return len(expired)

    def _evict_oldest(self):
        """Evict the least recently used entry (internal, must hold lock)."""
        if self._cache:
            self._cache.popitem(last=False)
            self._evictions += 1

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, evictions, etc.
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_entries": self._max_entries,
            "ttl": self._ttl,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "evictions": self._evictions,
            "expirations": self._expirations,
            "total_requests": total_requests
        }

    async def get_all_entries(self) -> Dict[str, Tuple[str, float]]:
        """
        Get all cache entries with remaining TTL.

        Returns:
            Dict mapping hostname to (ip, seconds_remaining)
        """
        async with self._lock:
            return {
                hostname: (entry.ip, entry.time_remaining())
                for hostname, entry in self._cache.items()
                if not entry.is_expired()
            }

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)

    def __contains__(self, hostname: str) -> bool:
        """Check if hostname is in cache (may be expired)."""
        return hostname in self._cache
