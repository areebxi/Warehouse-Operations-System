"""Real ShipStation provider — stable façade."""

from __future__ import annotations

from app.providers.real.provider_impl1 import RealProvider
from app.providers.real.provider_impl2 import (
    ProviderHttpError,
    ProviderNonRetryableError,
    ProviderParseError,
    _SpacingRateLimiter,
    _local_rate_limiter_from_cfg,
    _parse_retry_after_header,
)

__all__ = [
    "RealProvider",
    "ProviderHttpError",
    "ProviderNonRetryableError",
    "ProviderParseError",
    "_SpacingRateLimiter",
    "_local_rate_limiter_from_cfg",
    "_parse_retry_after_header",
]
