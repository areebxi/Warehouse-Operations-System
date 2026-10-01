from __future__ import annotations

import asyncio

from aiohttp import web

from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import ProviderHttpError, ProviderParseError, RealProvider
from real_provider_helpers import make_cfg as cfg, set_env, aio_test_server


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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
            try:
                out = await rp.list_shipments(99, include_voided=False, page_size=5)
                assert [s.shipmentId for s in out] == [12, 11]
            finally:
                await rp.aclose()

    asyncio.run(run())

def test_provider_http_error_exposes_retry_after() -> None:
    routes = web.RouteTableDef()

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        return web.Response(status=429, headers={"Retry-After": "2"}, text="Too Many Requests")

    async def run() -> None:
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
            try:
                a = await rp.list_shipments(99, include_voided=False, page_size=10)
                b = await rp.list_shipments(99, include_voided=False, page_size=10)
                assert len(a) == 1 and len(b) == 1
                assert a[0].shipmentId == b[0].shipmentId
                assert calls["n"] == 2
            finally:
                await rp.aclose()

    asyncio.run(run())

