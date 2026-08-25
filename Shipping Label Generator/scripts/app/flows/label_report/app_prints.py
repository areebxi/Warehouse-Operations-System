from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPrintRecord:
    order_number: str
    process_number: str = ""
    customer_name: str = ""
    shipstation_order_id: str = ""
    shipment_id: str = ""
    tracking_number: str = ""
    carrier_code: str = ""
    service_code: str = ""
    package_code: str = ""
    label_source: str = ""
    app_command: str = ""
    log_path: str = ""


@dataclass(frozen=True)
class AppFailedRecord:
    order_number: str
    process_number: str = ""
    customer_name: str = ""
    reason: str = ""
    app_command: str = ""
    log_path: str = ""


def _norm_order_number(raw: str) -> str:
    return str(raw or "").strip().replace("\r", "").replace("\n", "").replace(" ", "")


def _iter_log_files(logs_dir: Path, date_dir: str) -> list[Path]:
    paths: list[Path] = []
    combined_dir = logs_dir / "Combined_PDFs Logs" / date_dir
    if combined_dir.is_dir():
        paths.extend(sorted(combined_dir.glob("*.log")))

    manual_root = logs_dir / "Manual Print Logs" / date_dir
    if manual_root.is_dir():
        for job_dir in sorted(manual_root.iterdir()):
            if job_dir.is_dir():
                combined = job_dir / "combined.log"
                if combined.is_file():
                    paths.append(combined)
    return paths


def _command_from_log_path(log_path: Path) -> str:
    text = log_path.as_posix().replace("\\", "/")
    if "Manual Print Logs" in text:
        return "manual-print"
    return "print"


def _resolve_app_command(*, extra: dict, log_path: Path) -> str:
    cmd = str(extra.get("command") or "").strip()
    if cmd:
        return cmd
    return _command_from_log_path(log_path)


def _parse_audit_line(*, line: str, log_path: Path) -> tuple[str, dict] | None:
    line = line.strip()
    if not line:
        return None
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        return None
    if row.get("msg") != "order_audit":
        return None
    extra = row.get("extra")
    if not isinstance(extra, dict):
        return None
    outcome = str(extra.get("outcome") or "").strip()
    if not outcome:
        return None
    return outcome, extra


def collect_app_print_records(*, logs_dir: Path, date_dir: str) -> tuple[dict[str, AppPrintRecord], dict[str, AppFailedRecord]]:
    """
    Scan today's print/manual-print logs for per-order outcomes from this app.
    """
    success: dict[str, AppPrintRecord] = {}
    failed: dict[str, AppFailedRecord] = {}

    for log_path in _iter_log_files(logs_dir, date_dir):
        text = log_path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            parsed = _parse_audit_line(line=line, log_path=log_path)
            if parsed is None:
                continue
            outcome, extra = parsed
            on = _norm_order_number(str(extra.get("order_number") or ""))
            if not on:
                continue

            cmd = _resolve_app_command(extra=extra, log_path=log_path)
            if outcome == "print_success":
                success[on] = AppPrintRecord(
                    order_number=on,
                    process_number=str(extra.get("process_number") or "").strip(),
                    customer_name=str(extra.get("customer_name") or "").strip(),
                    shipstation_order_id=str(extra.get("shipstation_order_id") or "").strip(),
                    shipment_id=str(extra.get("shipment_id") or "").strip(),
                    tracking_number=str(extra.get("tracking_number") or "").strip(),
                    carrier_code=str(extra.get("carrier_code") or "").strip(),
                    service_code=str(extra.get("service_code") or "").strip(),
                    package_code=str(extra.get("package_code") or "").strip(),
                    label_source=str(extra.get("label_source") or "").strip(),
                    app_command=cmd,
                    log_path=str(log_path),
                )
            elif outcome == "print_failed":
                failed[on] = AppFailedRecord(
                    order_number=on,
                    process_number=str(extra.get("process_number") or "").strip(),
                    customer_name=str(extra.get("customer_name") or "").strip(),
                    reason=str(extra.get("reason") or "").strip(),
                    app_command=cmd,
                    log_path=str(log_path),
                )

    return success, failed
