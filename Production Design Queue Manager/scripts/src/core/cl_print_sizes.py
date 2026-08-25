"""
Print sizes from live Custom_Label_Database.csv (Queue option B).

Match Item SKU → Custom Label (universal matcher), then Width/Height mm slots.
Pocket / Override Print Size stays in Configuration Workbook (callers apply separately).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

_QUEUE_APP_ROOT = Path(__file__).resolve().parents[3]
_WAREHOUSE_ROOT = _QUEUE_APP_ROOT.parent
if str(_WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE_ROOT))

from shared.cl_sku_match import (  # noqa: E402
    default_cl_csv_path,
    normalize_label,
    resolve_label,
)
from src.core.size_reference import _build_size_result  # noqa: E402

_CL_INDEX: Optional[dict[str, int]] = None
_CL_DF: Optional[pd.DataFrame] = None
_CL_PATH: Optional[Path] = None


def _queue_app_root() -> Path:
    return _QUEUE_APP_ROOT


def clear_cl_size_cache() -> None:
    global _CL_INDEX, _CL_DF, _CL_PATH
    _CL_INDEX = None
    _CL_DF = None
    _CL_PATH = None


def load_cl_size_table(cl_csv_path: Optional[Path] = None) -> pd.DataFrame:
    global _CL_INDEX, _CL_DF, _CL_PATH
    path = Path(cl_csv_path) if cl_csv_path is not None else default_cl_csv_path(_queue_app_root())
    if _CL_DF is not None and _CL_PATH == path:
        return _CL_DF
    if not path.is_file():
        raise FileNotFoundError(f"CL CSV not found: {path}")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if "Custom Label" not in df.columns:
        raise ValueError(f"CL CSV missing Custom Label: {path}")
    index: dict[str, int] = {}
    for i, label in enumerate(df["Custom Label"].tolist()):
        key = normalize_label(label)
        if key and key not in index:
            index[key] = i
    _CL_DF = df
    _CL_INDEX = index
    _CL_PATH = path
    return df


def _parse_mm(value: Any) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _slots_from_row(row: pd.Series) -> List[tuple[Optional[str], float, float]]:
    slots: List[tuple[Optional[str], float, float]] = []
    for n in range(1, 5):
        w = _parse_mm(row.get(f"Width {n} (mm)"))
        h = _parse_mm(row.get(f"Height {n} (mm)"))
        if w is None or h is None:
            continue
        name = row.get(f"Position {n} Name")
        name_s = str(name).strip() if name is not None and str(name).strip() not in ("", "nan") else None
        slots.append((name_s, w, h))
    return slots


def resolve_cl_row(item_sku: Union[str, pd.Series], cl_csv_path: Optional[Path] = None) -> Optional[pd.Series]:
    load_cl_size_table(cl_csv_path)
    assert _CL_INDEX is not None and _CL_DF is not None
    sku = item_sku.iloc[0] if isinstance(item_sku, pd.Series) else item_sku
    key = resolve_label(sku, _CL_INDEX)
    if key is None:
        return None
    return _CL_DF.iloc[_CL_INDEX[key]]


def get_cl_position_size_entries(
    item_sku: Union[str, pd.Series],
    mm_to_pixel_factor: float,
    *,
    position_hint: Optional[str] = None,
    force_single: bool = False,
    cl_csv_path: Optional[Path] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Return position/size entries from CL CSV, or None if SKU does not match.

    Empty list is not used — None means fall through / missing; a list always
    has at least one entry (size_info may be None if dims blank).
    """
    try:
        row = resolve_cl_row(item_sku, cl_csv_path=cl_csv_path)
    except FileNotFoundError:
        return None
    if row is None:
        return None

    sku_str = str(item_sku.iloc[0] if isinstance(item_sku, pd.Series) else item_sku).strip()
    slots = _slots_from_row(row)
    if not slots:
        return [{"position": None, "size_info": None}]

    if position_hint:
        hint = position_hint.strip().casefold()
        for name, w, h in slots:
            if name and name.casefold() == hint:
                info = _build_size_result(
                    w, h, mm_to_pixel_factor, sku_str, name or sku_str, "cl-csv",
                    f"Width (mm)", f"Height (mm)",
                )
                return [{"position": name, "size_info": info}]

    if force_single or len(slots) == 1:
        name, w, h = slots[0]
        info = _build_size_result(
            w, h, mm_to_pixel_factor, sku_str, name or sku_str, "cl-csv",
            "Width (mm)", "Height (mm)",
        )
        return [{"position": None, "size_info": info}]

    entries: List[Dict[str, Any]] = []
    for name, w, h in slots:
        info = _build_size_result(
            w, h, mm_to_pixel_factor, sku_str, name or sku_str, "cl-csv",
            "Width (mm)", "Height (mm)",
        )
        entries.append({"position": name, "size_info": info})
    return entries
