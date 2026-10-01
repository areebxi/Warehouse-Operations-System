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

def test_list_shipments_filters_voided_and_sorts() -> None:
    routes = web.RouteTableDef()

    @routes.get("/shipments")
    async def shipments(request: web.Request) -> web.Response:
        assert request.query.get("orderId") == "99"
        assert request.query.get("pageSize") == "5"
        return web.json_response(
            {
                "shipments": [
                    {"shipmentId": 10, "orderId": 99, "voided": True},
                    {"shipmentId": 12, "orderId": 99, "voided": False},
                    {"shipmentId": 11, "orderId": 99, "voided": False},
                ]
            }
        )

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                out = await rp.list_shipments(99, include_voided=False, page_size=5)
                assert [s.shipmentId for s in out] == [12, 11]
            finally:
                await rp.aclose()

    asyncio.run(run())
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
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
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
def test_fetch_label_uses_labeldownload_href_when_no_labeldata() -> None:
    routes = web.RouteTableDef()

    pdf_bytes = b"%PDF-1.4\n%TEST\n%%EOF\n"

    @routes.get("/shipments/123/label")
    async def label(request: web.Request) -> web.Response:
        return web.json_response({"labelDownload": {"href": "/labels/123.pdf"}, "trackingNumber": "T1"})

    @routes.get("/labels/123.pdf")
    async def label_pdf(request: web.Request) -> web.Response:
        return web.Response(body=pdf_bytes, content_type="application/pdf")

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                out = await rp.fetch_label(123)
                assert out is not None
                assert out.trackingNumber == "T1"
                assert base64.b64decode(out.labelData.encode("ascii")) == pdf_bytes
            finally:
                await rp.aclose()

    asyncio.run(run())
def test_list_shipments_each_call_hits_api() -> None:
    """No in-memory cache: identical calls still issue two GET /shipments requests."""
    routes = web.RouteTableDef()
    calls = {"n": 0}

    @routes.get("/shipments")
    async def shipments(request: web.Request) -> web.Response:
        calls["n"] += 1
        assert request.query.get("orderId") == "99"
        return web.json_response({"shipments": [{"shipmentId": 1, "orderId": 99, "voided": False}]})

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                a = await rp.list_shipments(99, include_voided=False, page_size=10)
                b = await rp.list_shipments(99, include_voided=False, page_size=10)
                assert len(a) == 1 and len(b) == 1
                assert a[0].shipmentId == b[0].shipmentId
                assert calls["n"] == 2
            finally:
                await rp.aclose()

    asyncio.run(run())
def test_provider_http_error_exposes_retry_after() -> None:
    routes = web.RouteTableDef()

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        return web.Response(status=429, headers={"Retry-After": "2"}, text="Too Many Requests")

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                try:
                    await rp.lookup_orders("ABC123")
                    assert False, "expected ProviderHttpError"
                except ProviderHttpError as e:
                    assert e.status == 429
                    assert e.retry_after == 2.0
                    assert e.method == "GET"
                    assert "/orders" in e.url
            finally:
                await rp.aclose()

    asyncio.run(run())
def test_void_label_posts_payload() -> None:
    routes = web.RouteTableDef()
    seen: dict[str, Any] = {}

    @routes.post("/shipments/voidlabel")
    async def void(request: web.Request) -> web.Response:
        seen["json"] = await request.json()
        return web.json_response({"ok": True})

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                await rp.void_label(777)
                assert seen["json"] == {"shipmentId": 777}
            finally:
                await rp.aclose()

    asyncio.run(run())
def test_parse_retry_after_header_http_date() -> None:
    # Far past: should clamp to 0s wait
    assert _parse_retry_after_header("Thu, 01 Jan 1970 00:00:00 GMT") == 0.0
