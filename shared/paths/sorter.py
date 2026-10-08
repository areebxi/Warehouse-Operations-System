from __future__ import annotations

from pathlib import Path

from shared.paths.packing import packing_input_dir
from shared.paths.root import DB_SLUG_SORTER, database_app_dir, warehouse_root_from

def sorter_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Order Grouping Sorter"


def sorter_data_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_SORTER, from_path)


def sorter_taxonomy_picklists_path(from_path: object | None = None) -> Path:
    """Closed category / subcategory / product type / product style lists (Hashim #038)."""
    return sorter_data_dir(from_path) / "taxonomy_picklists.csv"


def sorter_fixed_batches_path(from_path: object | None = None) -> Path:
    """Fixed batch codes + match criteria (B80 / B100 / …). Source for sorter naming."""
    return sorter_data_dir(from_path) / "fixed_batches.csv"


def sorter_leftover_batches_dir(from_path: object | None = None) -> Path:
    """Per-date leftover B1/B2… criteria CSVs (same columns as fixed_batches.csv)."""
    return sorter_data_dir(from_path) / "leftover_batches"


def sorter_catalog_cache_dir(from_path: object | None = None) -> Path:
    """Pickled Plain/Packs indexes; rebuild when source xlsx mtime/size changes."""
    return sorter_data_dir(from_path) / "catalog_cache"


def sorter_catalog_cache_path(
    stem: str,
    *,
    from_path: object | None = None,
) -> Path:
    """One pickle per catalog stem, e.g. plain.pkl / packs.pkl."""
    return sorter_catalog_cache_dir(from_path) / f"{stem}.pkl"


def sorter_leftover_batches_path(
    run_date: object,
    *,
    from_path: object | None = None,
) -> Path:
    """One leftover-batches CSV per run date: leftover_batches/{YYYY-MM-DD}.csv."""
    if hasattr(run_date, "isoformat"):
        stamp = run_date.isoformat()  # date / datetime
    else:
        stamp = str(run_date)
    return sorter_leftover_batches_dir(from_path) / f"{stamp}.csv"


def sorter_logs_dir(from_path: object | None = None) -> Path:
    return sorter_app_dir(from_path) / "Logs"


def sorter_input_csv_path(
    date_dd_mm_yyyy: str,
    shift_folder: str,
    process_name: str,
    *,
    from_path: object | None = None,
) -> Path:
    """Packing Input/{DD-MM-YYYY}/{shift folder}/{process}.csv — write only after run."""
    return packing_input_dir(from_path) / date_dd_mm_yyyy / shift_folder / f"{process_name}.csv"

__all__ = [
    "sorter_app_dir",
    "sorter_data_dir",
    "sorter_taxonomy_picklists_path",
    "sorter_fixed_batches_path",
    "sorter_leftover_batches_dir",
    "sorter_leftover_batches_path",
    "sorter_catalog_cache_dir",
    "sorter_catalog_cache_path",
    "sorter_logs_dir",
    "sorter_input_csv_path",
]
