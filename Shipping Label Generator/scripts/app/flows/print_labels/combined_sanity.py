from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from PyPDF2 import PdfReader

from app.logging.jsonl import JsonlLogger
from app.util.process_numbers import process_number_sort_key

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
        key=process_number_sort_key,
    )
    unexpected = sorted(
        [pn for pn, c in actual_counts.items() if expected_counts.get(pn, 0) < c],
        key=process_number_sort_key,
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

