from __future__ import annotations

from pathlib import Path

from shared.paths.root import DB_SLUG_PACKING, database_app_dir, warehouse_root_from

def packing_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Order Packing List Generator"


def packing_data_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_PACKING, from_path)


def packing_workbook_path(from_path: object | None = None) -> Path:
    return packing_data_dir(from_path) / "Workbook.xlsx"


def packing_new_sku_csv_path(from_path: object | None = None) -> Path:
    return packing_data_dir(from_path) / "New SKU Database.csv"


def packing_all_orders_path(from_path: object | None = None) -> Path:
    return packing_data_dir(from_path) / "All Orders.csv"


def packing_runtime_dir(from_path: object | None = None) -> Path:
    """I/O lives at the packing app root (Input/, Output/, Logs/, …)."""
    return packing_app_dir(from_path)


def packing_input_dir(from_path: object | None = None) -> Path:
    return packing_runtime_dir(from_path) / "Input"


def packing_output_dir(from_path: object | None = None) -> Path:
    return packing_runtime_dir(from_path) / "Output"


def packing_logs_dir(from_path: object | None = None) -> Path:
    return packing_runtime_dir(from_path) / "Logs"


def packing_missing_input_dir(from_path: object | None = None) -> Path:
    return packing_runtime_dir(from_path) / "Missing Input"


def packing_missing_logo_dir(from_path: object | None = None) -> Path:
    return packing_runtime_dir(from_path) / "Missing Logo Files"


def packing_preflight_dir(from_path: object | None = None) -> Path:
    return packing_runtime_dir(from_path) / "Preflight Issues"


def packing_config_dir(from_path: object | None = None) -> Path:
    return packing_app_dir(from_path) / "config"


def packing_gui_config_path(from_path: object | None = None) -> Path:
    return packing_config_dir(from_path) / "gui_config.json"

__all__ = [
    "packing_app_dir",
    "packing_data_dir",
    "packing_workbook_path",
    "packing_new_sku_csv_path",
    "packing_all_orders_path",
    "packing_runtime_dir",
    "packing_input_dir",
    "packing_output_dir",
    "packing_logs_dir",
    "packing_missing_input_dir",
    "packing_missing_logo_dir",
    "packing_preflight_dir",
    "packing_config_dir",
    "packing_gui_config_path",
]
