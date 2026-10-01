import re
from pathlib import Path
import pandas as pd
from .config import (
    DTF_COL_COMPANY_LABEL,
    DTF_COL_OLD_LABEL,
    EXCEL_PROCESS_NO_DASH,
    _DTF_DESIGN_HEAD_FAWAD,
    _DTF_DESIGN_HEAD_LG,
    _DTF_DESIGN_HEAD_PER,
)
def _normalize(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()
def _tracker_seq_from_val(val) -> str | None:
    """If 'Process and Item Number' is tracker format 'Process 31 Item-1 (...)', return the number as string (e.g. '31'); else None."""
    s = _normalize(val)
    m = re.match(r"^Process\s+(\d+)\s+Item", s)
    return m.group(1) if m else None
def _file_level_seq(df: pd.DataFrame, process_base: str) -> str:
    col = "Process and Item Number"
    if col not in df.columns:
        return process_base
    for val in df[col].dropna().astype(str):
        s = _normalize(val)
        if not s:
            continue
        seq = _tracker_seq_from_val(s)
        if seq is not None:
            return seq
    return process_base
def _process_number_for_excel_from_row(process_and_item_val) -> str:
    seq = _tracker_seq_from_val(process_and_item_val)
    if seq is not None:
        return seq
    extended = _extended_process_and_item_number(process_and_item_val)
    process_plus = _process_plus_additional(extended)
    return _process_number_for_excel(process_plus)
def _extended_process_and_item_number(val) -> str:
    s = _normalize(val)
    m = re.search(r"\(([^)]+)\)", s)
    if m:
        return m.group(1).strip()
    # New PIN: B100-S1-1 Item 1  →  B100-S1-1-1
    batch_pin = re.match(r"^(.+?)\s+Item[-\s](\d+)$", s, re.IGNORECASE)
    if batch_pin and not s.lower().startswith("process "):
        return f"{batch_pin.group(1)}-{batch_pin.group(2)}"
    simple = re.match(r"^Process\s+(.+?)\s+Item-(\d+)$", s)
    if simple:
        return f"{simple.group(1)}-{simple.group(2)}"
    return s
def _process_number_for_excel(process_plus: str) -> str:
    s = _normalize(process_plus)
    if not s:
        return ""
    if not EXCEL_PROCESS_NO_DASH:
        return s
    idx = s.rfind("-")
    if idx <= 0:
        return s
    return s[:idx] + s[idx + 1 :]
def _process_plus_additional(extended: str) -> str:
    """Filename + inside-file -N. Spaces in WAREHOUSE STOCK are part of the name.

    Old tracker parenthetical was `{base}-{N} {item}` (space before item).
    New PIN extends as `{filename}-{N}-{item}` (last hyphen is the item).
    """
    s = _normalize(extended)
    if not s:
        return ""
    old = re.fullmatch(r"(.+-\d+)\s+(\d+)", s)
    if old:
        return old.group(1)
    idx = s.rfind("-")
    if idx <= 0:
        return s
    return s[:idx]
def _base_additional_no_dash(extended: str) -> str:
    process_plus = _process_plus_additional(extended)
    if not process_plus:
        return ""
    idx = process_plus.rfind("-")
    if idx <= 0:
        return process_plus
    return process_plus[:idx] + process_plus[idx + 1 :]
def _item_number_from_extended(extended: str) -> str:
    s = _normalize(extended)
    if not s:
        return ""
    old = re.fullmatch(r".+-\d+\s+(\d+)", s)
    if old:
        return old.group(1)
    idx = s.rfind("-")
    if idx < 0:
        return ""
    return s[idx + 1 :].strip()
