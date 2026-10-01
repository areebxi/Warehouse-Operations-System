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
def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"
