from __future__ import annotations

import asyncio
import base64

from aiohttp import web

from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import RealProvider
from real_provider_helpers import aio_test_server, make_cfg as cfg, set_env


def test_lookup_orders_falls_back_to_shipped_status() -> None:
    routes = web.RouteTableDef()
    seen: list[str | None] = []

    @routes.get("/orders")
    async def orders(request: web.Request) -> web.Response:
        status = request.query.get("orderStatus")
        seen.append(status)
        if status != "shipped":
            return web.json_response({"orders": []})
        return web.json_response(
            {"orders": [{"orderId": 7, "orderNumber": "SO-9", "orderStatus": "shipped"}]}
        )

    async def run() -> None:
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
            try:
                out = await rp.lookup_orders("SO-9")
                assert len(out) == 1
                assert out[0].orderId == 7
                assert out[0].orderStatus == "shipped"
            finally:
                await rp.aclose()

    asyncio.run(run())
    assert seen == [None, "shipped"]


def test_fetch_label_uses_getlabel_when_primary_is_missing() -> None:
    routes = web.RouteTableDef()
    pdf_b64 = base64.b64encode(b"%PDF-1.4\n%SHIPPED\n%%EOF\n").decode("ascii")

    @routes.get("/shipments/{sid}/label")
    async def missing(request: web.Request) -> web.Response:
        raise web.HTTPNotFound()

    @routes.get("/shipments/getlabel")
    async def getlabel(request: web.Request) -> web.Response:
        assert request.query.get("shipmentId") == "15"
        return web.json_response({"labelData": pdf_b64, "trackingNumber": "TRK-OLD"})

    async def run() -> None:
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
            try:
                label = await rp.fetch_label(15)
                assert label is not None
                assert label.trackingNumber == "TRK-OLD"
                assert base64.b64decode(label.labelData.encode("ascii")).startswith(b"%PDF")
            finally:
                await rp.aclose()

    asyncio.run(run())
