from __future__ import annotations

import json
from pathlib import Path

from scripts.app.flows.label_report.app_prints import AppFailedRecord, AppPrintRecord, collect_app_print_records
from scripts.app.flows.label_report.run import _build_report_rows
from scripts.app.flows.label_report.shipstation_shipments import ShipStationShipmentRow


def test_collect_app_print_records_captures_command(tmp_path: Path) -> None:
    date_dir = "2026-06-16"
    log_dir = tmp_path / "Manual Print Logs" / date_dir / "2000-2400"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "combined.log"
    row = {
        "msg": "order_audit",
        "extra": {
            "outcome": "print_success",
            "command": "manual-print",
            "order_number": "A-1",
            "process_number": "2000",
            "label_source": "created",
        },
    }
    log_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    success, _ = collect_app_print_records(logs_dir=tmp_path, date_dir=date_dir)
    assert success["A-1"].app_command == "manual-print"


def test_build_report_rows_label_origins() -> None:
    ss_outside = ShipStationShipmentRow(
        order_number="OUT-1",
        order_id=1,
        shipment_id=99,
        create_date="2026-06-16T13:19:00",
        tracking_number="TRK1",
        carrier_code="royal_mail",
        service_code="rm_tracked_48",
        package_code="large_letter",
        voided=False,
    )
    ss_in_batch = ShipStationShipmentRow(
        order_number="DTF-SS-1",
        order_id=2,
        shipment_id=100,
        create_date="2026-06-16T14:00:00",
        tracking_number="TRK2",
        carrier_code="royal_mail",
        service_code="rm_tracked_48",
        package_code="large_letter",
        voided=False,
    )
    app_dtf = AppPrintRecord(order_number="APP-1", process_number="50", label_source="created", app_command="print")
    app_manual = AppPrintRecord(
        order_number="MAN-1", process_number="2000", label_source="created", app_command="manual-print"
    )
    rows = _build_report_rows(
        batch_orders={"APP-1": ("50", "Alice"), "DTF-SS-1": ("50", "Bob"), "WAIT-1": ("51", "Carol")},
        app_success={"APP-1": app_dtf, "MAN-1": app_manual},
        app_failed={"FAIL-1": AppFailedRecord(order_number="FAIL-1", reason="timeout", app_command="print")},
        ss_by_order={"OUT-1": ss_outside, "DTF-SS-1": ss_in_batch, "APP-1": ss_in_batch},
    )
    by_order = {r.order_number: r for r in rows}

    assert by_order["APP-1"].label_origin == "app_dtf_print"
    assert by_order["APP-1"].in_todays_dtf_batch is True
    assert by_order["APP-1"].app_command == "print"
    assert by_order["APP-1"].shipstation_only is False

    assert by_order["MAN-1"].label_origin == "app_manual_print"
    assert by_order["MAN-1"].in_todays_dtf_batch is False
    assert by_order["MAN-1"].app_command == "manual-print"

    assert by_order["OUT-1"].label_origin == "shipstation_only_no_dtf"
    assert by_order["OUT-1"].shipstation_only is True
    assert by_order["OUT-1"].in_todays_dtf_batch is False

    assert by_order["DTF-SS-1"].label_origin == "dtf_batch_shipped_in_shipstation"
    assert by_order["DTF-SS-1"].in_todays_dtf_batch is True
    assert by_order["DTF-SS-1"].shipstation_only is False

    assert by_order["WAIT-1"].label_origin == "dtf_batch_not_shipped"
    assert by_order["FAIL-1"].label_origin == "app_dtf_print_failed"
