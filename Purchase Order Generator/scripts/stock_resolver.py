"""
Custom Label → BTC SKU fallback when primary free_stock lookup fails.

Reads live Custom Label Database app CSV (Custom_Label_Database.csv).
Stock id column in that file is ``BTC SKU`` (mapped in code from former BTC Stock ID).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Callable

from app_paths import APP_ROOT

_WAREHOUSE_ROOT = APP_ROOT.parent
if str(_WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE_ROOT))

from shared.cl_sku_match import (  # noqa: E402
    default_cl_csv_path,
    normalize_label,
    resolve_from_map,
    resolve_label,
)

DEFAULT_CL_CSV = default_cl_csv_path(APP_ROOT)
# Legacy local copy (archive); default path is the CL app CSV.
LEGACY_LOCAL_CL_CSV = "Custom Label Database.csv"
STOCK_ID_COLUMNS = ("BTC SKU", "BTC Stock ID")

STATUS_NOT_IN_CUSTOM_LABEL_DB = "Not in Custom Label Database"
STATUS_CUSTOM_LABEL_MISSING_STOCK_ID = "Custom Label missing Stock ID"
STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS = "Stock ID not in stock levels"
STATUS_NOT_FOUND = "Not Found"

NOT_FOUND_STATUSES = frozenset(
    {
        STATUS_NOT_IN_CUSTOM_LABEL_DB,
        STATUS_CUSTOM_LABEL_MISSING_STOCK_ID,
        STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS,
        STATUS_NOT_FOUND,
    }
)


def _norm_label(value: str) -> str:
    return normalize_label(value)


def get_app_dir() -> Path:
    return APP_ROOT


def _default_cl_path() -> Path:
    if DEFAULT_CL_CSV.is_file():
        return DEFAULT_CL_CSV
    # Fallback to archived local copy if CL app path missing
    legacy = APP_ROOT / "data" / "archive" / LEGACY_LOCAL_CL_CSV
    if legacy.is_file():
        return legacy
    legacy2 = APP_ROOT / "data" / LEGACY_LOCAL_CL_CSV
    return legacy2


def load_custom_label_stock_map(
    path: Path | None = None,
    log: Callable[[str], None] = print,
) -> tuple[dict[str, str], set[str]]:
    """
    Load Custom_Label_Database.csv (or override path).

    Returns:
        mapping: Custom Label (casefold) → BTC SKU
        labels_missing_stock_id: labels present with blank BTC SKU
    """
    csv_path = Path(path) if path is not None else _default_cl_path()
    if not csv_path.exists():
        log(f"[WARNING] Custom Label Database not found at: {csv_path}")
        return {}, set()

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(csv_path, encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                mapping: dict[str, str] = {}
                empty_ids: set[str] = set()
                for row in reader:
                    label = (row.get("Custom Label") or "").strip()
                    stock_id = ""
                    for col in STOCK_ID_COLUMNS:
                        stock_id = (row.get(col) or "").strip()
                        if stock_id:
                            break
                    key = _norm_label(label)
                    if not key:
                        continue
                    if stock_id:
                        if key not in mapping:
                            mapping[key] = stock_id
                    else:
                        empty_ids.add(key)
                empty_ids -= set(mapping)
            log(
                f"[CUSTOM LABEL] Loaded {len(mapping)} label -> BTC SKU mappings from {csv_path}"
            )
            return mapping, empty_ids
        except UnicodeDecodeError:
            continue
        except OSError as e:
            log(f"[WARNING] Could not read Custom Label Database: {e}")
            return {}, set()

    log(f"[WARNING] Could not decode Custom Label Database: {csv_path}")
    return {}, set()


def not_found_status(
    original_sku: str,
    custom_label_map: dict[str, str],
    labels_missing_stock_id: set[str],
    *,
    used_fallback: bool,
) -> str:
    """
    Human-readable Status for stock_level == -1 issue rows.
    """
    if used_fallback:
        return STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS

    original = (original_sku or "").strip()
    if not original:
        return STATUS_NOT_FOUND

    matched = resolve_label(original, custom_label_map)
    if matched is not None:
        # Label matched but primary stock miss and fallback stock id also miss
        # (caller only uses this when level == -1).
        if matched in labels_missing_stock_id:
            return STATUS_CUSTOM_LABEL_MISSING_STOCK_ID
        return STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS

    # Any key strategy that hits labels_missing_stock_id
    from shared.cl_sku_match import match_keys

    for candidate in match_keys(original):
        key = candidate.casefold()
        if key in labels_missing_stock_id:
            return STATUS_CUSTOM_LABEL_MISSING_STOCK_ID

    if "-" not in original:
        return STATUS_NOT_FOUND
    return STATUS_NOT_IN_CUSTOM_LABEL_DB


def resolve_stock_level(
    original_sku: str,
    stock_levels: dict[str, int],
    custom_label_map: dict[str, str],
) -> tuple[int, str, str, bool]:
    """
    Resolve stock level and effective stock ID for a ShipStation SKU.

    1. Primary = text before first dash (or whole SKU) against BTC free_stock.
    2. Else universal CL match on Custom Label → BTC SKU → free_stock.
    """
    original = (original_sku or "").strip()
    if not original:
        return -1, "", "", False

    primary = original.split("-", 1)[0] if "-" in original else original
    level = stock_levels.get(primary, -1)
    effective = primary
    marketplace = ""
    used_fallback = False

    if level == -1:
        resolved = resolve_from_map(original, custom_label_map)
        if resolved:
            effective = resolved
            marketplace = original
            used_fallback = True
            level = stock_levels.get(resolved, -1)

    return level, effective, marketplace, used_fallback
