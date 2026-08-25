from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from unittest.mock import patch

from scripts.app.config.defaults import default_config_dict
from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.process_order import process_one_order
from scripts.app.flows.print_labels.read_group import read_and_group_orders
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.logging.orders_audit import OrderAuditLogger
from scripts.app.models.label import Label
from scripts.app.models.order import Order


def _order_audit_rows(log_path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("msg") == "order_audit":
            rows.append(row["extra"])
    return rows


def _order_audit_outcomes(log_path: Path) -> list[str]:
    return [row["outcome"] for row in _order_audit_rows(log_path)]


def test_order_audit_writes_per_order_lines_to_existing_log(tmp_path: Path) -> None:
    log_path = tmp_path / "run" / "shipping.log"
    log = JsonlLogger(
        logs_dir=tmp_path,
        level="INFO",
        redact_keys=[],
        logger_name="test.audit",
        log_path=log_path,
        rotate=False,
        also_console=False,
    )
    audit = OrderAuditLogger.for_log(log=log, command="print", run_key="test-key")
    audit.record(
        outcome="print_success",
        order_number="A-1",
        process_number="50",
        customer_name="Alice",
        carrier_code="royal_mail",
        service_code="rm_tracked_48",
        package_code="large_letter",
    )

    text = log_path.read_text(encoding="utf-8")
    assert "order_audit" in text
    assert "A-1" in text
    assert "rm_tracked_48" in text
    assert "large_letter" in text
    assert not (tmp_path / "run" / "orders_audit.jsonl").exists()


def test_read_group_logs_deduped_rows_to_existing_log(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "Process Number,Order Number,Customer Name\n"
        "50,O-1,Alice\n"
        "50,O-1,Alice\n"
        "50,O-2,Bob\n",
        encoding="utf-8",
    )
    log_path = tmp_path / "shipping.log"
    log = JsonlLogger(
        logs_dir=tmp_path,
        level="INFO",
        redact_keys=[],
        logger_name="test.read_group",
        log_path=log_path,
        rotate=False,
        also_console=False,
    )
    audit = OrderAuditLogger.for_log(log=log, command="print", run_key="job")
    groups = read_and_group_orders(csv_path, audit=audit)

    assert len(groups) == 1
    assert groups[0].order_numbers == ["O-1", "O-2"]

    outcomes = _order_audit_outcomes(log_path)
    assert outcomes.count("print_queued") == 2
    assert outcomes.count("print_deduped") == 1


class _FakeProvider:
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
        pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
        return Label(labelData=base64.b64encode(pdf_bytes).decode(), trackingNumber="TRK123")


def test_process_order_logs_each_step_to_existing_log(tmp_path: Path) -> None:
    log_path = tmp_path / "combined.log"
    log = JsonlLogger(
        logs_dir=tmp_path,
        level="INFO",
        redact_keys=[],
        logger_name="test.process_order",
        log_path=log_path,
        rotate=False,
        also_console=False,
    )
    audit = OrderAuditLogger.for_log(log=log, command="print", run_key="job-1")
    raw = default_config_dict()
    raw["concurrency"] = {**raw["concurrency"], "max_retries": 0}
    cfg = AppConfig(raw=raw, provider_name="real")

    async def run() -> None:
        with patch("scripts.app.pdf.label_decode.write_label_pdf"):
            await process_one_order(
                cfg=cfg,
                log=log,
                provider=_FakeProvider(),
                process_number="50",
                order_number="O-100",
                customer_name_from_input="Alice",
                labels_dir=tmp_path / "labels",
                audit=audit,
            )

    asyncio.run(run())

    outcomes = _order_audit_outcomes(log_path)
    assert outcomes[0] == "print_start"
    assert "print_lookup" in outcomes
    assert "print_order_selected" in outcomes
    assert "print_shipments_loaded" in outcomes
    assert "print_service_resolved" in outcomes
    assert "print_label_creating" in outcomes
    assert outcomes[-1] == "print_success"

    success = [r for r in _order_audit_rows(log_path) if r["outcome"] == "print_success"][0]
    assert success["order_number"] == "O-100"
    assert success["process_number"] == "50"
    assert success["service_code"] == "rm_tracked_48"
    assert success["package_code"] == "large_letter"
    assert success["tracking_number"] == "TRK123"

