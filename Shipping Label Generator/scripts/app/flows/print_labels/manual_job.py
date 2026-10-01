from __future__ import annotations

import shutil
from pathlib import Path

from app.config.load import AppConfig
from app.flows.print_labels.paths import _path_from_repo
from app.flows.print_labels.read_group import GroupedOrders
from app.logging.jsonl import JsonlLogger
from app.util.process_numbers import process_number_sort_key
from app.util.time import utc_compact_timestamp

def _manual_orders_csv_path(cfg: AppConfig) -> Path:
    manual_cfg = cfg.raw.get("manual_print") or {}
    input_csv = str(manual_cfg.get("input_csv", "Manual Print Input/Order Numbers.csv"))
    return _path_from_repo(input_csv)

def _manual_output_root(cfg: AppConfig) -> Path:
    return Path(str(cfg.raw["paths"]["output_dir"])) / "Manual Outputs"

def _manual_logs_job_dir(*, cfg: AppConfig, date_dir: str, job_id: str) -> Path:
    return Path(str(cfg.raw["paths"]["logs_dir"])) / "Manual Print Logs" / date_dir / job_id

def _manual_job_id_from_groups(groups: list[GroupedOrders]) -> str:
    """
    Build a stable manual job id from process numbers in the CSV, e.g. "2000-2400-2450".
    """
    process_numbers = sorted(
        {str(g.process_number).strip() for g in groups if str(g.process_number).strip()},
        key=process_number_sort_key,
    )
    if not process_numbers:
        raise ValueError("no process numbers in manual input")
    return "-".join(process_numbers)

def _manual_job_paths(*, cfg: AppConfig, date_dir: str, job_id: str, process_numbers: set[str] | None = None) -> dict[str, Path]:
    out_dir = _manual_output_root(cfg)
    paths: dict[str, Path] = {
        "combined_pdf": out_dir / "Combined_PDFs" / date_dir / f"{job_id}.pdf",
        "process_pdfs_dir": out_dir / "Process_PDFs" / date_dir / "Manual" / job_id,
        "logs_dir": _manual_logs_job_dir(cfg=cfg, date_dir=date_dir, job_id=job_id),
    }
    if process_numbers:
        labels_root = out_dir / "Labels" / date_dir
        for process_number in process_numbers:
            clean = str(process_number).strip()
            if clean:
                paths[f"labels_process_{clean}"] = labels_root / f"process_{clean}"
    return paths

def _manual_job_has_outputs(*, cfg: AppConfig, date_dir: str, job_id: str) -> bool:
    return any(p.exists() for p in _manual_job_paths(cfg=cfg, date_dir=date_dir, job_id=job_id).values())

def _archive_existing_manual_job(
    *,
    cfg: AppConfig,
    date_dir: str,
    job_id: str,
    process_numbers: set[str],
    log: JsonlLogger,
) -> Path:
    stamp = utc_compact_timestamp()
    archive_root = _manual_output_root(cfg) / "Archived_Replaced_Runs" / date_dir / f"{job_id}_{stamp}"
    archive_root.mkdir(parents=True, exist_ok=True)

    moved: list[dict[str, str]] = []
    for label, path in _manual_job_paths(cfg=cfg, date_dir=date_dir, job_id=job_id, process_numbers=process_numbers).items():
        if not path.exists():
            continue
        dest = archive_root / label
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
        moved.append({"source": str(path), "archive": str(dest)})

    log.info(
        "manual_print_existing_job_archived",
        extra={"job_id": job_id, "archive_root": str(archive_root), "moved": moved},
    )
    return archive_root

def _write_manual_input_log(
    *,
    cfg: AppConfig,
    date_dir: str,
    job_id: str,
    manual_csv: Path,
    groups,
    replace: bool,
) -> None:
    log_path = _manual_logs_job_dir(cfg=cfg, date_dir=date_dir, job_id=job_id) / "input.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    total_orders = sum(len(g.order_numbers) for g in groups)
    lines = [
        f"Manual Print Job: {job_id}",
        f"Date: {date_dir}",
        f"Mode: {'replace existing job' if replace else 'new manual job'}",
        f"Input CSV: {manual_csv}",
        f"Process Count: {len(groups)}",
        f"Total Orders: {total_orders}",
        "",
        "Processes:",
    ]
    for g in groups:
        lines.append(f"- Process {g.process_number}: {len(g.order_numbers)} orders")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

