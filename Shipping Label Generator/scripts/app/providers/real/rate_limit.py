from __future__ import annotations

import asyncio
from time import monotonic
from typing import Any

from app.logging.jsonl import JsonlLogger


class _SpacingRateLimiter:
    """
    Very small async rate limiter.

    This enforces an average request rate by spacing requests (no bursts).
    It is intentionally simple and dependency-free.
    """

    def __init__(self, requests_per_sec: float | None) -> None:
        rps = float(requests_per_sec) if requests_per_sec else 0.0
        self._interval = (1.0 / rps) if rps > 0.0 else 0.0
        self._lock = asyncio.Lock()
        self._next_at = 0.0

    async def acquire(self) -> None:
        if self._interval <= 0.0:
            return
        while True:
            delay = 0.0
            async with self._lock:
                now = monotonic()
                at = self._next_at
                if now >= at:
                    self._next_at = now + self._interval
                    return
                delay = at - now
            await asyncio.sleep(delay)


def _local_rate_limiter_from_cfg(*, rl: dict[str, Any], log: JsonlLogger) -> _SpacingRateLimiter:
    """
    Optional fixed spacing between requests (requests_per_sec).
    If unset, null, or <= 0: no in-process pacing — rely on max_workers semaphore + ShipStation 429 handling.
    """
    requests_per_sec = rl.get("requests_per_sec")
    rps_f: float | None = float(requests_per_sec) if requests_per_sec is not None else None
    if rps_f is not None and rps_f <= 0.0:
        rps_f = None

    lim = _SpacingRateLimiter(float(rps_f) if rps_f is not None else None)
    log.info(
        "provider_rate_limit_mode",
        extra={
            "mode": "spacing" if (rps_f is not None and rps_f > 0.0) else "none",
            "requests_per_sec": rps_f,
        },
    )
    return lim
