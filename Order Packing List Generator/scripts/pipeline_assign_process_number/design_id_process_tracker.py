"""
Design ID Process Tracker — isolated Step 5 lookup for Separate by Logo ID.

Reads workbook sheet "Design ID Process Tracker" (columns Design ID, Process Number).
When over threshold, assigns the mapped Process Number instead of the raw Logo ID.

Set USE_TRACKER = False to disable this module and restore prior Step 5 logo behaviour
without changing other pipeline code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from .normalize import _normalize, _normalize_key, _normalize_process_start, _resolve_workbook_path
from .tracker_shift_offset import apply_shift_offset_to_tracker_map

SHEET_NAME = "Design ID Process Tracker"
USE_TRACKER = True


def _log(msg: str, log: Optional[Callable[[str], None]]) -> None:
    if log:
        log(msg)


def design_id_map_from_dataframe(df: pd.DataFrame) -> dict[str, str]:
    """Build Design ID -> Process Number map from columns Design ID and Process Number."""
    design_idx: int | None = None
    process_idx: int | None = None
    for i, col in enumerate(df.columns):
        c = _normalize_key(str(col))
        if c == "design id":
            design_idx = i
        elif c == "process number":
            process_idx = i
    if design_idx is None or process_idx is None:
        return {}
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        key = _normalize_key(row.iloc[design_idx])
        val = row.iloc[process_idx]
        if key and not pd.isna(val):
            out[key] = _normalize_process_start(val)
    return out


def load_tracker_map(
    workbook_path: Path,
    log: Optional[Callable[[str], None]] = None,
) -> dict[str, str]:
    """
    Load Design ID -> Process Number from workbook sheet Design ID Process Tracker.
    Returns {} if the sheet is missing, empty, or unreadable (does not raise).
    """
    try:
        path = _resolve_workbook_path(workbook_path)
    except (FileNotFoundError, OSError) as exc:
        _log(f"Design ID Process Tracker: workbook not available ({exc}); no logo lookups.", log)
        return {}

    try:
        df = pd.read_excel(path, sheet_name=SHEET_NAME, engine="openpyxl", header=0)
    except ValueError:
        _log(
            f"Design ID Process Tracker: sheet {SHEET_NAME!r} not found in workbook; no logo lookups.",
            log,
        )
        return {}
    except Exception as exc:
        _log(f"Design ID Process Tracker: failed to read sheet ({exc}); no logo lookups.", log)
        return {}

    if df.empty:
        _log(f"Design ID Process Tracker: sheet {SHEET_NAME!r} is empty; no logo lookups.", log)
        return {}

    out = design_id_map_from_dataframe(df)
    _log(f"Design ID Process Tracker: loaded {len(out)} Design ID -> Process Number mapping(s).", log)
    return out


def prepare_tracker_assign_kwargs(
    workbook_path: Path,
    separate_by_logo_id: bool,
    fixed_process_number: str | None,
    shift_input: str = "",
    log: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Build optional kwargs for assign_process_numbers when separate_by_logo_id is True.

    Logo ID only (no fixed process): over-threshold rows use Process Number only when
    listed in the tracker; otherwise they get the normal 6-part process number.

    Combined (fixed + separate by Logo ID): over-threshold rows use Process Number from the
    tracker when listed; otherwise they get the fixed process number (same batch as below-threshold rows).
    """
    if not separate_by_logo_id:
        return {}

    fixed = (fixed_process_number or "").strip()
    combined_with_fixed = bool(fixed)

    if not USE_TRACKER:
        _log("Design ID Process Tracker: USE_TRACKER is False; using legacy logo assignment.", log)
        if combined_with_fixed:
            return {
                "design_id_to_process_number": {},
                "logo_id_fallback_when_not_in_tracker": False,
            }
        return {}

    tracker_map = load_tracker_map(workbook_path, log=log)
    tracker_map = apply_shift_offset_to_tracker_map(tracker_map, shift_input, log=log)
    return {
        "design_id_to_process_number": tracker_map,
        "logo_id_fallback_when_not_in_tracker": False,
    }


__all__ = [
    "SHEET_NAME",
    "USE_TRACKER",
    "design_id_map_from_dataframe",
    "load_tracker_map",
    "prepare_tracker_assign_kwargs",
]
