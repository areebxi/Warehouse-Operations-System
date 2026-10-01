from __future__ import annotations
import asyncio
import math
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar
import aiohttp
from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger

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
