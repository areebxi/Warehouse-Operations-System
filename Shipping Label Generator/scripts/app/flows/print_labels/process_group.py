from __future__ import annotations

import asyncio
from collections import Counter
from pathlib import Path
from time import monotonic

from app.config.load import AppConfig
from app.flows.print_labels.failures import FailureRow
from app.flows.print_labels.process_order import OrderResult, process_one_order
from app.flows.print_labels.read_group import OrderInput
from app.flows.print_labels.summary_buckets import ProcessGroupResult
from app.logging.jsonl import JsonlLogger
from app.logging.orders_audit import OrderAuditLogger
from app.pdf.merge_process import merge_process_pdf
from app.pdf.report_pages import make_missed_orders_page_pdf, make_summary_page_pdf

async def _run_process_group(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider,
    process_number: str,
    orders: list[OrderInput],
    labels_base_dir: Path,
    audit: OrderAuditLogger | None = None,
    source_file: str = "",
    source_index: int = 0,
) -> ProcessGroupResult:
    """
    Fetch/create labels for one CSV process group.

    Does not write the process PDF yet — PDFs are built after all groups finish.
    Single-label consecutive processes may share one summary page within the same
    DTF/source file; each new DTF file always starts a fresh summary page.
    """
    labels_dir = labels_base_dir / f"process_{process_number}"
    t0 = monotonic()
    log.info(
        "print_process_group_start",
        extra={
            "process_number": str(process_number),
            "order_count": int(len(orders)),
            "orders_preview": [str(o.order_number) for o in orders[:5]],
            "labels_dir": str(labels_dir),
            "source_file": str(source_file or ""),
            "source_index": int(source_index),
        },
    )

    async def _wrap(o: OrderInput) -> OrderResult:
        return await process_one_order(
            cfg=cfg,
            log=log,
            provider=provider,
            process_number=process_number,
            order_number=o.order_number,
            customer_name_from_input=o.customer_name,
            labels_dir=labels_dir,
            audit=audit,
        )

    results = await asyncio.gather(*[_wrap(o) for o in orders])

    label_paths: list[Path] = [r.label_pdf_path for r in results]
    ship_from_counts: Counter[str] = Counter()
    for r in results:
        if r.ship_from:
            ship_from_counts[str(r.ship_from).strip()] += 1
    ship_from = ship_from_counts.most_common(1)[0][0] if ship_from_counts else ""

    failures: list[FailureRow] = []
    for r in results:
        if r.failure is not None:
            failures.append(r.failure)

    if audit is not None:
        audit.record(
            outcome="print_process_done",
            order_number=str(process_number),
            process_number=str(process_number),
            label_pdf_count=int(len(label_paths)),
            failure_count=int(len(failures)),
            ship_from=str(ship_from or ""),
            source_file=str(source_file or ""),
        )
    log.info(
        "print_process_group_done",
        extra={
            "process_number": str(process_number),
            "label_pdf_count": int(len(label_paths)),
            "failure_count": int(len(failures)),
            "ship_from": str(ship_from or ""),
            "source_file": str(source_file or ""),
            "elapsed_sec": float(monotonic() - t0),
        },
    )
    return ProcessGroupResult(
        process_number=str(process_number).strip(),
        order_count=int(len(orders)),
        label_paths=label_paths,
        failures=failures,
        ship_from=str(ship_from or ""),
        source_file=str(source_file or ""),
        source_index=int(source_index),
    )

def _write_summary_bucket_pdf(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    batch_number: str,
    bucket,
    process_pdfs_dir: Path,
) -> Path:
    """Write one process PDF for a summary bucket (shared or solo)."""
    src_idx = int(bucket.members[0].source_index) if bucket.members else 0
    src_file = str(bucket.members[0].source_file) if bucket.members else ""
    # Avoid filename collisions when different DTF files reuse a process number.
    if src_file and src_idx > 0:
        process_pdf_path = process_pdfs_dir / f"process_{bucket.summary_process_number}__s{src_idx}.pdf"
    else:
        process_pdf_path = process_pdfs_dir / f"process_{bucket.summary_process_number}.pdf"
    ship_from = bucket.ship_from or str(cfg.raw.get("batch", {}).get("ship_from", ""))
    summary = make_summary_page_pdf(
        process_number=bucket.summary_process_number,
        batch_number=batch_number,
        batch_notes=str(cfg.raw.get("batch", {}).get("notes", "")),
        processed_by=str(cfg.raw.get("batch", {}).get("processed_by", "")),
        ship_from=ship_from,
        label_count=int(bucket.label_count),
    )
    missed = None
    failures = list(bucket.failures)
    if failures:
        missed = make_missed_orders_page_pdf(
            process_number=bucket.summary_process_number,
            missed=[(f.order_number, f.reason) for f in failures],
        )
    merge_process_pdf(
        out_path=process_pdf_path,
        summary_pdf_bytes=summary,
        label_pdf_paths=list(bucket.label_paths),
        missed_pdf_bytes=missed,
    )
    log.info(
        "print_summary_bucket_pdf_written",
        extra={
            "summary_process_number": str(bucket.summary_process_number),
            "member_process_numbers": list(bucket.process_numbers),
            "label_count": int(bucket.label_count),
            "failure_count": int(len(failures)),
            "process_pdf_path": str(process_pdf_path),
            "shared_summary": bool(len(bucket.members) > 1),
            "source_file": src_file,
            "source_index": src_idx,
        },
    )
    return process_pdf_path

