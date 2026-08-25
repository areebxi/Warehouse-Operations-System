from pathlib import Path

import pandas as pd

from .config import (
    DEFAULT_POSITION_LABEL,
    LIP_LOGO_ID_COL,
    LIP_POSITION_COL,
    LOGO_IDS_TO_POSITIONS_SHEET,
    MULTIPLE_POSITIONS_SHEET,
    DP_ABBREVIATION_COL,
    DP_POSITION_COLS,
    PROCESS_INFO_SHEET,
)
from .normalize import _normalize_label, _normalize_logo_id_key


def _find_pq_columns_by_header(df: pd.DataFrame) -> list[int] | None:
    """If sheet has < 17 columns, try to find P/Q by header name. Returns [p_idx, q_idx] or None."""
    cols = [str(c).strip().lower() for c in df.columns]
    p_idx = None
    q_idx = None
    for i, c in enumerate(cols):
        if "position" in c and ("combination" in c or "combinations" in c):
            if p_idx is None:
                p_idx = i
        if "code" in c and q_idx is None:
            q_idx = i
    if p_idx is not None and q_idx is not None and p_idx != q_idx:
        return [p_idx, q_idx]
    return None


def _find_pq_columns_by_value(df: pd.DataFrame) -> list[int] | None:
    """Find column that contains 'Default Position' as a value; use it and the next column as P, Q."""
    for i in range(df.shape[1]):
        col = df.iloc[:, i]
        for v in col:
            if _normalize_label(v).lower() == DEFAULT_POSITION_LABEL.lower():
                if i + 1 < df.shape[1]:
                    return [i, i + 1]
                break
    return None


def load_process_info_pq(workbook_path: Path) -> pd.DataFrame:
    """
    Load Process Info Sheet, return DataFrame with columns P and Q only.
    Prefer Excel P/Q (indices 15, 16) if sheet has >= 17 columns; else try
    columns by header (e.g. 'Position Combinations' and 'Code').
    """
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    df = pd.read_excel(
        workbook_path,
        sheet_name=PROCESS_INFO_SHEET,
        engine="openpyxl",
        header=0,
    )
    if df.shape[1] >= 17:
        df = df.iloc[:, [15, 16]].copy()
    else:
        indices = _find_pq_columns_by_header(df) or _find_pq_columns_by_value(df)
        if indices is None:
            raise ValueError(
                f"Sheet '{PROCESS_INFO_SHEET}' has {df.shape[1]} columns (need 17 for P/Q). "
                "Alternatively add a column containing 'Default Position' (and next column for codes)."
            )
        df = df.iloc[:, indices].copy()
    df.columns = ["P", "Q"]
    return df


def load_multiple_positions(workbook_path: Path) -> pd.DataFrame | None:
    """
    Load Workbook 'Multiple Positions' sheet if present.
    Returns DataFrame with columns including abbreviation and position-1..position-5, or None.
    """
    if not workbook_path.exists():
        return None
    try:
        df = pd.read_excel(
            workbook_path,
            sheet_name=MULTIPLE_POSITIONS_SHEET,
            engine="openpyxl",
            header=0,
        )
    except Exception:
        return None
    if df.empty:
        return None
    # Normalize column names to lowercase for lookup
    cols_lower = {str(c).strip(): str(c).strip() for c in df.columns}
    abbrev_col = None
    for k in cols_lower:
        if k.lower() == DP_ABBREVIATION_COL.lower():
            abbrev_col = cols_lower[k]
            break
    if abbrev_col is None:
        return None
    pos_cols = []
    for pc in DP_POSITION_COLS:
        for k in cols_lower:
            if k.lower() == pc.lower():
                pos_cols.append(cols_lower[k])
                break
    if not pos_cols:
        return None
    use_cols = [abbrev_col] + pos_cols
    return df[use_cols].copy()


def load_logo_ids_to_positions(workbook_path: Path) -> dict[str, str] | None:
    """
    Load Workbook 'Logo IDs to Positions' sheet if present.
    Returns logo_id_key -> position text dict, or None if sheet unavailable.
    """
    if not workbook_path.exists():
        return None
    try:
        df = pd.read_excel(
            workbook_path,
            sheet_name=LOGO_IDS_TO_POSITIONS_SHEET,
            engine="openpyxl",
            header=0,
        )
    except Exception:
        return None
    if df.empty:
        return None

    cols_lower = {str(c).strip(): str(c).strip() for c in df.columns}
    logo_col = None
    position_col = None
    for k in cols_lower:
        if k.lower() == LIP_LOGO_ID_COL.lower():
            logo_col = cols_lower[k]
        elif k.lower() == LIP_POSITION_COL.lower():
            position_col = cols_lower[k]
    if logo_col is None or position_col is None:
        return None

    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        logo_key = _normalize_logo_id_key(row.get(logo_col))
        position_val = _normalize_label(row.get(position_col))
        if not logo_key or not position_val:
            continue
        mapping[logo_key] = position_val  # last row wins for duplicates

    if not mapping:
        return None
    return mapping

