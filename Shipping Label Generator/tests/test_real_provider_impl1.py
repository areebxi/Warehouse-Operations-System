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
