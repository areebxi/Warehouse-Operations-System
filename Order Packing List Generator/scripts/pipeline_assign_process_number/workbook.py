from pathlib import Path

import pandas as pd

from .config import (
    COL_GENDER_APPAREL,
    COL_PROCESS_START,
    COL_SHIFT_CODE,
    COL_SHIFT_LABEL,
    PROCESS_INFO_SHEET,
    SHIFT_FALLBACK,
)
from .normalize import _normalize, _normalize_key, _normalize_process_start, _resolve_workbook_path


def load_process_info_sheet(workbook_path: Path) -> pd.DataFrame:
    """Load full 'Process Info Sheet' from workbook."""
    path = _resolve_workbook_path(workbook_path)
    df = pd.read_excel(
        path,
        sheet_name=PROCESS_INFO_SHEET,
        engine="openpyxl",
        header=0,
    )
    if df.empty:
        raise ValueError(f"Sheet '{PROCESS_INFO_SHEET}' is empty.")
    return df


def _col_index_by_header(df: pd.DataFrame, names: list[str]) -> int | None:
    """Return first column index whose header (normalized) contains any of the given names."""
    for i, col in enumerate(df.columns):
        c = _normalize_key(col)
        for n in names:
            if n in c or c in n:
                return i
    return None


def build_gender_to_start_number(df: pd.DataFrame) -> dict[str, str]:
    """Build map: normalized Gender Apparel -> Process Start Number (column B)."""
    a_idx = _col_index_by_header(df, ["gender apparel", "gender"])
    if a_idx is None:
        a_idx = COL_GENDER_APPAREL
    b_idx = _col_index_by_header(df, ["process start number", "process start"])
    if b_idx is None:
        b_idx = COL_PROCESS_START
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        key = _normalize_key(row.iloc[a_idx])
        val = row.iloc[b_idx]
        if key and not pd.isna(val):
            out[key] = _normalize_process_start(val)
    return out


def get_shift_code(df: pd.DataFrame, shift_input: str) -> str:
    """Resolve user shift (e.g. '1st', '2nd') to code from column E. Match column D to 'Nth Shift'."""
    d_idx = _col_index_by_header(df, ["shift"]) if df.shape[1] > COL_SHIFT_LABEL else COL_SHIFT_LABEL
    if d_idx is None:
        d_idx = COL_SHIFT_LABEL
    e_idx = COL_SHIFT_CODE if df.shape[1] > COL_SHIFT_CODE else d_idx + 1
    shift_clean = _normalize(shift_input).lower()
    # Normalize to "1st shift", "2nd shift", etc.
    if shift_clean and "shift" not in shift_clean:
        shift_clean = f"{shift_clean} shift"
    for _, row in df.iterrows():
        label = _normalize_key(row.iloc[d_idx])
        if label and shift_clean and (shift_clean in label or label in shift_clean):
            code = row.iloc[e_idx]
            if not pd.isna(code) and _normalize(code):
                return _normalize(code)
            break
    # Fallback from shift input: 1st->A, 2nd->B, 3rd->C, 4th->D, 5th->E
    shift_key = _normalize(shift_input).lower().replace(" shift", "").strip()
    if shift_key in SHIFT_FALLBACK:
        return SHIFT_FALLBACK[shift_key]
    # Last resort: treat as 1st
    return "A"

