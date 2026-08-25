from __future__ import annotations

import asyncio
from time import monotonic
from typing import Any

import pytest

from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import ProviderHttpError
from scripts.app.providers.real.provider import ProviderNonRetryableError
from scripts.app.util.retries import call_with_retries


def _cfg(*, max_retries: int) -> AppConfig:
    raw: dict[str, Any] = {
        "paths": {"logs_dir": "logs", "output_dir": "output", "orders_csv": "Order Numbers.csv", "desfiles_dir": "DTF Des Files", "void_csv": "void label input/void_labels.csv"},
        "logging": {"level": "INFO", "redact_keys": []},
        "concurrency": {
            "max_workers": 2,
            "max_retries": max_retries,
            "request_timeout_sec": 5,
            "label_timeout_sec": 5,
            "retry_min_wait_sec": 0.01,
            "retry_max_wait_sec": 0.02,
            # Keep sleeps deterministic for timing assertions in tests.
            "retry_jitter_pct": 0.0,
        },
        "rate_limit": {
            "fallback_wait_sec": 0.01,
        },
        "provider": {"label_download_type": "inline"},
    }
    return AppConfig(raw=raw, provider_name="real")


def test_non_429_4xx_fails_immediately_no_retry() -> None:
    cfg = _cfg(max_retries=3)
    log = JsonlLogger.from_config(cfg)
    attempts = {"n": 0}

    async def fn() -> Any:
        attempts["n"] += 1
        raise ProviderHttpError(method="GET", url="http://example.test/orders", status=400, message="Bad Request")

    async def run() -> None:
        with pytest.raises(ProviderHttpError) as e:
            await call_with_retries(cfg=cfg, log=log, op="test", op_kind="request", fn=fn, extra={"x": 1})
        assert e.value.status == 400

    asyncio.run(run())
    assert attempts["n"] == 1


def test_non_retryable_exception_fails_immediately_no_retry() -> None:
    cfg = _cfg(max_retries=3)
    log = JsonlLogger.from_config(cfg)
    attempts = {"n": 0}

    async def fn() -> Any:
        attempts["n"] += 1
        raise ProviderNonRetryableError("no labelData in response")

    async def run() -> None:
        with pytest.raises(ProviderNonRetryableError):
            await call_with_retries(cfg=cfg, log=log, op="test", op_kind="label", fn=fn, extra={"x": 1})

    asyncio.run(run())
    assert attempts["n"] == 1


def test_429_honors_retry_after_then_succeeds() -> None:
    cfg = _cfg(max_retries=3)
    log = JsonlLogger.from_config(cfg)
    attempts = {"n": 0}

    async def fn() -> Any:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ProviderHttpError(
                method="GET",
                url="http://example.test/orders",
                status=429,
                message="Too Many Requests",
                retry_after=0.03,
            )
        return {"ok": True}

    async def run() -> None:
        t0 = monotonic()
        out = await call_with_retries(cfg=cfg, log=log, op="test", op_kind="request", fn=fn, extra={"x": 1})
        dt = monotonic() - t0
        assert out == {"ok": True}
        assert dt >= 0.03

    asyncio.run(run())
    assert attempts["n"] == 2


def test_429_uses_fallback_when_no_retry_after() -> None:
    cfg = _cfg(max_retries=3)
    log = JsonlLogger.from_config(cfg)
    attempts = {"n": 0}

    async def fn() -> Any:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ProviderHttpError(
                method="GET",
                url="http://example.test/orders",
                status=429,
                message="Too Many Requests",
                retry_after=None,
            )
        return {"ok": True}

    async def run() -> None:
        t0 = monotonic()
        out = await call_with_retries(cfg=cfg, log=log, op="test", op_kind="request", fn=fn, extra={"x": 1})
        dt = monotonic() - t0
        assert out == {"ok": True}
        assert dt >= 0.01

    asyncio.run(run())
    assert attempts["n"] == 2


def test_429_exhausts_max_retries() -> None:
    cfg = _cfg(max_retries=2)
    log = JsonlLogger.from_config(cfg)
    attempts = {"n": 0}

    async def fn() -> Any:
        attempts["n"] += 1
        raise ProviderHttpError(
            method="GET",
            url="http://example.test/orders",
            status=429,
            message="Too Many Requests",
            retry_after=0.01,
        )

    async def run() -> None:
        with pytest.raises(ProviderHttpError) as e:
            await call_with_retries(cfg=cfg, log=log, op="test", op_kind="request", fn=fn, extra={"x": 1})
        assert e.value.status == 429

    asyncio.run(run())
    assert attempts["n"] == 3


def test_503_exponential_backoff_then_succeeds() -> None:
    cfg = _cfg(max_retries=3)
    log = JsonlLogger.from_config(cfg)
    attempts = {"n": 0}

    async def fn() -> Any:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise ProviderHttpError(method="GET", url="http://example.test/orders", status=503, message="Service Unavailable")
        return {"ok": True}

    async def run() -> None:
        out = await call_with_retries(cfg=cfg, log=log, op="test", op_kind="request", fn=fn, extra={"x": 1})
        assert out == {"ok": True}

    asyncio.run(run())
    assert attempts["n"] == 2
