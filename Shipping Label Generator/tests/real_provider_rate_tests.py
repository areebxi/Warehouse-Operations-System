from __future__ import annotations

import asyncio
import os
from time import monotonic

import pytest
from aiohttp import web

from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import (
    ProviderHttpError,
    RealProvider,
    _SpacingRateLimiter,
    _parse_retry_after_header,
)
from real_provider_helpers import make_cfg as cfg, make_cfg_with as cfg_with, set_env, aio_test_server


def test_second_lookup_orders_not_delayed_after_bare_429() -> None:
    """Second HTTP request is not blocked by a provider-wide cooldown after a raw 429."""
    routes = web.RouteTableDef()
    calls = {"n": 0}

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return web.Response(status=429, headers={"Retry-After": "5"}, text="Too Many Requests")
        return web.json_response({"orders": []})

    async def run() -> None:
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
            try:
                with pytest.raises(ProviderHttpError) as e:
                    await rp.lookup_orders("ABC123")
                assert e.value.status == 429
                t0 = monotonic()
                await rp.lookup_orders("ABC123")
                assert monotonic() - t0 < 0.5
            finally:
                await rp.aclose()

    asyncio.run(run())
    assert calls["n"] == 2

def test_parse_retry_after_header_seconds() -> None:
    assert _parse_retry_after_header("0") == 0.0
    assert _parse_retry_after_header("2.5") == 2.5
    assert _parse_retry_after_header("  120  ") == 120.0
    assert _parse_retry_after_header(None) is None
    assert _parse_retry_after_header("") is None

def test_parse_retry_after_header_http_date() -> None:
    # Far past: should clamp to 0s wait
    assert _parse_retry_after_header("Thu, 01 Jan 1970 00:00:00 GMT") == 0.0

def test_requests_per_sec_positive_uses_spacing_limiter() -> None:
    os.environ["REAL_API_BASE_URL"] = "http://127.0.0.1:9"
    os.environ["REAL_API_KEY"] = "k"
    os.environ["REAL_API_SECRET"] = "s"
    app_cfg = cfg_with(
        raw_overrides={
            "rate_limit": {
                **(cfg().raw.get("rate_limit") or {}),
                "requests_per_sec": 2.0,
            }
        }
    )
    rp = RealProvider(app_cfg, JsonlLogger.from_config(app_cfg))
    try:
        assert isinstance(rp._rate_limiter, _SpacingRateLimiter)
        assert rp._rate_limiter._interval > 0.0
    finally:
        asyncio.run(rp.aclose())

def test_no_requests_per_sec_disables_in_process_pacing() -> None:
    os.environ["REAL_API_BASE_URL"] = "http://127.0.0.1:9"
    os.environ["REAL_API_KEY"] = "k"
    os.environ["REAL_API_SECRET"] = "s"
    app_cfg = cfg()
    rp = RealProvider(app_cfg, JsonlLogger.from_config(app_cfg))
    try:
        assert isinstance(rp._rate_limiter, _SpacingRateLimiter)
        assert rp._rate_limiter._interval == 0.0
    finally:
        asyncio.run(rp.aclose())

