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


@asynccontextmanager
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


def test_lookup_orders_parses_all_matches() -> None:
    routes = web.RouteTableDef()

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        assert request.query.get("orderNumber") == "ABC123"
        assert request.query.get("pageSize") == "100"
        return web.json_response(
            {
                "orders": [
                    {
                        "orderId": 1,
                        "orderNumber": "ABC123",
                        "customerName": "Alice",
                        "requestedShippingService": "TestSvc",
                        "items": [{"weight": 1.0, "weightUnit": "lb", "quantity": 1}],
                    },
                    {
                        "orderId": 2,
                        "orderNumber": "ABC123",
                        "shipTo": {"name": "Bob"},
                        "items": [],
                    },
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
                out = await rp.lookup_orders("ABC123")
                assert [o.orderId for o in out] == [1, 2]
                assert out[0].customerName == "Alice"
                assert out[1].customerName == "Bob"
            finally:
                await rp.aclose()

    asyncio.run(run())


def test_lookup_orders_parses_order_status() -> None:
    routes = web.RouteTableDef()

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "orders": [
                    {
                        "orderId": 9,
                        "orderNumber": "CANCEL-1",
                        "orderStatus": "cancelled",
                    }
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
                out = await rp.lookup_orders("CANCEL-1")
                assert len(out) == 1
                assert out[0].orderStatus == "cancelled"
            finally:
                await rp.aclose()

    asyncio.run(run())


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


def test_create_label_requires_labeldata() -> None:
    routes = web.RouteTableDef()

    @routes.post("/orders/createlabelfororder")
    async def create(request: web.Request) -> web.Response:
        payload = await request.json()
        # Ensure the provider forces inline.
        assert payload["labelDownloadType"] == "inline"
        return web.json_response({"trackingNumber": "T1"})

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                orders = await rp.lookup_orders("ABC123") if False else []
                from scripts.app.models.order import Order

                try:
                    await rp.create_label(
                        order=Order(orderId=1, orderNumber="ABC123"),
                        carrier_code="c",
                        service_code="s",
                        package_code="p",
                        ship_date="2026-01-01",
                        weight=None,
                        weight_unit=None,
                        customer_reference=None,
                    )
                    assert False, "expected error"
                except RuntimeError as e:
                    assert "no labelData" in str(e)
            finally:
                await rp.aclose()

    asyncio.run(run())


def test_create_label_returns_base64_labeldata() -> None:
    routes = web.RouteTableDef()

    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    label_b64 = base64.b64encode(pdf_bytes).decode("ascii")

    @routes.post("/orders/createlabelfororder")
    async def create(request: web.Request) -> web.Response:
        payload = await request.json()
        assert payload["labelDownloadType"] == "inline"
        return web.json_response({"labelData": label_b64, "trackingNumber": "T123"})

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            from scripts.app.models.order import Order

            try:
                lbl = await rp.create_label(
                    order=Order(orderId=1, orderNumber="ABC123"),
                    carrier_code="c",
                    service_code="s",
                    package_code="p",
                    ship_date="2026-01-01",
                    weight=1.2,
                    weight_unit="lb",
                    customer_reference="REF",
                )
                assert lbl.labelData == label_b64
                assert lbl.trackingNumber == "T123"
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


def test_lookup_orders_unexpected_shape_raises_parse_error_with_details() -> None:
    routes = web.RouteTableDef()

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        return web.json_response({"orders": "not-a-list"})

    async def run() -> None:
        async with _test_server(routes) as base_url:
            os.environ["REAL_API_BASE_URL"] = base_url
            os.environ["REAL_API_KEY"] = "k"
            os.environ["REAL_API_SECRET"] = "s"
            rp = RealProvider(_cfg(), JsonlLogger.from_config(_cfg()))
            try:
                try:
                    await rp.lookup_orders("ABC123")
                    assert False, "expected ProviderParseError"
                except ProviderParseError as e:
                    assert "orders" in str(e).lower()
                    assert "/orders" in e.url
            finally:
                await rp.aclose()

    asyncio.run(run())


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

