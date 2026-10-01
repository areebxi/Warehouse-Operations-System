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
def _reports_dir(cfg: AppConfig) -> Path:
    paths = cfg.raw.get("paths") or {}
    raw = str(paths.get("reports_dir") or "Reports")
    p = Path(raw)
    if p.is_absolute():
        return p
    return _repo_root() / p
def _orders_csv_path(cfg: AppConfig, date_dir: str) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    return out_dir / "Order_Numbers" / date_dir / p
def _repo_root() -> Path:
    # scripts/app/flows/label_report/ -> repo root
    return Path(__file__).resolve().parents[4]
def _print_console_summary(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    print(text)
