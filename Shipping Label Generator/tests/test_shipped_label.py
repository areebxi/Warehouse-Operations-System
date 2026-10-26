from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from scripts.app.config.defaults import default_config_dict
from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.process_order import process_one_order
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.flows.print_labels.sample_pdf import sample_label_pdf_bytes
from scripts.app.models.label import Label
from scripts.app.models.order import Order
from scripts.app.models.shipment import Shipment


class _ShippedProvider:
    def __init__(self) -> None:
        self.created = 0

    async def lookup_orders(self, order_number: str) -> list[Order]:
        return [
            Order(
                orderId=44,
                orderNumber=order_number,
                orderStatus="shipped",
                customerName="Ada",
                carrierCode="royal_mail",
                serviceCode="rm_tracked_48",
                packageCode="large_letter",
            )
        ]

    async def list_shipments(self, order_id: int, *, include_voided: bool = False, page_size: int = 1):
        return [
            Shipment(
                shipmentId=9,
                orderId=order_id,
                voided=False,
                carrierCode="royal_mail",
                serviceCode="rm_tracked_48",
                packageCode="large_letter",
            )
        ]

    async def fetch_label(self, shipment_id: int) -> Label:
        pdf_bytes = sample_label_pdf_bytes(process_number="B100-S1-1", order_number="SO-1", customer_name="Ada")
        return Label(labelData=base64.b64encode(pdf_bytes).decode(), trackingNumber="EXISTING")

    async def create_label(self, **kwargs) -> Label:
        self.created += 1
        raise AssertionError("must not buy a new label")


def test_shipped_order_reuses_label_by_order_number(tmp_path: Path) -> None:
    log = JsonlLogger(
        logs_dir=tmp_path,
        level="INFO",
        redact_keys=[],
        logger_name="test.shipped",
        log_path=tmp_path / "shipping.log",
        rotate=False,
        also_console=False,
    )
    raw = default_config_dict()
    raw["concurrency"] = {**raw["concurrency"], "max_retries": 0}
    cfg = AppConfig(raw=raw, provider_name="real")
    provider = _ShippedProvider()

    async def run() -> None:
        result = await process_one_order(
            cfg=cfg,
            log=log,
            provider=provider,
            process_number="B100-S1-1",
            order_number="SO-1",
            customer_name_from_input="Ada",
            labels_dir=tmp_path / "labels",
            audit=None,
        )
        assert result.failure is None
        assert result.label_pdf_path.is_file()

    asyncio.run(run())
    assert provider.created == 0


class _NoRemoteLabel(_ShippedProvider):
    async def fetch_label(self, shipment_id: int) -> Label | None:
        return None


def test_shipped_order_reuses_saved_pdf_when_api_has_no_label(tmp_path: Path) -> None:
    saved = sample_label_pdf_bytes(process_number="70", order_number="A70", customer_name="Ada")
    out = tmp_path / "output" / "Labels" / "2026-10-20" / "process_70"
    out.mkdir(parents=True)
    (out / "A70.pdf").write_bytes(saved)
    log = JsonlLogger(
        logs_dir=tmp_path,
        level="INFO",
        redact_keys=[],
        logger_name="test.local",
        log_path=tmp_path / "shipping.log",
        rotate=False,
        also_console=False,
    )
    raw = default_config_dict()
    raw["paths"] = {**raw["paths"], "output_dir": str(tmp_path / "output")}
    raw["concurrency"] = {**raw["concurrency"], "max_retries": 0}
    cfg = AppConfig(raw=raw, provider_name="real")
    provider = _NoRemoteLabel()

    async def run() -> None:
        result = await process_one_order(
            cfg=cfg,
            log=log,
            provider=provider,
            process_number="70",
            order_number="A70",
            customer_name_from_input="Ada",
            labels_dir=tmp_path / "labels",
            audit=None,
        )
        assert result.failure is None
        assert result.label_pdf_path.read_bytes() == saved

    asyncio.run(run())
    assert provider.created == 0
