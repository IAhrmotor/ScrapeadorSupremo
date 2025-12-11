"""DNS Health Monitor with automatic pause/resume of scrapers."""

import asyncio
import socket
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Awaitable
from enum import Enum


logger = logging.getLogger(__name__)


class DNSHealthStatus(Enum):
    """DNS health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    domain: str
    success: bool
    latency_ms: float
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class DNSMonitor:
    """
    Monitors DNS health and triggers callbacks when issues detected.

    Features:
    - Periodic health checks against test domains
    - Automatic status transitions (healthy -> degraded -> unhealthy)
    - Callback system for pause/resume notifications
    - Latency tracking for performance monitoring

    Usage:
        monitor = DNSMonitor()

        # Register callbacks
        monitor.on_unhealthy(pause_scrapers)
        monitor.on_recovered(resume_scrapers)

        # Start monitoring (runs in background)
        await monitor.start()

        # Stop monitoring
        await monitor.stop()
    """

    def __init__(
        self,
        check_interval: float = 30.0,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
        test_domains: Optional[List[str]] = None,
        timeout: float = 5.0
    ):
        """
        Initialize DNS monitor.

        Args:
            check_interval: Seconds between health checks
            failure_threshold: Consecutive failures to mark unhealthy
            recovery_threshold: Consecutive successes to mark recovered
            test_domains: Domains to test (defaults to critical services)
            timeout: Timeout per DNS lookup
        """
        self._check_interval = check_interval
        self._failure_threshold = failure_threshold
        self._recovery_threshold = recovery_threshold
        self._test_domains = test_domains or [
            "supabase.co",
            "google.com",
            "cloudflare.com"
        ]
        self._timeout = timeout

        # State
        self._status = DNSHealthStatus.HEALTHY
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

        # History
        self._history: List[HealthCheckResult] = []
        self._max_history = 100

        # Callbacks
        self._on_unhealthy: List[Callable[[], Awaitable[None]]] = []
        self._on_degraded: List[Callable[[], Awaitable[None]]] = []
        self._on_recovered: List[Callable[[], Awaitable[None]]] = []
        self._on_check: List[Callable[[HealthCheckResult], Awaitable[None]]] = []

    @property
    def status(self) -> DNSHealthStatus:
        """Current DNS health status."""
        return self._status

    @property
    def is_healthy(self) -> bool:
        """Whether DNS is currently healthy."""
        return self._status == DNSHealthStatus.HEALTHY

    @property
    def is_running(self) -> bool:
        """Whether monitor is currently running."""
        return self._is_running

    def on_unhealthy(self, callback: Callable[[], Awaitable[None]]):
        """Register callback for unhealthy status."""
        self._on_unhealthy.append(callback)

    def on_degraded(self, callback: Callable[[], Awaitable[None]]):
        """Register callback for degraded status."""
        self._on_degraded.append(callback)

    def on_recovered(self, callback: Callable[[], Awaitable[None]]):
        """Register callback for recovery."""
        self._on_recovered.append(callback)

    def on_check(self, callback: Callable[[HealthCheckResult], Awaitable[None]]):
        """Register callback for each health check."""
        self._on_check.append(callback)

    async def start(self):
        """Start monitoring in background."""
        if self._is_running:
            return

        self._is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("DNS Monitor started")

    async def stop(self):
        """Stop monitoring."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("DNS Monitor stopped")

    async def check_now(self) -> bool:
        """
        Perform immediate health check.

        Returns:
            True if DNS is healthy
        """
        return await self._perform_check()

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._is_running:
            try:
                await self._perform_check()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in DNS monitor loop: {e}")
                await asyncio.sleep(self._check_interval)

    async def _perform_check(self) -> bool:
        """Perform a single health check cycle."""
        results = []

        for domain in self._test_domains:
            result = await self._check_domain(domain)
            results.append(result)

            # Notify callbacks
            for callback in self._on_check:
                try:
                    await callback(result)
                except Exception as e:
                    logger.error(f"Error in on_check callback: {e}")

        # Calculate overall health
        successful = sum(1 for r in results if r.success)
        total = len(results)

        is_ok = successful >= (total // 2 + 1)  # Majority must succeed

        # Update consecutive counters
        if is_ok:
            self._consecutive_successes += 1
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
            self._consecutive_successes = 0

        # State transitions
        old_status = self._status
        await self._update_status()

        if old_status != self._status:
            logger.info(f"DNS status changed: {old_status.value} -> {self._status.value}")

        # Store history
        for result in results:
            self._add_to_history(result)

        return is_ok

    async def _check_domain(self, domain: str) -> HealthCheckResult:
        """Check a single domain."""
        start = time.time()

        try:
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.getaddrinfo(domain, 443, family=socket.AF_INET),
                timeout=self._timeout
            )

            latency = (time.time() - start) * 1000
            return HealthCheckResult(
                domain=domain,
                success=True,
                latency_ms=latency
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                domain=domain,
                success=False,
                latency_ms=self._timeout * 1000,
                error="Timeout"
            )
        except socket.gaierror as e:
            return HealthCheckResult(
                domain=domain,
                success=False,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )
        except Exception as e:
            return HealthCheckResult(
                domain=domain,
                success=False,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )

    async def _update_status(self):
        """Update health status based on consecutive counts."""
        old_status = self._status

        if self._consecutive_failures >= self._failure_threshold:
            self._status = DNSHealthStatus.UNHEALTHY
        elif self._consecutive_failures >= 1:
            self._status = DNSHealthStatus.DEGRADED
        elif self._consecutive_successes >= self._recovery_threshold:
            self._status = DNSHealthStatus.HEALTHY

        # Trigger callbacks on transitions
        if old_status != self._status:
            if self._status == DNSHealthStatus.UNHEALTHY:
                for callback in self._on_unhealthy:
                    try:
                        await callback()
                    except Exception as e:
                        logger.error(f"Error in on_unhealthy callback: {e}")

            elif self._status == DNSHealthStatus.DEGRADED:
                for callback in self._on_degraded:
                    try:
                        await callback()
                    except Exception as e:
                        logger.error(f"Error in on_degraded callback: {e}")

            elif self._status == DNSHealthStatus.HEALTHY and old_status != DNSHealthStatus.HEALTHY:
                for callback in self._on_recovered:
                    try:
                        await callback()
                    except Exception as e:
                        logger.error(f"Error in on_recovered callback: {e}")

    def _add_to_history(self, result: HealthCheckResult):
        """Add result to history, maintaining max size."""
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_stats(self) -> Dict:
        """Get monitor statistics."""
        recent_results = self._history[-10:] if self._history else []
        recent_success_rate = 0
        avg_latency = 0

        if recent_results:
            successful = sum(1 for r in recent_results if r.success)
            recent_success_rate = successful / len(recent_results) * 100
            latencies = [r.latency_ms for r in recent_results if r.success]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return {
            "status": self._status.value,
            "is_healthy": self.is_healthy,
            "is_running": self._is_running,
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
            "failure_threshold": self._failure_threshold,
            "recovery_threshold": self._recovery_threshold,
            "check_interval": self._check_interval,
            "test_domains": self._test_domains,
            "recent_success_rate": f"{recent_success_rate:.1f}%",
            "avg_latency_ms": f"{avg_latency:.1f}",
            "total_checks": len(self._history)
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get recent check history."""
        results = self._history[-limit:] if self._history else []
        return [
            {
                "domain": r.domain,
                "success": r.success,
                "latency_ms": r.latency_ms,
                "error": r.error,
                "timestamp": r.timestamp
            }
            for r in results
        ]
