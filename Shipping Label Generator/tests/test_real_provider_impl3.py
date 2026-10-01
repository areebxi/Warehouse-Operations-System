from __future__ import annotations
import asyncio
import base64
import os
from contextlib import asynccontextmanager
from time import monotonic
from typing import Any, AsyncIterator
import pytest
from aiohttp import web
from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import (
    ProviderHttpError,
    ProviderParseError,
    RealProvider,
    _SpacingRateLimiter,
    _parse_retry_after_header,
)

def test_fetch_label_returns_none_on_404() -> None:
    routes = web.RouteTableDef()

    @routes.get("/shipments/{sid}/label")
    async def label(request: web.Request) -> web.Response:
        raise web.HTTPNotFound()

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                out = await rp.fetch_label(123)
                assert out is None
            finally:
                await rp.aclose()

    asyncio.run(run())
def test_requests_per_sec_positive_uses_spacing_limiter() -> None:
    os.environ["REAL_API_BASE_URL"] = "http://127.0.0.1:9"
    os.environ["REAL_API_KEY"] = "k"
    os.environ["REAL_API_SECRET"] = "s"
    cfg = _cfg_with(
        raw_overrides={
            "rate_limit": {
                **(_cfg().raw.get("rate_limit") or {}),
                "requests_per_sec": 2.0,
            }
        }
    )
    rp = RealProvider(cfg, JsonlLogger.from_config(cfg))
    try:
        assert isinstance(rp._rate_limiter, _SpacingRateLimiter)
        assert rp._rate_limiter._interval > 0.0
    finally:
        asyncio.run(rp.aclose())
async def _test_server(routes: web.RouteTableDef) -> AsyncIterator[str]:
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="127.0.0.1", port=0)
    await site.start()
    # Discover bound port
    sockets = site._server.sockets  # type: ignore[attr-defined]
    port = int(sockets[0].getsockname()[1])
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()
def test_no_requests_per_sec_disables_in_process_pacing() -> None:
    os.environ["REAL_API_BASE_URL"] = "http://127.0.0.1:9"
    os.environ["REAL_API_KEY"] = "k"
    os.environ["REAL_API_SECRET"] = "s"
    cfg = _cfg()
    rp = RealProvider(cfg, JsonlLogger.from_config(cfg))
    try:
        assert isinstance(rp._rate_limiter, _SpacingRateLimiter)
        assert rp._rate_limiter._interval == 0.0
    finally:
        asyncio.run(rp.aclose())
def _cfg() -> AppConfig:
    # Minimal config for provider init.
    raw: dict[str, Any] = {
        "paths": {"logs_dir": "Logs", "output_dir": "Output", "orders_csv": "Order Numbers.csv", "desfiles_dir": "DTF Des Files", "void_csv": "Void Label Input/void_labels.csv"},
        "logging": {"level": "INFO", "redact_keys": ["labelData", "Authorization", "apiKey", "apiSecret"]},
        "concurrency": {"max_workers": 5, "max_retries": 0, "request_timeout_sec": 15, "label_timeout_sec": 35, "retry_min_wait_sec": 1, "retry_max_wait_sec": 8},
        "rate_limit": {"fallback_wait_sec": 60},
        "provider": {"label_format": "PDF", "label_layout": "4x6", "label_download_type": "inline"},
    }
    return AppConfig(raw=raw, provider_name="real")
def _cfg_with(*, raw_overrides: dict[str, Any]) -> AppConfig:
    base = _cfg().raw
    merged: dict[str, Any] = dict(base)
    for k, v in raw_overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return AppConfig(raw=merged, provider_name="real")
def test_parse_retry_after_header_seconds() -> None:
    assert _parse_retry_after_header("0") == 0.0
    assert _parse_retry_after_header("2.5") == 2.5
    assert _parse_retry_after_header("  120  ") == 120.0
    assert _parse_retry_after_header(None) is None
    assert _parse_retry_after_header("") is None
