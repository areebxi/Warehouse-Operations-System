from __future__ import annotations
import base64
import os
import asyncio
import json
from dataclasses import dataclass
from time import monotonic
from typing import Any
import aiohttp
from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger
from app.models.label import Label
from app.models.order import Order
from app.models.shipment import Shipment
from app.providers.base import Provider

def _parse_retry_after_header(raw: str | None) -> float | None:
    """
    Parse Retry-After per RFC 7231: delay in seconds, or an HTTP-date after which to retry.
    Returns seconds to wait (>= 0), or None if the header is missing or unparsable.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        sec = float(s)
        if sec >= 0.0:
            return sec
    except ValueError:
        pass
    try:
        from datetime import datetime, timezone

        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0.0, (dt - now).total_seconds())
    except Exception:
        return None
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
class ProviderParseError(RuntimeError):
    method: str
    url: str
    status: int
    message: str
    body_snippet: str = ""
    expected: str = ""
    non_retryable: bool = True

    def __str__(self) -> str:
        bits = [f"ProviderParseError(method={self.method}, url={self.url}, status={self.status}"]
        if self.expected:
            bits.append(f"expected={self.expected}")
        bits.append(f"message={self.message})")
        return ", ".join(bits)
class ProviderHttpError(RuntimeError):
    method: str
    url: str
    status: int
    message: str
    retry_after: float | None = None

    def __str__(self) -> str:
        return f"ProviderHttpError(method={self.method}, url={self.url}, status={self.status}, message={self.message})"
class ProviderNonRetryableError(RuntimeError):
    message: str
    non_retryable: bool = True

    def __str__(self) -> str:
        return self.message
