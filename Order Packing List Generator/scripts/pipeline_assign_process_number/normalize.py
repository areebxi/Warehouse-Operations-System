import re
from datetime import date
from pathlib import Path

import pandas as pd


def _normalize(val) -> str:
    """Strip and return string; empty if NaN/blank."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def _normalize_process_start(val) -> str:
    """
    Normalize process-start values from workbook:
    - whole-number numerics become integer text (100.0 -> "100")
    - other values keep their trimmed string form.
    """
    s = _normalize(val)
    if not s:
        return ""
    try:
        num = float(s)
    except (TypeError, ValueError):
        return s
    if num.is_integer():
        return str(int(num))
    return s


def _normalize_key(val) -> str:
    """Strip and lowercase for lookup."""
    return _normalize(val).lower()


def _prime_is_yes(val) -> bool:
    """True if Prime is 'Yes' (case-insensitive, trimmed)."""
    return _normalize_key(val) == "yes"


def _customise_is_yes(val) -> bool:
    """True if Customise is 'Yes' (case-insensitive, trimmed)."""
    return _normalize_key(val) == "yes"


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
    return None


def _resolve_workbook_path(workbook_path: Path) -> Path:
    """Return workbook path; must be Workbook.xlsx."""
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    return workbook_path

