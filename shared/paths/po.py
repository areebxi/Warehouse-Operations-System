from __future__ import annotations

from pathlib import Path

from shared.paths.catalog import packs_database_path, plain_database_path
from shared.paths.root import (
    APP_NAME_PO,
    DB_SLUG_PO,
    app_output_dir,
    database_app_dir,
    warehouse_root_from,
)

def po_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / APP_NAME_PO


def po_data_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_PO, from_path)


def po_database_path(from_path: object | None = None) -> Path:
    """Alias for plain_database_path (legacy PO name)."""
    return plain_database_path(from_path)


def po_packs_database_path(from_path: object | None = None) -> Path:
    """Alias for packs_database_path (legacy PO name)."""
    return packs_database_path(from_path)


def po_stock_csv_path(
    from_path: object | None = None,
    *,
    filename: str = "stock_levels_stock_id_fully_quoted.csv",
) -> Path:
    return po_data_dir(from_path) / filename


def po_runtime_dir(from_path: object | None = None) -> Path:
    return po_app_dir(from_path)


def po_output_dir(from_path: object | None = None) -> Path:
    return app_output_dir(APP_NAME_PO, from_path)


def po_config_dir(from_path: object | None = None) -> Path:
    """``config.py`` and GUI settings live under ``database/purchase-order-generator/``."""
    return po_data_dir(from_path)


def po_config_py_path(from_path: object | None = None) -> Path:
    return po_config_dir(from_path) / "config.py"


def po_gui_settings_path(from_path: object | None = None) -> Path:
    return po_data_dir(from_path) / "gui_settings.json"

__all__ = [
    "po_app_dir",
    "po_data_dir",
    "po_database_path",
    "po_packs_database_path",
    "po_stock_csv_path",
    "po_runtime_dir",
    "po_output_dir",
    "po_config_dir",
    "po_config_py_path",
    "po_gui_settings_path",
]
