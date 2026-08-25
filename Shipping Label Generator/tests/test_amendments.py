from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from unittest.mock import AsyncMock, patch

from scripts.app.config.defaults import default_config_dict
from scripts.app.config.load import AppConfig
from scripts.app.flows.amendments.shipstation_tags import (
    _order_tag_info_from_raw,
    selected_order_has_amendments,
)
from scripts.app.flows.amendments.tags import (
    AMENDMENTS_SKIP_REASON,
    AMENDMENTS_TAG_NAME,
    OrderTagInfo,
    amendments_skip_reason,
    has_amendments_tag,
    should_skip_label_for_amendments,
)
from scripts.app.flows.print_labels.process_order import process_one_order
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.models.label import Label
from scripts.app.models.order import Order


def test_has_amendments_tag_case_insensitive() -> None:
    assert has_amendments_tag(["Urgent", "Amendments"]) is True
    assert has_amendments_tag(["amendments"]) is True
    assert has_amendments_tag(["  AMENDMENTS  "]) is True
    assert has_amendments_tag(["Urgent", "Hold"]) is False
    assert has_amendments_tag([]) is False
    assert has_amendments_tag(None) is False


def test_should_skip_label_for_amendments() -> None:
    assert should_skip_label_for_amendments(["Amendments"]) is True
    assert should_skip_label_for_amendments(["Other"]) is False


def test_amendments_skip_reason_default() -> None:
    assert amendments_skip_reason() == AMENDMENTS_SKIP_REASON
    assert AMENDMENTS_TAG_NAME in amendments_skip_reason()


def test_order_tag_info_properties() -> None:
    info = OrderTagInfo(
        order_number="205-123",
        order_id=99,
        tag_ids=[1, 2],
        tag_names=["Hold", "Amendments"],
    )
    assert info.tag_count == 2
    assert info.has_amendments is True

    bare = OrderTagInfo(order_number="x", order_id=1, tag_ids=[7], tag_names=[])
    assert bare.tag_count == 1
    assert bare.has_amendments is False


def test_order_tag_info_from_raw_resolves_names() -> None:
    info = _order_tag_info_from_raw(
        order_number="O-1",
        raw_order={
            "orderId": 55,
            "orderNumber": "O-1",
            "customerName": "Sam",
            "orderStatus": "awaiting_shipment",
            "tagIds": [10, 20],
        },
        tag_id_to_name={10: "Hold", 20: "Amendments"},
    )
    assert info.order_id == 55
    assert info.tag_names == ["Hold", "Amendments"]
    assert info.has_amendments is True


def test_selected_order_has_amendments_skips_non_real_provider() -> None:
    class _P:
        pass

    blocked, info = asyncio.run(
        selected_order_has_amendments(_P(), order_id=1, order_number="O-1")
    )
    assert blocked is False
    assert info is None


class _FakePrintProvider:
    def __init__(self) -> None:
        self.create_calls = 0

    async def lookup_orders(self, order_number: str) -> list[Order]:
        return [
            Order(
                orderId=101,
                orderNumber=order_number,
                customerName="Alice",
                carrierCode="royal_mail",
                serviceCode="rm_tracked_48",
                packageCode="large_letter",
                requestedShippingService="NextDay UK Next",
            )
        ]

    async def list_shipments(self, order_id: int, *, include_voided: bool = False, page_size: int = 1):
        return []

    async def create_label(self, **kwargs) -> Label:
        self.create_calls += 1
        pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
        return Label(labelData=base64.b64encode(pdf_bytes).decode(), trackingNumber="TRK123")

    async def fetch_label(self, shipment_id: int) -> Label | None:
        return None

    async def void_label(self, shipment_id: int) -> None:
        return None


def test_process_order_skips_label_when_amendments_tag_present(tmp_path: Path) -> None:
    log = JsonlLogger(
        logs_dir=tmp_path,
        level="INFO",
        redact_keys=[],
        logger_name="test.amendments_print",
        log_path=tmp_path / "shipping.log",
        rotate=False,
        also_console=False,
    )
    raw = default_config_dict()
    raw["concurrency"] = {**raw["concurrency"], "max_retries": 0}
    cfg = AppConfig(raw=raw, provider_name="real")
    provider = _FakePrintProvider()
    tag_info = OrderTagInfo(
        order_number="O-AMD",
        order_id=101,
        tag_ids=[9],
        tag_names=["Amendments"],
        customer_name="Alice",
    )

    async def run():
        with patch(
            "scripts.app.flows.amendments.shipstation_tags.selected_order_has_amendments",
            new=AsyncMock(return_value=(True, tag_info)),
        ):
            return await process_one_order(
                cfg=cfg,
                log=log,
                provider=provider,
                process_number="100",
                order_number="O-AMD",
                customer_name_from_input="Alice",
                labels_dir=tmp_path / "labels",
            )

    result = asyncio.run(run())
    assert result.failure is not None
    assert result.failure.reason == AMENDMENTS_SKIP_REASON
    assert provider.create_calls == 0
    assert result.label_pdf_path.name.endswith("__ERROR.pdf")
    assert result.label_pdf_path.exists()
