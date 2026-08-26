from __future__ import annotations

import asyncio
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from time import monotonic

from PyPDF2 import PdfReader

from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.failures import FailureRow, append_human_error_log, write_failures_csv
from scripts.app.flows.print_labels.process_order import OrderResult, process_one_order
from scripts.app.flows.print_labels.read_group import GroupedOrders, OrderInput, read_and_group_orders
from scripts.app.flows.print_labels.summary_buckets import (
    ProcessGroupResult,
    bucket_process_groups_for_shared_summaries,
)
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.logging.orders_audit import OrderAuditLogger
from scripts.app.pdf.merge_combined import merge_combined_by_process
from scripts.app.pdf.merge_process import merge_process_pdf
from scripts.app.pdf.report_pages import make_combined_missed_orders_page_pdf, make_missed_orders_page_pdf, make_summary_page_pdf
from scripts.app.providers.select_provider import get_provider
from scripts.app.util.time import local_date_ymd, utc_compact_timestamp


def _orders_csv_path(cfg: AppConfig) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    date_dir = out_dir / "Order_Numbers" / local_date_ymd()
    return date_dir / p


def _path_from_repo(value: str | Path) -> Path:
    p = Path(str(value))
    if p.is_absolute():
        return p
    return _repo_root() / p


def _manual_orders_csv_path(cfg: AppConfig) -> Path:
    manual_cfg = cfg.raw.get("manual_print") or {}
    input_csv = str(manual_cfg.get("input_csv", "Manual Print Input/Order Numbers.csv"))
    return _path_from_repo(input_csv)


def _combined_pdf_name_from_orders_dir(orders_dir: Path) -> str:
    """
    Prefer DTF id from convert's manifest (e.g. 3000 -> "3000.pdf").
    """
    manifest_path = orders_dir / "source_manifest.json"
    if not manifest_path.exists():
        return "combined"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8") or "{}")
    except Exception:
        return "combined"
    dtf_id = data.get("dtf_id")
    if isinstance(dtf_id, str) and dtf_id.strip():
        return dtf_id.strip()
    return "combined"


def _combined_pdf_name_for_run(*, orders_csv: Path, combined_name_override: str | None) -> str:
    if combined_name_override is not None and str(combined_name_override).strip():
        return str(combined_name_override).strip()
    return _combined_pdf_name_from_orders_dir(orders_csv.parent)


def _repo_root() -> Path:
    # scripts/app/flows/print_labels/ -> repo root
    return Path(__file__).resolve().parents[4]


_PROCESS_PDF_RE = re.compile(r"process_(\d+)", re.IGNORECASE)


def _process_number_key_from_pdf_path(p: Path) -> int:
    """
    Extract numeric process number from filenames like `process_2.pdf`.

    If parsing fails, return a large key so unknown names sort last.
    """
    m = _PROCESS_PDF_RE.search(p.stem)
    if not m:
        return 1_000_000_000
    try:
        return int(m.group(1))
    except Exception:
        return 1_000_000_000


def _process_number_sort_key(pn: str) -> tuple[int, str]:
    """
    Sort process numbers numerically when possible, else lexicographically.
    """
    s = str(pn).strip()
    if s.isdigit():
        return (0, f"{int(s):020d}")
    return (1, s.lower())


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
        key=_process_number_sort_key,
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


_SUMMARY_PROCESS_MARKER_RE = re.compile(r"PROCESS_NUMBER=([^\r\n]+)", re.IGNORECASE)
_SUMMARY_PROCESS_HINT_RE = re.compile(r"process\s*number\s+(\S+)", re.IGNORECASE)


def _extract_process_number_from_summary_page(text: str) -> str | None:
    """
    Best-effort extraction of the process number from a ReportLab-generated summary page.
    """
    if not text:
        return None
    t = text.replace("\u00a0", " ")
    m = _SUMMARY_PROCESS_MARKER_RE.search(t)
    if m:
        return str(m.group(1)).strip()
    m = _SUMMARY_PROCESS_HINT_RE.search(t)
    if m:
        return str(m.group(1)).strip()
    return None


def _sanity_check_combined_pdf(*, combined_pdf: Path, expected_process_numbers: set[str] | list[str], log: JsonlLogger) -> bool:
    """
    Verify the combined PDF contains exactly the expected summary pages
    (one per bucket; first process number in each bucket).
    Multiplicity matters when different DTF files reuse the same process number.
    """
    try:
        r = PdfReader(str(combined_pdf))
    except Exception as e:
        log.error("combined_pdf_read_failed", extra={"combined_pdf": str(combined_pdf)}, exc=e)
        return False

    found: list[str] = []
    for i, pg in enumerate(r.pages):
        try:
            text = (pg.extract_text() or "").strip()
        except Exception:
            text = ""
        if not text:
            continue
        # Summary pages start with "Batch Summary" in our ReportLab template.
        if not text.lower().startswith("batch summary"):
            continue
        pn = _extract_process_number_from_summary_page(text)
        if pn:
            found.append(pn)
        else:
            log.warning("combined_pdf_summary_parse_failed", extra={"combined_pdf": str(combined_pdf), "page_index": int(i)})

    expected_list = [str(x).strip() for x in expected_process_numbers]
    expected_counts = Counter(expected_list)
    actual_counts = Counter(str(x).strip() for x in found)

    missing = sorted(
        [pn for pn, c in expected_counts.items() if actual_counts.get(pn, 0) < c],
        key=_process_number_sort_key,
    )
    unexpected = sorted(
        [pn for pn, c in actual_counts.items() if expected_counts.get(pn, 0) < c],
        key=_process_number_sort_key,
    )

    ok = expected_counts == actual_counts
    log.info(
        "combined_pdf_sanity_check",
        extra={
            "combined_pdf": str(combined_pdf),
            "page_count": int(len(r.pages)),
            "expected_process_numbers": expected_list,
            "found_summary_process_numbers": found,
        },
    )
    if not ok:
        log.error(
            "combined_pdf_sanity_check_failed",
            extra={
                "combined_pdf": str(combined_pdf),
                "expected_process_count": int(len(expected_list)),
                "found_summary_count": int(len(found)),
                "missing_process_numbers": missing,
                "unexpected_process_numbers": unexpected,
                "expected_counts": dict(expected_counts),
                "actual_counts": dict(actual_counts),
            },
        )
    return ok


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
    combined_name = _combined_pdf_name_for_run(orders_csv=orders_csv, combined_name_override=combined_name_override)
    input_key = combined_name if combined_name != "combined" else batch_number
    log = run_log_override or JsonlLogger.for_combined_pdf_run(cfg, combined_pdf_stem=input_key, date_dir=date_dir)

    # Process PDFs are scoped per input key to avoid mixing runs on the same day:
    #   output/Process_PDFs/<date>/<input_key>/process_<n>.pdf
    # Keep the old base dir for backwards-compatible recovery.
    process_pdfs_base_dir = process_pdfs_base_dir_override or (out_dir / "Process_PDFs" / date_dir)
    process_pdfs_dir = process_pdfs_base_dir / str(input_key)
    combined_pdf = combined_pdfs_dir / f"{combined_name}.pdf"

    if not allow_existing_outputs:
        existing = [
            str(p)
            for p in (combined_pdf, process_pdfs_dir)
            if p.exists()
        ]
        if existing:
            log.error(
                "print_refusing_to_overwrite_outputs",
                extra={"input_key": input_key, "existing_paths": existing},
            )
            log.info("run_end", extra={"command": command_name, "input_key": input_key, "exit_code": 2})
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

    process_results_by_key: dict[str, ProcessGroupResult] = {}
    all_failures: list[FailureRow] = []
    input_group_keys: set[str] = {
        f"{int(g.source_index)}::{str(g.process_number).strip()}" for g in groups
    }
    log.info(
        "print_groups_loaded",
        extra={
            "group_count": int(len(groups)),
            "expected_process_numbers": sorted(
                [str(g.process_number).strip() for g in groups],
                key=_process_number_sort_key,
            ),
            "orders_per_process": {
                f"{int(g.source_index)}:{g.process_number}": int(len(g.order_numbers)) for g in groups
            },
            "source_files": sorted({str(g.source_file) for g in groups if g.source_file}),
            "total_orders": total_orders,
        },
    )

    async def runner() -> None:
        nonlocal process_results_by_key, all_failures
        provider = get_provider(cfg, log)
        conc = cfg.raw.get("concurrency") or {}
        max_groups = int(conc.get("max_process_groups", 3))
        group_sem = asyncio.Semaphore(max(1, max_groups))

        async def _run_one_group(g) -> ProcessGroupResult:
            async with group_sem:
                return await _run_process_group(
                    cfg=cfg,
                    log=log,
                    provider=provider,
                    process_number=g.process_number,
                    orders=g.orders,
                    labels_base_dir=labels_base_dir,
                    audit=audit,
                    source_file=g.source_file,
                    source_index=g.source_index,
                )

        tasks = [_run_one_group(g) for g in groups]
        try:
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                except Exception as e:
                    log.error("print_process_group_failed", exc=e)
                    raise
                else:
                    key = f"{int(result.source_index)}::{str(result.process_number).strip()}"
                    process_results_by_key[key] = result
                    all_failures.extend(result.failures)
        finally:
            from scripts.app.flows.amendments.shipstation_tags import clear_account_tags_cache

            clear_account_tags_cache()
            aclose = getattr(provider, "aclose", None)
            if callable(aclose):
                await aclose()

    asyncio.run(runner())
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
        combined_name = _combined_pdf_name_for_run(orders_csv=orders_csv, combined_name_override=combined_name_override)
        failures_key = combined_name if combined_name != "combined" else batch_number
        import sys
        _wh_root = _repo_root().parent
        if str(_wh_root) not in sys.path:
            sys.path.insert(0, str(_wh_root))
        from shared import paths as wh
        failures_dir = failures_dir_override or (
            wh.shipping_errors_dir() / date_dir / failures_key
        )
        failures_dir.mkdir(parents=True, exist_ok=True)
        failures_csv = failures_dir / "failures.csv"
        error_log = failures_dir / "error_log.txt"
        write_failures_csv(failures_csv, all_failures)
        append_human_error_log(error_log, all_failures)

    combined_pdfs_dir.mkdir(parents=True, exist_ok=True)
    combined_name = _combined_pdf_name_for_run(orders_csv=orders_csv, combined_name_override=combined_name_override)
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
    merge_combined_by_process(out_path=combined_pdf, per_process_pdfs=per_process_pdfs_sorted, missed_pdf_bytes=combined_missed)
    try:
        page_count = int(len(PdfReader(str(combined_pdf)).pages))
    except Exception:
        page_count = -1
    log.info("merge_combined_done", extra={"combined_pdf": str(combined_pdf), "page_count": int(page_count)})

    if not _sanity_check_combined_pdf(combined_pdf=combined_pdf, expected_process_numbers=summary_process_numbers, log=log):
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

def run_manual_print(cfg: AppConfig, log: JsonlLogger, *, replace_job_id: str | None = None) -> int:
    """
    Print from the fixed manual CSV under Manual Outputs/.

    Job id is derived from process numbers in the CSV (e.g. "2000-2400-2450").
    Replace runs archive existing outputs for that job id before reprinting.
    """
    date_dir = local_date_ymd()
    manual_csv = _manual_orders_csv_path(cfg)
    if not manual_csv.exists():
        log.error("manual_print_missing_orders_csv", extra={"orders_csv": str(manual_csv)})
        print(f"Manual print input not found: {manual_csv}")
        print("Create it with columns: Process Number, Order Number, Customer Name")
        return 2

    try:
        groups = read_and_group_orders(manual_csv)
    except Exception as e:
        log.error("manual_print_read_failed", extra={"orders_csv": str(manual_csv)}, exc=e)
        print(f"Manual print input could not be read: {manual_csv}")
        return 2

    if not groups:
        log.error("manual_print_no_orders", extra={"orders_csv": str(manual_csv)})
        print(f"Manual print input has no orders: {manual_csv}")
        return 2

    process_numbers = {str(g.process_number).strip() for g in groups if str(g.process_number).strip()}
    try:
        expected_job_id = _manual_job_id_from_groups(groups)
    except ValueError as e:
        log.error("manual_print_invalid_job_id", exc=e)
        print("Manual print input has no valid process numbers.")
        return 2

    if replace_job_id is not None:
        job_id = str(replace_job_id).strip()
        if not job_id:
            log.error("manual_print_invalid_replace_job_id", extra={"job_id": job_id})
            print("Replace job id is required, for example: 2000-2400-2450")
            return 2
        if job_id != expected_job_id:
            log.error(
                "manual_print_replace_job_id_mismatch",
                extra={"entered_job_id": job_id, "expected_job_id": expected_job_id},
            )
            print(f"Replace job id must match current CSV processes: {expected_job_id}")
            return 2
        _archive_existing_manual_job(
            cfg=cfg,
            date_dir=date_dir,
            job_id=job_id,
            process_numbers=process_numbers,
            log=log,
        )
        allow_existing_outputs = True
    else:
        job_id = expected_job_id
        if _manual_job_has_outputs(cfg=cfg, date_dir=date_dir, job_id=job_id):
            log.error("manual_print_job_already_exists", extra={"job_id": job_id, "date_dir": date_dir})
            print(f"Manual print outputs already exist for job: {job_id}")
            print("Use option 2 (Replace existing job) to archive and reprint.")
            return 2
        allow_existing_outputs = False

    log.info(
        "manual_print_selected_job",
        extra={
            "job_id": job_id,
            "orders_csv": str(manual_csv),
            "replace": bool(replace_job_id),
            "process_numbers": sorted(process_numbers, key=_process_number_sort_key),
        },
    )
    print(f"Manual Print job id: {job_id}")
    _write_manual_input_log(
        cfg=cfg,
        date_dir=date_dir,
        job_id=job_id,
        manual_csv=manual_csv,
        groups=groups,
        replace=bool(replace_job_id),
    )

    manual_output_root = _manual_output_root(cfg)
    manual_log = JsonlLogger.for_manual_print_run(cfg, job_id=job_id, date_dir=date_dir)
    manual_job_log_dir = _manual_logs_job_dir(cfg=cfg, date_dir=date_dir, job_id=job_id)

    return run_print(
        cfg,
        log,
        orders_csv_override=manual_csv,
        combined_name_override=job_id,
        labels_base_dir_override=manual_output_root / "Labels" / date_dir,
        combined_pdfs_dir_override=manual_output_root / "Combined_PDFs" / date_dir,
        process_pdfs_base_dir_override=manual_output_root / "Process_PDFs" / date_dir / "Manual",
        failures_dir_override=manual_job_log_dir,
        run_log_override=manual_log,
        command_name="manual-print",
        allow_existing_outputs=allow_existing_outputs,
    )

