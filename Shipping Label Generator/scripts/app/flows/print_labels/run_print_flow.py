from __future__ import annotations

import asyncio
from pathlib import Path

from app.config.load import AppConfig
from app.flows.print_labels.paths import _combined_pdf_name_for_run, _orders_csv_path
from app.flows.print_labels.read_group import read_and_group_orders
from app.flows.print_labels.run_print_execute import execute_process_groups
from app.flows.print_labels.run_print_finalize import finalize_print_run
from app.logging.jsonl import JsonlLogger
from app.logging.orders_audit import OrderAuditLogger
from app.util.process_numbers import process_number_sort_key
from app.util.time import local_date_ymd, utc_compact_timestamp


def run_print(
    cfg: AppConfig,
    log: JsonlLogger,
    *,
    orders_csv_override: Path | None = None,
    combined_name_override: str | None = None,
    labels_base_dir_override: Path | None = None,
    combined_pdfs_dir_override: Path | None = None,
    process_pdfs_base_dir_override: Path | None = None,
    failures_dir_override: Path | None = None,
    run_log_override: JsonlLogger | None = None,
    command_name: str = "print",
    allow_existing_outputs: bool = True,
) -> int:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    date_dir = local_date_ymd()
    labels_base_dir = labels_base_dir_override or (out_dir / "Labels" / date_dir)
    combined_pdfs_dir = combined_pdfs_dir_override or (out_dir / "Combined_PDFs" / date_dir)

    # Batch# should be YYYYMMDDHHMMSS (no underscore).
    batch_number = utc_compact_timestamp().replace("_", "")

    orders_csv = orders_csv_override or _orders_csv_path(cfg)
    if not orders_csv.exists():
        log.error("print_missing_orders_csv", extra={"orders_csv": str(orders_csv)})
        return 2

    # Per-combined-PDF log folder based on DTF id / manifest (e.g. "8300-8310-8320").
    combined_name = _combined_pdf_name_for_run(
        orders_csv=orders_csv, combined_name_override=combined_name_override
    )
    input_key = combined_name if combined_name != "combined" else batch_number
    log = run_log_override or JsonlLogger.for_combined_pdf_run(
        cfg, combined_pdf_stem=input_key, date_dir=date_dir
    )

    # Process PDFs are scoped per input key to avoid mixing runs on the same day:
    #   output/Process_PDFs/<date>/<input_key>/process_<n>.pdf
    # Keep the old base dir for backwards-compatible recovery.
    process_pdfs_base_dir = process_pdfs_base_dir_override or (out_dir / "Process_PDFs" / date_dir)
    process_pdfs_dir = process_pdfs_base_dir / str(input_key)
    combined_pdf = combined_pdfs_dir / f"{combined_name}.pdf"

    if not allow_existing_outputs:
        existing = [str(p) for p in (combined_pdf, process_pdfs_dir) if p.exists()]
        if existing:
            log.error(
                "print_refusing_to_overwrite_outputs",
                extra={"input_key": input_key, "existing_paths": existing},
            )
            log.info(
                "run_end",
                extra={"command": command_name, "input_key": input_key, "exit_code": 2},
            )
            return 2

    log.info("run_start", extra={"command": command_name, "input_key": input_key})
    log.info(
        "print_run_context",
        extra={
            "orders_csv": str(orders_csv),
            "input_key": input_key,
            "batch_number": batch_number,
            "date_dir": str(date_dir),
            "labels_base_dir": str(labels_base_dir),
            "process_pdfs_dir": str(process_pdfs_dir),
            "process_pdfs_base_dir": str(process_pdfs_base_dir),
            "combined_pdfs_dir": str(combined_pdfs_dir),
            "combined_log_path": str(log.log_path),
        },
    )

    audit = OrderAuditLogger.for_log(log=log, command=command_name, run_key=input_key)

    groups = read_and_group_orders(orders_csv, audit=audit)
    if not groups:
        log.error("print_no_orders", extra={"orders_csv": str(orders_csv)})
        log.info("run_end", extra={"command": command_name, "input_key": input_key, "exit_code": 2})
        return 2

    total_orders = int(sum(len(g.order_numbers) for g in groups))
    input_group_keys: set[str] = {
        f"{int(g.source_index)}::{str(g.process_number).strip()}" for g in groups
    }
    log.info(
        "print_groups_loaded",
        extra={
            "group_count": int(len(groups)),
            "expected_process_numbers": sorted(
                [str(g.process_number).strip() for g in groups],
                key=process_number_sort_key,
            ),
            "orders_per_process": {
                f"{int(g.source_index)}:{g.process_number}": int(len(g.order_numbers))
                for g in groups
            },
            "source_files": sorted({str(g.source_file) for g in groups if g.source_file}),
            "total_orders": total_orders,
        },
    )

    process_results_by_key, all_failures = asyncio.run(
        execute_process_groups(
            cfg=cfg,
            log=log,
            groups=groups,
            labels_base_dir=labels_base_dir,
            audit=audit,
        )
    )
    return finalize_print_run(
        cfg=cfg,
        log=log,
        audit=audit,
        orders_csv=orders_csv,
        combined_name_override=combined_name_override,
        process_results_by_key=process_results_by_key,
        all_failures=all_failures,
        input_group_keys=input_group_keys,
        batch_number=batch_number,
        process_pdfs_dir=process_pdfs_dir,
        combined_pdfs_dir=combined_pdfs_dir,
        failures_dir_override=failures_dir_override,
        date_dir=date_dir,
        input_key=input_key,
        command_name=command_name,
        total_orders=total_orders,
    )
