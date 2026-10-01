from __future__ import annotations

import sys
from pathlib import Path

from PyPDF2 import PdfReader

from app.config.load import AppConfig
from app.flows.print_labels.combined_sanity import _sanity_check_combined_pdf
from app.flows.print_labels.failures import FailureRow, append_human_error_log, write_failures_csv
from app.flows.print_labels.paths import _combined_pdf_name_for_run, _repo_root
from app.flows.print_labels.process_group import _write_summary_bucket_pdf
from app.flows.print_labels.summary_buckets import (
    ProcessGroupResult,
    bucket_process_groups_for_shared_summaries,
)
from app.logging.jsonl import JsonlLogger
from app.logging.orders_audit import OrderAuditLogger
from app.pdf.merge_combined import merge_combined_by_process
from app.pdf.report_pages import make_combined_missed_orders_page_pdf


def finalize_print_run(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    audit: OrderAuditLogger,
    orders_csv: Path,
    combined_name_override: str | None,
    process_results_by_key: dict[str, ProcessGroupResult],
    all_failures: list[FailureRow],
    input_group_keys: set[str],
    batch_number: str,
    process_pdfs_dir: Path,
    combined_pdfs_dir: Path,
    failures_dir_override: Path | None,
    date_dir: str,
    input_key: str,
    command_name: str,
    total_orders: int,
) -> int:
    log.info(
        "print_process_group_results_collected",
        extra={
            "expected_process_count": int(len(input_group_keys)),
            "actual_process_count": int(len(process_results_by_key)),
            "actual_process_keys": sorted(list(process_results_by_key.keys())),
        },
    )

    still_missing = sorted(list(input_group_keys - set(process_results_by_key.keys())))
    if still_missing:
        log.error(
            "print_missing_process_results",
            extra={
                "missing_process_keys": still_missing,
                "expected_process_keys": sorted(list(input_group_keys)),
                "actual_process_keys": sorted(list(process_results_by_key.keys())),
            },
        )
        log.info("run_end", extra={"command": command_name, "input_key": input_key, "exit_code": 2})
        return 2

    # Share summary only for exactly-1-label consecutive processes within the same DTF file.
    # Each new DTF/source file always starts a fresh summary page.
    ordered_results = list(process_results_by_key.values())
    buckets = bucket_process_groups_for_shared_summaries(ordered_results)
    process_pdfs_dir.mkdir(parents=True, exist_ok=True)
    bucket_pdfs: list[Path] = []
    for bucket in buckets:
        pdf_path = _write_summary_bucket_pdf(
            cfg=cfg,
            log=log,
            batch_number=batch_number,
            bucket=bucket,
            process_pdfs_dir=process_pdfs_dir,
        )
        bucket_pdfs.append(pdf_path)

    summary_process_numbers: list[str] = [str(b.summary_process_number).strip() for b in buckets]
    log.info(
        "print_summary_buckets_built",
        extra={
            "input_process_count": int(len(input_group_keys)),
            "summary_bucket_count": int(len(buckets)),
            "shared_summaries_enabled": True,
            "share_rule": "exactly_1_label_consecutive_within_source_file",
            "buckets": [
                {
                    "summary_process_number": b.summary_process_number,
                    "member_process_numbers": list(b.process_numbers),
                    "order_counts": [int(m.order_count) for m in b.members],
                    "label_count": int(b.label_count),
                    "source_file": b.members[0].source_file if b.members else "",
                    "source_index": int(b.members[0].source_index) if b.members else 0,
                }
                for b in buckets
            ],
        },
    )

    # Write failures artifacts (if any).
    if all_failures:
        combined_name = _combined_pdf_name_for_run(
            orders_csv=orders_csv, combined_name_override=combined_name_override
        )
        failures_key = combined_name if combined_name != "combined" else batch_number
        _wh_root = _repo_root().parent
        if str(_wh_root) not in sys.path:
            sys.path.insert(0, str(_wh_root))
        from shared import paths as wh

        failures_dir = failures_dir_override or (wh.shipping_errors_dir() / date_dir / failures_key)
        failures_dir.mkdir(parents=True, exist_ok=True)
        failures_csv = failures_dir / "failures.csv"
        error_log = failures_dir / "error_log.txt"
        write_failures_csv(failures_csv, all_failures)
        append_human_error_log(error_log, all_failures)

    combined_pdfs_dir.mkdir(parents=True, exist_ok=True)
    combined_name = _combined_pdf_name_for_run(
        orders_csv=orders_csv, combined_name_override=combined_name_override
    )
    combined_pdf = combined_pdfs_dir / f"{combined_name}.pdf"
    # Combined: one summary per bucket (source-file order), then that bucket's labels.
    per_process_pdfs_sorted = bucket_pdfs
    log.info(
        "merge_combined_start",
        extra={
            "combined_pdf": str(combined_pdf),
            "process_pdf_count": int(len(per_process_pdfs_sorted)),
            "process_pdfs": [str(p) for p in per_process_pdfs_sorted],
            "missed_orders_page_appended": bool(all_failures),
        },
    )
    combined_missed = None
    if all_failures:
        combined_missed = make_combined_missed_orders_page_pdf(
            missed=[(f.process_number, f.order_number, f.reason) for f in all_failures]
        )
    merge_combined_by_process(
        out_path=combined_pdf,
        per_process_pdfs=per_process_pdfs_sorted,
        missed_pdf_bytes=combined_missed,
    )
    try:
        page_count = int(len(PdfReader(str(combined_pdf)).pages))
    except Exception:
        page_count = -1
    log.info("merge_combined_done", extra={"combined_pdf": str(combined_pdf), "page_count": int(page_count)})

    if not _sanity_check_combined_pdf(
        combined_pdf=combined_pdf, expected_process_numbers=summary_process_numbers, log=log
    ):
        log.info("run_end", extra={"command": command_name, "input_key": input_key, "exit_code": 2})
        return 2

    log.info(
        "print_done",
        extra={
            "process_count": int(len(process_results_by_key)),
            "combined_pdf": str(combined_pdf),
            "failure_count": len(all_failures),
        },
    )
    audit.summary(
        unique_orders=int(total_orders),
        process_count=int(len(process_results_by_key)),
        failure_count=int(len(all_failures)),
        combined_pdf=str(combined_pdf),
    )
    log.info("run_end", extra={"command": command_name, "input_key": input_key, "exit_code": 0})
    return 0
