"""Combined PDF plus one PDF per DTF file when a run has several batches."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PyPDF2 import PdfReader

from scripts.app.flows.print_labels.summary_buckets import SummaryBucket
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.pdf.merge_combined import merge_combined_by_process
from scripts.app.util.process_numbers import dtf_id_from_stem


@dataclass(frozen=True)
class WrittenPdfs:
    combined_pdf: Path
    batch_pdfs: tuple[Path, ...]


# ponytail: Windows MAX_PATH is 260. Shorten the process-PDF folder when a file
# inside it would pass 250. Upgrade path: \\?\ prefix if that folder name must stay readable.
_WIN_FILE_BUDGET = 250
_PROCESS_PDF_SAMPLE = "process_B8000-S2-22__s99.pdf"


def process_pdf_dir(base: Path, input_key: str) -> Path:
    """Folder for per-process PDFs. A long combined name is hashed when the file path would not fit."""
    direct = base / input_key
    if len(str(direct / _PROCESS_PDF_SAMPLE)) <= _WIN_FILE_BUDGET:
        return direct
    short = hashlib.sha256(input_key.encode("utf-8")).hexdigest()[:12]
    return base / short


def _batch_id(bucket: SummaryBucket) -> str | None:
    src = bucket.members[0].source_file if bucket.members else ""
    if not str(src).strip():
        return None
    return dtf_id_from_stem(Path(str(src)).stem)


def write_combined_and_batch_pdfs(
    *,
    combined_pdfs_dir: Path,
    combined_name: str,
    buckets: list[SummaryBucket],
    bucket_pdfs: list[Path],
    missed_pdf_bytes: bytes | None,
    log: JsonlLogger,
) -> WrittenPdfs:
    """
    Always write `{combined_name}.pdf`.
    When two or more batch ids are present, also write `{batch id}.pdf` for each.
    A single-file run stays one PDF.
    """
    groups: dict[str, list[Path]] = {}
    order: list[str] = []
    for bucket, pdf in zip(buckets, bucket_pdfs):
        bid = _batch_id(bucket)
        if not bid:
            continue
        if bid not in groups:
            order.append(bid)
            groups[bid] = []
        groups[bid].append(pdf)

    combined_pdfs_dir.mkdir(parents=True, exist_ok=True)
    combined_pdf = combined_pdfs_dir / f"{combined_name}.pdf"
    log.info(
        "merge_combined_start",
        extra={
            "combined_pdf": str(combined_pdf),
            "process_pdf_count": int(len(bucket_pdfs)),
            "batch_ids": list(order),
            "missed_orders_page_appended": missed_pdf_bytes is not None,
        },
    )
    merge_combined_by_process(
        out_path=combined_pdf,
        per_process_pdfs=list(bucket_pdfs),
        missed_pdf_bytes=missed_pdf_bytes,
    )
    batch_pdfs: list[Path] = []
    if len(order) >= 2:
        for bid in order:
            path = combined_pdfs_dir / f"{bid}.pdf"
            merge_combined_by_process(out_path=path, per_process_pdfs=groups[bid], missed_pdf_bytes=None)
            batch_pdfs.append(path)
    try:
        page_count = int(len(PdfReader(str(combined_pdf)).pages))
    except Exception:
        page_count = -1
    log.info(
        "merge_combined_done",
        extra={
            "combined_pdf": str(combined_pdf),
            "page_count": int(page_count),
            "batch_pdfs": [str(p) for p in batch_pdfs],
        },
    )
    return WrittenPdfs(combined_pdf=combined_pdf, batch_pdfs=tuple(batch_pdfs))
