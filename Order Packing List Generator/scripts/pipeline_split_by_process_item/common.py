import re
from datetime import date
from pathlib import Path

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)

from scripts.pipeline_runtime.order_number_csv import (
    coerce_order_number_columns as _coerce_order_number_columns,
    order_number_to_str as _order_number_to_str,
)

from .config import BLANK_FILENAME, INVALID_FILENAME_CHARS


def _normalize(val) -> str:
    """Strip and return string; empty if NaN/blank."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def _normalize_key(val) -> str:
    """Strip and lowercase for matching."""
    return _normalize(val).lower()


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


def is_pure_numeric_process_base(base: str) -> bool:
    """True when process base is digits only (tracker/fixed numeric processes)."""
    return _normalize_numeric_process_base(base) is not None


def _order_number_column(df: pd.DataFrame) -> str | None:
    """Return the actual 'Order Number' column name (exact or normalized match), or None if missing."""
    if "Order Number" in df.columns:
        return "Order Number"
    for c in df.columns:
        if _normalize_key(str(c)) == "order number":
            return c
    return None


def _reorder_columns_for_output(df: pd.DataFrame) -> pd.DataFrame:
    """Put Order Number first (if present), other columns in middle, Order Number (Base) last."""
    on_col = _order_number_column(df)
    base_col = "Order Number (Base)"
    cols = list(df.columns)
    first = [on_col] if on_col and on_col in cols else []
    last = [base_col] if base_col in cols else []
    mid = [c for c in cols if c not in first and c not in last]
    return df[[*first, *mid, *last]]


def _customise_is_yes(val) -> bool:
    """True if Customise is 'Yes' (case-insensitive, trimmed)."""
    if pd.isna(val):
        return False
    return str(val).strip().lower() == "yes"


def _logo_design_tokens(logo_design_val) -> list[str]:
    """Split Logo/Design Image into comma-separated tokens (max 5, trimmed, non-empty)."""
    if pd.isna(logo_design_val):
        return []
    s = str(logo_design_val).strip()
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()][:5]


def _apply_draw_replace(
    row: pd.Series,
    position_val: str,
    *,
    position_code_to_draw: dict[str, str] | None,
    default_position_code: str,
) -> str:
    """Replace CL position text with workbook Draw value via Position Code."""
    if not position_code_to_draw or "Position Code" not in row.index:
        return position_val
    pos_code = _normalize(row.get("Position Code", ""))
    if not pos_code:
        return position_val
    if pos_code == default_position_code:
        return ""
    draw_val = lookup_draw_for_position_code(position_code_to_draw, pos_code)
    if draw_val:
        return draw_val
    return position_val


def _merge_positions_for_single_custom_logo(
    row: pd.Series,
    *,
    position_code_to_draw: dict[str, str] | None = None,
    default_position_code: str = "X",
) -> str:
    """
    Replace Position with workbook Draw (via Position Code), then when Logo/Design Image
    has a single token and Position lists multiple comma-separated values, merge with ' / '.
    """
    original = row.get("Position")
    if pd.isna(original):
        return ""
    position_val = _normalize(original)
    if not position_val:
        return original

    position_val = _apply_draw_replace(
        row,
        position_val,
        position_code_to_draw=position_code_to_draw,
        default_position_code=default_position_code,
    )
    if not position_val:
        return ""

    logo_tokens = _logo_design_tokens(row.get("Logo/Design Image"))
    if len(logo_tokens) != 1:
        return position_val

    parts = [p.strip() for p in position_val.split(",") if p.strip()]
    if len(parts) <= 1:
        return position_val

    return " / ".join(parts)


def _position_after_merge(
    row: pd.Series,
    *,
    position_code_to_draw: dict[str, str] | None = None,
    default_position_code: str = "X",
) -> str:
    """Draw replace via Position Code, then slash merge for single-logo rows."""
    return _merge_positions_for_single_custom_logo(
        row,
        position_code_to_draw=position_code_to_draw,
        default_position_code=default_position_code,
    )


def _resolve_workbook_path(workbook_path: Path) -> Path:
    """Return workbook path; must be Workbook.xlsx."""
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    return workbook_path


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


def sanitize_filename(value: str) -> str:
    """Make a safe filename: replace invalid chars with underscore; empty -> _blank."""
    if not _normalize(value):
        return BLANK_FILENAME
    s = INVALID_FILENAME_CHARS.sub("_", str(value).strip())
    return s if s else BLANK_FILENAME

