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
from pipeline_split_by_process_item.common_impl import (
    _BATCH_SHIFT_RE,
    _normalize,
    _parse_ship_by,
    _normalize_numeric_process_base,
    pin_batch_shift,
    _reorder_columns_for_output,
    _order_number_column,
    format_batch_pin,
    sanitize_filename,
    _resolve_workbook_path,
    _normalize_key,
    is_pure_numeric_process_base,
)


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

