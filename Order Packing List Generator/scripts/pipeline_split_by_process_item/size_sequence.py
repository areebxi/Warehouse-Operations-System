from pathlib import Path

import pandas as pd

from .common import _normalize, _normalize_key, _resolve_workbook_path
from .config import COL_AD_INDEX, PROCESS_INFO_SHEET, SEQUENCE_BY_SIZE_HEADER


def load_sequence_by_size(workbook_path: Path) -> dict[str, int] | None:
    """
    Load Process Info Sheet, find 'Sequence by Size' column (by header or column AD).
    Return map: normalized size -> rank (0, 1, 2, ...). Sizes not in list get rank = len(sequence).
    Return None if workbook missing, sheet missing, or column not found (caller skips sort).
    """
    try:
        path = _resolve_workbook_path(workbook_path)
    except (FileNotFoundError, OSError):
        return None
    try:
        df = pd.read_excel(
            path,
            sheet_name=PROCESS_INFO_SHEET,
            engine="openpyxl",
            header=0,
        )
    except Exception:
        return None
    if df.empty:
        return None
    # Find column: 1) exact "Sequence by Size", 2) column AD (index 29), 3) header contains "size" + ("sequence" or "order")
    col_idx = None
    header_lower = _normalize_key(SEQUENCE_BY_SIZE_HEADER)
    for i, col in enumerate(df.columns):
        c = _normalize_key(str(col))
        if c == header_lower:
            col_idx = i
            break
    if col_idx is None and df.shape[1] > COL_AD_INDEX:
        col_idx = COL_AD_INDEX
    if col_idx is None:
        for i, col in enumerate(df.columns):
            c = _normalize_key(str(col))
            if "size" in c and ("sequence" in c or "order" in c):
                col_idx = i
                break
    if col_idx is None:
        return None
    size_to_rank: dict[str, int] = {}
    col_header = _normalize_key(str(df.columns[col_idx]))
    rank = 0
    for val in df.iloc[:, col_idx]:
        s = _normalize(val)
        if not s:
            continue
        key = _normalize_key(s)
        if key == col_header:
            continue
        if key not in size_to_rank:
            size_to_rank[key] = rank
            rank += 1
    return size_to_rank if size_to_rank else None

