from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from aiohttp import web

from scripts.app.config.load import AppConfig


@asynccontextmanager
async def aio_test_server(routes: web.RouteTableDef) -> AsyncIterator[str]:
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="127.0.0.1", port=0)
    await site.start()
    sockets = site._server.sockets  # type: ignore[attr-defined]
    port = int(sockets[0].getsockname()[1])
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


def make_cfg() -> AppConfig:
    raw: dict[str, Any] = {
        "paths": {
            "logs_dir": "Logs",
            "output_dir": "Output",
            "orders_csv": "Order Numbers.csv",
            "desfiles_dir": "DTF Des Files",
            "void_csv": "Void Label Input/void_labels.csv",
        },
        "logging": {
            "level": "INFO",
            "redact_keys": ["labelData", "Authorization", "apiKey", "apiSecret"],
        },
        "concurrency": {
            "max_workers": 5,
            "max_retries": 0,
            "request_timeout_sec": 15,
            "label_timeout_sec": 35,
            "retry_min_wait_sec": 1,
            "retry_max_wait_sec": 8,
        },
        "rate_limit": {"fallback_wait_sec": 60},
        "provider": {
            "label_format": "PDF",
            "label_layout": "4x6",
            "label_download_type": "inline",
        },
    }
    return AppConfig(raw=raw, provider_name="real")


def make_cfg_with(*, raw_overrides: dict[str, Any]) -> AppConfig:
    base = make_cfg().raw
    merged: dict[str, Any] = dict(base)
    for k, v in raw_overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return AppConfig(raw=merged, provider_name="real")


def set_env(base_url: str) -> None:
    os.environ["REAL_API_BASE_URL"] = base_url
    os.environ["REAL_API_KEY"] = "k"
    os.environ["REAL_API_SECRET"] = "s"
