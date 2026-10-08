from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

import aiohttp

from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int
    retry_min_wait_sec: float
    retry_max_wait_sec: float
    request_timeout_sec: float
    label_timeout_sec: float
    rate_limit_fallback_wait_sec: float
    retry_jitter_pct: float


def _retry_cfg(cfg: AppConfig) -> RetryConfig:
    conc = cfg.raw.get("concurrency") or {}
    rl = cfg.raw.get("rate_limit") or {}
    jitter = (conc.get("retry_jitter_pct") if isinstance(conc, dict) else None)
    return RetryConfig(
        max_retries=int(conc.get("max_retries", 0)),
        retry_min_wait_sec=float(conc.get("retry_min_wait_sec", 1)),
        retry_max_wait_sec=float(conc.get("retry_max_wait_sec", 8)),
        request_timeout_sec=float(conc.get("request_timeout_sec", 15)),
        label_timeout_sec=float(conc.get("label_timeout_sec", 35)),
        rate_limit_fallback_wait_sec=float(rl.get("fallback_wait_sec", 60)),
        retry_jitter_pct=float(jitter) if jitter is not None else 0.25,
    )


def _timeout_for(op_kind: str, rc: RetryConfig) -> float:
    return rc.label_timeout_sec if op_kind == "label" else rc.request_timeout_sec


def _is_rate_limited(exc: BaseException) -> bool:
    status = getattr(exc, "status", None)
    if status == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg and "too many" in msg


def _http_status(exc: BaseException) -> int | None:
    status = getattr(exc, "status", None)
    try:
        return int(status) if status is not None else None
    except Exception:
        return None


def _is_non_retryable_http_4xx(exc: BaseException) -> bool:
    """HTTP 4xx other than 429 (and 408 Request Timeout) — do not retry."""
    status = _http_status(exc)
    if status is None:
        return False
    if status == 429:
        return False
    if status == 408:
        return False
    return 400 <= status <= 499


def _is_non_retryable(exc: BaseException) -> bool:
    return bool(getattr(exc, "non_retryable", False))


def _retry_after_seconds(exc: BaseException) -> float | None:
    ra = getattr(exc, "retry_after", None)
    if ra is None:
        return None
    try:
        return float(ra)
    except Exception:
        return None


def _backoff(attempt: int, *, rc: RetryConfig) -> float:
    # attempt: 1..N (1 is first retry wait)
    base = max(0.0, rc.retry_min_wait_sec) * math.pow(2.0, max(0, attempt - 1))
    return min(max(0.0, rc.retry_min_wait_sec), rc.retry_max_wait_sec) if base <= 0 else min(base, rc.retry_max_wait_sec)


def _apply_jitter(wait: float, *, jitter_pct: float) -> float:
    w = max(0.0, float(wait))
    j = max(0.0, float(jitter_pct))
    if w <= 0.0 or j <= 0.0:
        return w
    lo = max(0.0, 1.0 - j)
    hi = 1.0 + j
    return w * random.uniform(lo, hi)


async def call_with_retries(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    op: str,
    op_kind: str,
    fn: Callable[[], Awaitable[T]],
    extra: dict[str, Any] | None = None,
) -> T:
    """
    Per-call retry policy:
    - 429: sleep Retry-After (seconds) if present on the exception, else rate_limit.fallback_wait_sec; retry up to max_retries.
    - 5xx / asyncio timeout / aiohttp client errors / HTTP 408: exponential backoff (retry_min * 2^n capped at retry_max); retry up to max_retries.
    - Other 4xx (except above): fail immediately.
    Shared retry budget (max_retries) across 429 and transient failures for this invocation.
    """
    rc = _retry_cfg(cfg)
    timeout = _timeout_for(op_kind, rc)
    attempt_total = 0
    attempt_retryable = 0

    while True:
        try:
            return await asyncio.wait_for(fn(), timeout=timeout)
        except Exception as e:
            attempt_total += 1
            if _is_non_retryable(e):
                log.error(
                    "provider_call_failed",
                    extra={
                        **(extra or {}),
                        "op": op,
                        "attempt_total": attempt_total,
                        "attempt_retryable": attempt_retryable,
                        "max_retries": rc.max_retries,
                        "reason": "non_retryable",
                    },
                    exc=e,
                )
                raise
            if _is_non_retryable_http_4xx(e):
                log.error(
                    "provider_call_failed",
                    extra={
                        **(extra or {}),
                        "op": op,
                        "attempt_total": attempt_total,
                        "attempt_retryable": attempt_retryable,
                        "max_retries": rc.max_retries,
                        "reason": "non_retryable_4xx",
                    },
                    exc=e,
                )
                raise

            attempt_retryable += 1
            if attempt_retryable > rc.max_retries:
                log.error(
                    "provider_call_failed",
                    extra={
                        **(extra or {}),
                        "op": op,
                        "attempt_total": attempt_total,
                        "attempt_retryable": attempt_retryable,
                        "max_retries": rc.max_retries,
                        "reason": "max_retries_exceeded",
                    },
                    exc=e,
                )
                raise e

            if _is_rate_limited(e):
                ra_sec = _retry_after_seconds(e)
                if ra_sec is not None:
                    wait = float(ra_sec)
                    wait_basis = "retry_after_header"
                else:
                    wait = float(rc.rate_limit_fallback_wait_sec)
                    wait_basis = "fallback_wait_sec"
                reason = "rate_limited"
            elif isinstance(e, (asyncio.TimeoutError, TimeoutError)) or isinstance(e, aiohttp.ClientError):
                wait_base = _backoff(attempt_retryable, rc=rc)
                wait = _apply_jitter(wait_base, jitter_pct=rc.retry_jitter_pct)
                reason = "retry_backoff"
                wait_basis = "transient_network"
            else:
                # 5xx and unknown transient HTTP from ProviderHttpError, etc.
                wait_base = _backoff(attempt_retryable, rc=rc)
                wait = _apply_jitter(wait_base, jitter_pct=rc.retry_jitter_pct)
                reason = "retry_backoff"
                wait_basis = "transient_http_or_other"

            log.warning(
                "provider_call_retrying",
                extra={
                    **(extra or {}),
                    "op": op,
                    "attempt_total": attempt_total,
                    "attempt_retryable": attempt_retryable,
                    "wait_sec": wait,
                    "reason": reason,
                    "wait_basis": wait_basis,
                },
            )
            await asyncio.sleep(wait)
