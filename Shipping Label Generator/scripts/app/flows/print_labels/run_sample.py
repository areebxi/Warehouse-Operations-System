from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader

from scripts.app.config.label_page_threshold import read_label_page_threshold
from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.failures import FailureRow, append_human_error_log, write_failures_csv
from scripts.app.flows.print_labels.read_group import read_and_group_orders
from scripts.app.flows.print_labels.run import (
    _combined_pdf_name_for_run,
    _orders_csv_path,
    _process_number_sort_key,
    _sanity_check_combined_pdf,
    _write_summary_bucket_pdf,
)
from scripts.app.flows.print_labels.sample_order import process_sample_order
from scripts.app.flows.print_labels.summary_buckets import (
    ProcessGroupResult,
    bucket_process_groups_for_shared_summaries,
)
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.logging.orders_audit import OrderAuditLogger
from scripts.app.pdf.merge_combined import merge_combined_by_process
from scripts.app.pdf.report_pages import make_combined_missed_orders_page_pdf
from scripts.app.util.time import local_date_ymd, utc_compact_timestamp


def run_sample_print(cfg: AppConfig, log: JsonlLogger) -> int:
    """Same PDF assembly as print, with local SAMPLE pages. No ShipStation calls."""
    print("SAMPLE PRINT — no ShipStation calls. These are not shipping labels.")
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    date_dir = local_date_ymd()
    sample_root = out_dir / "Sample" / date_dir
    orders_csv = _orders_csv_path(cfg)
    if not orders_csv.exists():
        log.error("sample_print_missing_orders_csv", extra={"orders_csv": str(orders_csv)})
        print(f"Order list not found: {orders_csv}")
        print("Run convert first, or put Order Numbers.csv in today's output folder.")
        return 2

    combined_name = _combined_pdf_name_for_run(orders_csv=orders_csv, combined_name_override=None)
    batch_number = utc_compact_timestamp().replace("_", "")
    input_key = combined_name if combined_name != "combined" else batch_number
    log = JsonlLogger.for_combined_pdf_run(cfg, combined_pdf_stem=f"sample-{input_key}", date_dir=date_dir)
    log.info("run_start", extra={"command": "sample-print", "input_key": input_key, "sample": True})

    groups = read_and_group_orders(orders_csv)
    if not groups:
        log.error("sample_print_no_orders", extra={"orders_csv": str(orders_csv)})
        print(f"No orders in {orders_csv}")
        return 2

    labels_base = sample_root / "Labels"
    process_pdfs_dir = sample_root / "Process_PDFs" / str(input_key)
    combined_pdfs_dir = sample_root / "Combined_PDFs"
    results: dict[str, ProcessGroupResult] = {}
    all_failures: list[FailureRow] = []
    audit = OrderAuditLogger.for_log(log=log, command="sample-print", run_key=input_key)

    for g in groups:
        proc = str(g.process_number).strip()
        labels_dir = labels_base / f"process_{proc}"
        order_results = [
            process_sample_order(
                log=log,
                process_number=proc,
                order_number=o.order_number,
                customer_name=o.customer_name,
                labels_dir=labels_dir,
            )
            for o in g.orders
        ]
        failures = [r.failure for r in order_results if r.failure is not None]
        all_failures.extend(failures)
        key = f"{int(g.source_index)}::{proc}"
        results[key] = ProcessGroupResult(
            process_number=proc,
            order_count=int(len(g.orders)),
            label_paths=[r.label_pdf_path for r in order_results],
            failures=failures,
            ship_from="SAMPLE",
            source_file=str(g.source_file or ""),
            source_index=int(g.source_index),
        )

    buckets = bucket_process_groups_for_shared_summaries(
        list(results.values()), summary_every=read_label_page_threshold()
    )
    process_pdfs_dir.mkdir(parents=True, exist_ok=True)
    bucket_pdfs = [
        _write_summary_bucket_pdf(
            cfg=cfg,
            log=log,
            batch_number=batch_number,
            bucket=bucket,
            process_pdfs_dir=process_pdfs_dir,
        )
        for bucket in buckets
    ]
    summary_numbers = [str(b.summary_process_number).strip() for b in buckets if b.include_summary]

    if all_failures:
        failures_dir = sample_root / "Error and Failures" / str(input_key)
        failures_dir.mkdir(parents=True, exist_ok=True)
        write_failures_csv(failures_dir / "failures.csv", all_failures)
        append_human_error_log(failures_dir / "error_log.txt", all_failures)

    combined_pdfs_dir.mkdir(parents=True, exist_ok=True)
    combined_pdf = combined_pdfs_dir / f"{combined_name}.pdf"
    missed = None
    if all_failures:
        missed = make_combined_missed_orders_page_pdf(
            missed=[(f.process_number, f.order_number, f.reason) for f in all_failures]
        )
    merge_combined_by_process(out_path=combined_pdf, per_process_pdfs=bucket_pdfs, missed_pdf_bytes=missed)
    try:
        page_count = int(len(PdfReader(str(combined_pdf)).pages))
    except Exception:
        page_count = -1
    log.info("merge_combined_done", extra={"combined_pdf": str(combined_pdf), "page_count": page_count, "sample": True})

    if not _sanity_check_combined_pdf(combined_pdf=combined_pdf, expected_process_numbers=summary_numbers, log=log):
        log.info("run_end", extra={"command": "sample-print", "input_key": input_key, "exit_code": 2})
        print(f"Sample PDF failed the summary check: {combined_pdf}")
        return 2

    total = int(sum(len(g.order_numbers) for g in groups))
    audit.summary(unique_orders=total, process_count=int(len(results)), failure_count=int(len(all_failures)), combined_pdf=str(combined_pdf))
    log.info(
        "sample_print_done",
        extra={
            "process_count": int(len(results)),
            "combined_pdf": str(combined_pdf),
            "failure_count": int(len(all_failures)),
            "process_numbers": sorted([str(g.process_number).strip() for g in groups], key=_process_number_sort_key),
        },
    )
    log.info("run_end", extra={"command": "sample-print", "input_key": input_key, "exit_code": 0})
    print(f"Sample combined PDF: {combined_pdf}")
    print(f"Orders: {total}. Processes: {len(results)}. Failures: {len(all_failures)}.")
    return 0
