from __future__ import annotations
import re
from datetime import date
from pathlib import Path
import pandas as pd
from pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)
from pipeline_runtime.order_number_csv import (
    coerce_order_number_columns as _coerce_order_number_columns,
    order_number_to_str as _order_number_to_str,
)
from .config import BLANK_FILENAME, INVALID_FILENAME_CHARS


def _normalize(val) -> str:
    """Strip and return string; empty if NaN/blank."""
    if pd.isna(val):
        return ""
    return str(val).strip()


_BATCH_SHIFT_RE = re.compile(r"^(B\d+-S\d+)", re.IGNORECASE)


def _parse_ship_by(ship_by_val) -> date | None:
    """Parse Ship By as DD-MM-YYYY or D/M/YYYY. Return date or None if empty/invalid."""
    s = _normalize(ship_by_val)
    if not s:
        return None
    # DD-MM-YYYY
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    # D/M/YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    # ISO YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None
def _normalize_numeric_process_base(base: str) -> str | None:
    """Return integer process base string when base is purely numeric (e.g. 10000, 10000.0); else None."""
    s = _normalize(base)
    if not s:
        return None
    if re.fullmatch(r"\d+", s):
        return s
    try:
        num = float(s)
    except (TypeError, ValueError):
        return None
    if num.is_integer():
        return str(int(num))
    return None
def pin_batch_shift(stem: str) -> str:
    """Visible process base from sorter/input stem: B100-S1-PRINTED-… → B100-S1.

    Used for PIN, Step 6/7/8 file stems, and preflight Process Number.
    Non-B#-S# stems (RESEND, UNMATCHED, numeric tracker ids) stay whole.
    """
    s = _normalize(stem)
    m = _BATCH_SHIFT_RE.match(s)
    return m.group(1) if m else s
def _reorder_columns_for_output(df: pd.DataFrame) -> pd.DataFrame:
    """Put Order Number first (if present), other columns in middle, Order Number (Base) last."""
    on_col = _order_number_column(df)
    base_col = "Order Number (Base)"
    cols = list(df.columns)
    first = [on_col] if on_col and on_col in cols else []
    last = [base_col] if base_col in cols else []
    mid = [c for c in cols if c not in first and c not in last]
    return df[[*first, *mid, *last]]
def _order_number_column(df: pd.DataFrame) -> str | None:
    """Return the actual 'Order Number' column name (exact or normalized match), or None if missing."""
    if "Order Number" in df.columns:
        return "Order Number"
    for c in df.columns:
        if _normalize_key(str(c)) == "order number":
            return c
    return None
def format_batch_pin(base: str, process_number: int, item: int) -> str:
    """Supervisor 2026-09-23: B100-S1-1 Item 1 (no Process prefix; Item with space)."""
    short = pin_batch_shift(base)
    if short:
        return f"{short}-{process_number} Item {item}"
    return f"{process_number} Item {item}"
def sanitize_filename(value: str) -> str:
    """Make a safe filename: replace invalid chars with underscore; empty -> _blank."""
    if not _normalize(value):
        return BLANK_FILENAME
    s = INVALID_FILENAME_CHARS.sub("_", str(value).strip())
    return s if s else BLANK_FILENAME
def _resolve_workbook_path(workbook_path: Path) -> Path:
    """Return workbook path; must be Workbook.xlsx."""
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    return workbook_path
def _normalize_key(val) -> str:
    """Strip and lowercase for matching."""
    return _normalize(val).lower()
def is_pure_numeric_process_base(base: str) -> bool:
    """True when process base is digits only (tracker/fixed numeric processes)."""
    return _normalize_numeric_process_base(base) is not None
