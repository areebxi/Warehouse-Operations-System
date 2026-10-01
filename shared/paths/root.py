"""Warehouse path registry — database/ live data + per-app code/I/O.

Shared databases: database/shared/ (CL, Tags, BTC/Uneek/Absolute Product Data,
Plain Database, Packs Database).
App databases: database/<app-slug>/.
Secrets: config/ShipStation. Pipeline I/O: runtime/SharedInbox + app Input/Output/Logs.
"""

from __future__ import annotations

from pathlib import Path

_WAREHOUSE_MARKERS = ("shared", "AGENTS.md")

# App slug folder names under database/
DB_SLUG_CL = "custom-label-database"
DB_SLUG_PACKING = "order-packing-list-generator"
DB_SLUG_QUEUE = "production-design-queue-manager"
DB_SLUG_PO = "purchase-order-generator"
DB_SLUG_SHIPPING = "shipping-label-generator"
DB_SLUG_SORTER = "order-grouping-sorter"

def warehouse_root_from(path: object | None = None) -> Path:
    """
    Walk up from path (or this file) until warehouse root is found.

    Root is a directory that contains ``shared/`` and ``database/``, ``data/``, or ``AGENTS.md``.
    """
    if path is None:
        start = Path(__file__).resolve().parent
    else:
        start = Path(path).resolve()
        if start.is_file():
            start = start.parent

    for candidate in (start, *start.parents):
        has_shared = (candidate / "shared").is_dir()
        has_database = (candidate / "database").is_dir()
        has_data = (candidate / "data").is_dir() or (candidate / "Data").is_dir()
        has_agents = (candidate / "AGENTS.md").is_file()
        if has_shared and (has_database or has_data or has_agents):
            return candidate
        if has_shared and (candidate / "Custom Label Database").is_dir():
            return candidate
    return start


def warehouse_root() -> Path:
    return warehouse_root_from(Path(__file__))


def database_root(from_path: object | None = None) -> Path:
    """All live database files (shared + per-app subfolders)."""
    return warehouse_root_from(from_path) / "database"


def database_shared_dir(from_path: object | None = None) -> Path:
    """Cross-app databases (PE, ShipStation tags, CL catalog)."""
    return database_root(from_path) / "shared"


def database_app_dir(slug: str, from_path: object | None = None) -> Path:
    """One app's database folder under database/."""
    return database_root(from_path) / slug


def data_root(from_path: object | None = None) -> Path:
    """Alias for database_shared_dir (replaces legacy warehouse data/)."""
    return database_shared_dir(from_path)


def runtime_root(from_path: object | None = None) -> Path:
    """Shared runtime only (SharedInbox)."""
    return warehouse_root_from(from_path) / "runtime"


def config_root(from_path: object | None = None) -> Path:
    """Shared config only (ShipStation secrets)."""
    return warehouse_root_from(from_path) / "config"

__all__ = [
    "DB_SLUG_CL",
    "DB_SLUG_PACKING",
    "DB_SLUG_QUEUE",
    "DB_SLUG_PO",
    "DB_SLUG_SHIPPING",
    "DB_SLUG_SORTER",
    "warehouse_root_from",
    "warehouse_root",
    "database_root",
    "database_shared_dir",
    "database_app_dir",
    "data_root",
    "runtime_root",
    "config_root",
]
