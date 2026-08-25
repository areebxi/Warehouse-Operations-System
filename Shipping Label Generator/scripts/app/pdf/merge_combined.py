from __future__ import annotations

import io
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


def _end_exclusive_excluding_missed(r: PdfReader) -> int:
    # Heuristic: if last page title starts with "Missed Orders", exclude it.
    if len(r.pages) == 0:
        return 0
    last_idx = len(r.pages) - 1
    last_text = ""
    try:
        last_text = (r.pages[last_idx].extract_text() or "").strip()
    except Exception:
        last_text = ""
    if last_text.lower().startswith("missed orders"):
        return max(1, len(r.pages) - 1)
    return len(r.pages)


def merge_combined_single_summary(
    *,
    out_path: Path,
    batch_summary_pdf_bytes: bytes,
    per_process_pdfs: list[Path],
) -> None:
    """
    Combined output: one batch summary page, then all label pages across all processes.

    Assumes each per-process PDF is: Summary (page 0), then label pages, then optional missed page at end.
    Excludes per-process summary pages and any missed page.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()

    # Batch-level summary as first page.
    br = PdfReader(io.BytesIO(batch_summary_pdf_bytes))
    for pg in br.pages:
        w.add_page(pg)

    # Add label pages from each process PDF (exclude per-process summary, exclude missed page).
    for proc_path in per_process_pdfs:
        r = PdfReader(proc_path)
        end_exclusive = _end_exclusive_excluding_missed(r)
        # IMPORTANT: use writer.append() to safely import pages.
        # Adding PageObjects directly across many readers can lead to nondeterministic
        # object reuse / wrong ordering in the output PDF.
        if end_exclusive > 1:
            w.append(proc_path, pages=(1, end_exclusive))

    with out_path.open("wb") as f:
        w.write(f)


def merge_combined_by_process(
    *,
    out_path: Path,
    per_process_pdfs: list[Path],
    missed_pdf_bytes: bytes | None = None,
) -> None:
    """
    Concatenate per-process PDFs without repeating summary pages.

    Assumes each per-process PDF is: Summary (page 0), then label pages, then optional missed page at end.
    Combined output includes summary once per process, then all label pages (missed pages excluded).
    If `missed_pdf_bytes` is provided, it is appended once at the end.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()

    for proc_path in per_process_pdfs:
        r = PdfReader(proc_path)
        end_exclusive = _end_exclusive_excluding_missed(r)
        if end_exclusive > 0:
            w.append(proc_path, pages=(0, end_exclusive))

    if missed_pdf_bytes is not None:
        mr = PdfReader(io.BytesIO(missed_pdf_bytes))
        for pg in mr.pages:
            w.add_page(pg)

    with out_path.open("wb") as f:
        w.write(f)


def merge_combined_alternating(
    *,
    out_path: Path,
    per_process_pdfs: list[Path],
) -> None:
    """
    Round-robin across processes: Summary, Label, Summary, Label, ...

    Assumes each per-process PDF is: Summary (page 0), then label pages, then optional missed page at end.
    Combined output includes only summary+label pages (missed pages excluded).

    Behavior: interleave label pages across processes instead of exhausting one process at a time.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()

    # Round-robin across processes while importing pages safely via append().
    # We first compute the label page indices for each process (excluding summary and missed page).
    proc_label_indices: list[tuple[Path, list[int]]] = []
    for proc_path in per_process_pdfs:
        r = PdfReader(proc_path)
        end_exclusive = _end_exclusive_excluding_missed(r)
        if end_exclusive <= 1:
            continue
        proc_label_indices.append((proc_path, list(range(1, end_exclusive))))

    made_progress = True
    while made_progress:
        made_progress = False
        for proc_path, label_idxs in proc_label_indices:
            if not label_idxs:
                continue
            made_progress = True
            # Summary page
            w.append(proc_path, pages=[0])
            # Next label page
            w.append(proc_path, pages=[label_idxs.pop(0)])

    with out_path.open("wb") as f:
        w.write(f)

