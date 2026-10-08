from __future__ import annotations

import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from scripts.app.config.load import AppConfig
from scripts.app.flows.label_report.app_prints import AppFailedRecord, AppPrintRecord, collect_app_print_records
from scripts.app.flows.label_report.shipstation_shipments import ShipStationShipmentRow, list_shipments_created_on_date
from scripts.app.flows.print_labels.read_group import read_and_group_orders
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import RealProvider
from scripts.app.providers.select_provider import get_provider
from scripts.app.util.time import local_compact_timestamp, local_date_ymd


def _repo_root() -> Path:
    # scripts/app/flows/label_report/ -> repo root
    return Path(__file__).resolve().parents[4]


def _reports_dir(cfg: AppConfig) -> Path:
    paths = cfg.raw.get("paths") or {}
    raw = str(paths.get("reports_dir") or "Reports")
    p = Path(raw)
    if p.is_absolute():
        return p
    return _repo_root() / p


REPORT_HEADER = [
    "Order Number",
    "Process Number",
    "Customer Name",
    "Status",
    "Label Origin",
    "In Today's DTF Batch",
    "App Command",
    "ShipStation Only",
    "ShipStation Shipment ID",
    "Tracking Number",
    "Carrier",
    "Service",
    "Package",
    "App Label Source",
    "App Failure Reason",
    "Shipment Create Date",
]


@dataclass(frozen=True)
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


def _orders_csv_path(cfg: AppConfig, date_dir: str) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    return out_dir / "Order_Numbers" / date_dir / p


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


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _app_command_for_order(
    *,
    app_ok: AppPrintRecord | None,
    app_bad: AppFailedRecord | None,
) -> str:
    if app_ok is not None and app_ok.app_command:
        return app_ok.app_command
    if app_bad is not None and app_bad.app_command:
        return app_bad.app_command
    return ""


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


def _build_report_rows(
    *,
    batch_orders: dict[str, tuple[str, str]],
    app_success: dict[str, AppPrintRecord],
    app_failed: dict[str, AppFailedRecord],
    ss_by_order: dict[str, ShipStationShipmentRow],
) -> list[ReportRow]:
    all_orders = set(batch_orders.keys()) | set(app_success.keys()) | set(app_failed.keys()) | set(ss_by_order.keys())
    rows: list[ReportRow] = []

    for on in sorted(all_orders):
        proc, cust = batch_orders.get(on, ("", ""))
        app_ok = app_success.get(on)
        app_bad = app_failed.get(on)
        ss = ss_by_order.get(on)
        in_batch = on in batch_orders
        app_command = _app_command_for_order(app_ok=app_ok, app_bad=app_bad)

        if app_ok is not None:
            proc = proc or app_ok.process_number
            cust = cust or app_ok.customer_name
            status = "printed_by_app"
            shipment_id = app_ok.shipment_id or (str(ss.shipment_id) if ss else "")
            tracking = app_ok.tracking_number or (ss.tracking_number if ss else "")
            carrier = app_ok.carrier_code or (ss.carrier_code if ss else "")
            service = app_ok.service_code or (ss.service_code if ss else "")
            package = app_ok.package_code or (ss.package_code if ss else "")
            label_source = app_ok.label_source
            fail_reason = ""
            create_date = ss.create_date if ss else ""
        elif ss is not None:
            status = "printed_outside_app"
            shipment_id = str(ss.shipment_id)
            tracking = ss.tracking_number
            carrier = ss.carrier_code
            service = ss.service_code
            package = ss.package_code
            label_source = ""
            fail_reason = ""
            create_date = ss.create_date
        elif app_bad is not None:
            proc = proc or app_bad.process_number
            cust = cust or app_bad.customer_name
            status = "app_failed"
            shipment_id = ""
            tracking = ""
            carrier = ""
            service = ""
            package = ""
            label_source = ""
            fail_reason = app_bad.reason
            create_date = ""
        else:
            status = "not_shipped"
            shipment_id = ""
            tracking = ""
            carrier = ""
            service = ""
            package = ""
            label_source = ""
            fail_reason = ""
            fail_reason = ""
            create_date = ""

        shipstation_only = ss is not None and app_ok is None and not in_batch
        label_origin = _label_origin(
            status=status,
            in_batch=in_batch,
            app_command=app_command,
            shipstation_only=shipstation_only,
        )

        rows.append(
            ReportRow(
                order_number=on,
                process_number=proc,
                customer_name=cust,
                status=status,
                label_origin=label_origin,
                in_todays_dtf_batch=in_batch,
                app_command=app_command,
                shipstation_only=shipstation_only,
                shipment_id=shipment_id,
                tracking_number=tracking,
                carrier_code=carrier,
                service_code=service,
                package_code=package,
                app_label_source=label_source,
                app_failure_reason=fail_reason,
                shipment_create_date=create_date,
            )
        )
    return rows


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


def _print_console_summary(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    print(text)


async def _run_async(*, cfg: AppConfig, log: JsonlLogger, date_dir: str, reports_dir: Path) -> int:
    logs_dir = Path(str(cfg.raw["paths"]["logs_dir"]))
    app_success, app_failed = collect_app_print_records(logs_dir=logs_dir, date_dir=date_dir)
    batch_orders = _batch_orders(cfg, date_dir)
    batch_csv = str(_orders_csv_path(cfg, date_dir))
    app_log_paths = [str(p) for p in (logs_dir / "Combined_PDFs Logs" / date_dir).glob("*.log")] if (logs_dir / "Combined_PDFs Logs" / date_dir).is_dir() else []
    manual_root = logs_dir / "Manual Print Logs" / date_dir
    if manual_root.is_dir():
        for job_dir in manual_root.iterdir():
            combined = job_dir / "combined.log"
            if combined.is_file():
                app_log_paths.append(str(combined))

    provider = get_provider(cfg, log)
    if not isinstance(provider, RealProvider):
        log.error("label_report_requires_real_provider", extra={"provider": cfg.provider_name})
        return 2

    ss_shipments: list[ShipStationShipmentRow] = []
    try:
        ss_shipments = await list_shipments_created_on_date(provider, date_ymd=date_dir)
    finally:
        aclose = getattr(provider, "aclose", None)
        if callable(aclose):
            await aclose()

    ss_by_order: dict[str, ShipStationShipmentRow] = {}
    for s in ss_shipments:
        on = str(s.order_number).strip()
        if not on:
            continue
        prev = ss_by_order.get(on)
        if prev is None or s.shipment_id > prev.shipment_id:
            ss_by_order[on] = s

    rows = _build_report_rows(
        batch_orders=batch_orders,
        app_success=app_success,
        app_failed=app_failed,
        ss_by_order=ss_by_order,
    )

    out_dir = reports_dir / date_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = local_compact_timestamp()
    csv_path = out_dir / f"label_source_report_{stamp}.csv"
    txt_path = out_dir / f"label_source_report_{stamp}.txt"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write_csv(csv_path, rows)
    _write_summary_txt(
        txt_path,
        date_dir=date_dir,
        generated_at=generated_at,
        rows=rows,
        app_log_files=app_log_paths,
        batch_csv=batch_csv if Path(batch_csv).exists() else "",
        ss_shipment_count=len(ss_shipments),
    )

    outside = sum(1 for r in rows if r.status == "printed_outside_app")
    log.info(
        "label_report_done",
        extra={
            "date_dir": date_dir,
            "orders_in_report": len(rows),
            "printed_by_app": sum(1 for r in rows if r.status == "printed_by_app"),
            "printed_outside_app": outside,
            "app_failed": sum(1 for r in rows if r.status == "app_failed"),
            "not_shipped": sum(1 for r in rows if r.status == "not_shipped"),
            "csv_path": str(csv_path),
            "txt_path": str(txt_path),
            "report_timestamp": stamp,
            "shipstation_shipments_today": len(ss_shipments),
            "app_dtf_print": sum(1 for r in rows if r.label_origin == "app_dtf_print"),
            "app_manual_print": sum(1 for r in rows if r.label_origin == "app_manual_print"),
            "dtf_batch_shipped_in_shipstation": sum(1 for r in rows if r.label_origin == "dtf_batch_shipped_in_shipstation"),
            "shipstation_only_no_dtf": sum(1 for r in rows if r.label_origin == "shipstation_only_no_dtf"),
        },
    )
    _print_console_summary(txt_path)
    return 0


def run_label_report(cfg: AppConfig, log: JsonlLogger, *, date_dir: str | None = None) -> int:
    date_dir = str(date_dir or local_date_ymd()).strip()
    reports_dir = _reports_dir(cfg)
    report_log = JsonlLogger.for_input_run(cfg, input_key="label_report", command="label-report")
    report_log.info("run_start", extra={"command": "label-report", "input_key": date_dir})
    report_log.info(
        "label_report_context",
        extra={"date_dir": date_dir, "reports_dir": str(reports_dir), "log_path": str(report_log.log_path)},
    )
    try:
        rc = asyncio.run(_run_async(cfg=cfg, log=report_log, date_dir=date_dir, reports_dir=reports_dir))
    except Exception as e:
        report_log.error("label_report_failed", exc=e)
        rc = 2
    report_log.info("run_end", extra={"command": "label-report", "input_key": date_dir, "exit_code": int(rc)})
    return rc
