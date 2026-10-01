from __future__ import annotations

import asyncio
import base64
from typing import Any

from aiohttp import web

from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.models.order import Order
from scripts.app.providers.real.provider import RealProvider
from real_provider_helpers import make_cfg as cfg, set_env, aio_test_server


def test_fetch_label_returns_none_on_404() -> None:
    routes = web.RouteTableDef()

    @routes.get("/shipments/{sid}/label")
    async def label(request: web.Request) -> web.Response:
        raise web.HTTPNotFound()

    async def run() -> None:
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
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
        async with aio_test_server(routes) as base_url:
            set_env(base_url)
            rp = RealProvider(cfg(), JsonlLogger.from_config(cfg()))
            try:
                await rp.void_label(777)
                assert seen["json"] == {"shipmentId": 777}
            finally:
                await rp.aclose()

    asyncio.run(run())

