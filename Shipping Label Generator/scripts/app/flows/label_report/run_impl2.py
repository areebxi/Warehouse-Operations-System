from __future__ import annotations
import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from app.config.load import AppConfig
from app.flows.label_report.app_prints import AppFailedRecord, AppPrintRecord, collect_app_print_records
from app.flows.label_report.shipstation_shipments import ShipStationShipmentRow, list_shipments_created_on_date
from app.flows.print_labels.read_group import read_and_group_orders
from app.logging.jsonl import JsonlLogger
from app.providers.real.provider import RealProvider
from app.providers.select_provider import get_provider
from app.util.time import local_compact_timestamp, local_date_ymd

def _write_summary_txt(
    path: Path,
    *,
    date_dir: str,
    generated_at: str,
    rows: list[ReportRow],
    app_log_files: list[str],
    batch_csv: str,
    ss_shipment_count: int,
) -> None:
    counts = {
        "printed_by_app": 0,
        "printed_outside_app": 0,
        "app_failed": 0,
        "not_shipped": 0,
    }
    for r in rows:
        if r.status in counts:
            counts[r.status] += 1

    origin_counts: dict[str, int] = {}
    for r in rows:
        origin_counts[r.label_origin] = origin_counts.get(r.label_origin, 0) + 1

    lines = [
        f"Label source report — {date_dir}",
        f"Generated at: {generated_at}",
        "",
        f"Today's batch CSV: {batch_csv or '(not found)'}",
        f"App log files scanned: {len(app_log_files)}",
        f"ShipStation shipments created today (non-voided): {ss_shipment_count}",
        "",
        f"Orders in report:              {len(rows)}",
        f"Printed by our app:            {counts['printed_by_app']}",
        f"  - App DTF print:             {origin_counts.get('app_dtf_print', 0)}",
        f"  - App manual print:          {origin_counts.get('app_manual_print', 0)}",
        f"Printed outside our app:       {counts['printed_outside_app']}",
        f"  - DTF batch, SS printed:   {origin_counts.get('dtf_batch_shipped_in_shipstation', 0)}",
        f"  - ShipStation only (no DTF): {origin_counts.get('shipstation_only_no_dtf', 0)}",
        f"App tried but failed:          {counts['app_failed']}",
        f"Not shipped yet (in DTF):      {origin_counts.get('dtf_batch_not_shipped', 0)}",
        "",
        "Label origins:",
        "  app_dtf_print                  = printed by app from DTF Convert + Print",
        "  app_manual_print               = printed by app Manual Print",
        "  dtf_batch_shipped_in_shipstation = in today's DTF CSV but label created in ShipStation",
        "  shipstation_only_no_dtf        = shipped in ShipStation, not in DTF batch, not by app",
        "",
    ]
    outside = [r for r in rows if r.status == "printed_outside_app"]
    ss_only = [r for r in rows if r.label_origin == "shipstation_only_no_dtf"]
    dtf_ss = [r for r in rows if r.label_origin == "dtf_batch_shipped_in_shipstation"]
    if ss_only:
        lines.append("ShipStation only (no DTF file for this date):")
        for r in ss_only:
            bits = [r.order_number]
            if r.tracking_number:
                bits.append(f"tracking={r.tracking_number}")
            lines.append("  - " + " | ".join(bits))
        lines.append("")
    if dtf_ss:
        lines.append("In DTF batch but printed in ShipStation (not by app):")
        for r in dtf_ss:
            bits = [r.order_number]
            if r.process_number:
                bits.append(f"process={r.process_number}")
            if r.tracking_number:
                bits.append(f"tracking={r.tracking_number}")
            lines.append("  - " + " | ".join(bits))
        lines.append("")
    if outside and not ss_only and not dtf_ss:
        lines.append("Orders printed outside our app:")
        for r in outside:
            bits = [r.order_number]
            if r.customer_name:
                bits.append(r.customer_name)
            if r.tracking_number:
                bits.append(f"tracking={r.tracking_number}")
            if r.service_code:
                bits.append(f"service={r.service_code}")
            lines.append("  - " + " | ".join(bits))
    elif not outside:
        lines.append("No orders found that were shipped in ShipStation today without an app print_success log.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
def _write_csv(path: Path, rows: list[ReportRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(REPORT_HEADER)
        for r in rows:
            w.writerow(
                [
                    r.order_number,
                    r.process_number,
                    r.customer_name,
                    r.status,
                    r.label_origin,
                    _yes_no(r.in_todays_dtf_batch),
                    r.app_command,
                    _yes_no(r.shipstation_only),
                    r.shipment_id,
                    r.tracking_number,
                    r.carrier_code,
                    r.service_code,
                    r.package_code,
                    r.app_label_source,
                    r.app_failure_reason,
                    r.shipment_create_date,
                ]
            )
def _label_origin(
    *,
    status: str,
    in_batch: bool,
    app_command: str,
    shipstation_only: bool,
) -> str:
    if status == "printed_by_app":
        if app_command == "manual-print":
            return "app_manual_print"
        return "app_dtf_print"
    if status == "printed_outside_app":
        if in_batch:
            return "dtf_batch_shipped_in_shipstation"
        if shipstation_only:
            return "shipstation_only_no_dtf"
        return "printed_outside_app"
    if status == "app_failed":
        if app_command == "manual-print":
            return "app_manual_print_failed"
        return "app_dtf_print_failed"
    if status == "not_shipped" and in_batch:
        return "dtf_batch_not_shipped"
    return status
def _batch_orders(cfg: AppConfig, date_dir: str) -> dict[str, tuple[str, str]]:
    """
    order_number -> (process_number, customer_name) from today's converted CSV, if present.
    """
    csv_path = _orders_csv_path(cfg, date_dir)
    if not csv_path.exists():
        return {}
    try:
        groups = read_and_group_orders(csv_path)
    except Exception:
        return {}
    out: dict[str, tuple[str, str]] = {}
    for g in groups:
        for o in g.orders:
            on = str(o.order_number).strip()
            if on:
                out[on] = (str(g.process_number).strip(), str(o.customer_name).strip())
    return out
class ReportRow:
    order_number: str
    process_number: str
    customer_name: str
    status: str
    label_origin: str
    in_todays_dtf_batch: bool
    app_command: str
    shipstation_only: bool
    shipment_id: str
    tracking_number: str
    carrier_code: str
    service_code: str
    package_code: str
    app_label_source: str
    app_failure_reason: str
    shipment_create_date: str
