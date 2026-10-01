"""Preflight audit: unmatched SKUs + missing logo/apparel dry-run."""

from __future__ import annotations

from pipeline_preflight_issues.service_audit import run_preflight_audit, run_unmatched_extraction
from pipeline_preflight_issues.service_images import _WAREHOUSE
from pipeline_preflight_issues.service_prep import _CSV_MAX_WORKERS, _load_workbook_cache, _process_one_csv
from pipeline_preflight_issues.service_types import PreflightResult, _WorkbookCache, _fmt_secs, _is_blank, _yes_no

__all__ = [
    "PreflightResult",
    "_CSV_MAX_WORKERS",
    "_WAREHOUSE",
    "_WorkbookCache",
    "_fmt_secs",
    "_is_blank",
    "_load_workbook_cache",
    "_process_one_csv",
    "_yes_no",
    "run_preflight_audit",
    "run_unmatched_extraction",
]
