"""Preflight result types and small format helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class PreflightResult:
    path: Path
    unmatched_count: int
    missing_logo_count: int
    missing_apparel_count: int
    issue_row_count: int


@dataclass(frozen=True)
class WorkbookCache:
    cl_lookup: dict
    logo_id_to_position: Optional[dict[str, str]]
    default_code: str
    position_to_code: dict[str, str]
    multiple_positions_df: Optional[pd.DataFrame]


# Backward-compatible private alias (tests / older callers).
_WorkbookCache = WorkbookCache


def _is_blank(val) -> bool:
    """True if value is missing, empty string, or whitespace-only."""
    if pd.isna(val):
        return True
    if not isinstance(val, str):
        val = str(val)
    return val.strip() == ""


def _yes_no(flag: bool) -> str:
    return "Yes" if flag else "No"


def _fmt_secs(seconds: float) -> str:
    if seconds < 10:
        return f"{seconds:.1f}s"
    return f"{seconds:.0f}s"
