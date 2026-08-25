from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import pandas as pd


def find_pqr_columns_by_header_impl(df: pd.DataFrame) -> Optional[Tuple[int, int, int]]:
    cols = [str(c).strip().lower() for c in df.columns]
    p_idx = q_idx = r_idx = None
    for i, c in enumerate(cols):
        if "position" in c and ("combination" in c or "combinations" in c):
            if p_idx is None:
                p_idx = i
        if "code" in c and q_idx is None:
            q_idx = i
        if "draw" in c and r_idx is None:
            r_idx = i
    if p_idx is not None and q_idx is not None and r_idx is not None:
        if len({p_idx, q_idx, r_idx}) == 3:
            return p_idx, q_idx, r_idx
    return None


def load_position_code_to_draw_impl(
    workbook_path: Path,
    *,
    process_info_sheet: str,
    normalize_label: Callable[..., str],
    find_pqr_columns_by_header: Callable[[pd.DataFrame], Optional[Tuple[int, int, int]]],
) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not workbook_path.exists():
        return mapping

    df = pd.read_excel(
        workbook_path,
        sheet_name=process_info_sheet,
        engine="openpyxl",
        header=0,
    )

    if df.shape[1] >= 18:
        pqr_df = df.iloc[:, [15, 16, 17]].copy()
        pqr_df.columns = ["P", "Q", "Draw"]
    else:
        indices = find_pqr_columns_by_header(df)
        if indices is None:
            return mapping
        p_idx, q_idx, r_idx = indices
        pqr_df = df.iloc[:, [p_idx, q_idx, r_idx]].copy()
        pqr_df.columns = ["P", "Q", "Draw"]

    for _, row in pqr_df.iterrows():
        code_val = normalize_label(row["Q"])
        if not code_val:
            continue
        draw_raw = row.get("Draw", "")
        draw_str = "" if pd.isna(draw_raw) else str(draw_raw).strip()
        mapping[code_val] = draw_str

    return mapping


def lookup_draw_for_position_code(
    mapping: Dict[str, str] | None,
    position_code: str,
) -> str:
    """Case-insensitive Position Code -> Draw; returns '' if not found."""
    if not mapping:
        return ""
    code = "" if position_code is None else str(position_code).strip()
    if not code:
        return ""
    if code in mapping:
        return mapping[code]
    lower = code.lower()
    for key, value in mapping.items():
        if str(key).strip().lower() == lower:
            return value
    return ""
