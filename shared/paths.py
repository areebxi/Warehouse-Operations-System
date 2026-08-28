"""
Warehouse path registry — database/ live data + per-app code/I/O.

Shared databases: database/shared/ (PE, Tags, CL CSV).
App databases: database/<app-slug>/.
Secrets: config/ShipStation. Pipeline I/O: runtime/SharedInbox + app Input/Output/Logs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

_WAREHOUSE_MARKERS = ("shared", "AGENTS.md")

# App slug folder names under database/
DB_SLUG_CL = "custom-label-database"
DB_SLUG_PACKING = "order-packing-list-generator"
DB_SLUG_QUEUE = "production-design-queue-manager"
DB_SLUG_PO = "purchase-order-generator"
DB_SLUG_SHIPPING = "shipping-label-generator"


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


# --- Catalog / shared tabular ---


def cl_app_dir(from_path: object | None = None) -> Path:
    """Custom Label Database app folder (scripts/docs only)."""
    return warehouse_root_from(from_path) / "Custom Label Database"


def cl_csv_path(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "custom_label" / "Custom_Label_Database.csv"


def cl_backups_dir(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "custom_label" / "backups"


def product_export_path(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "product_export" / "ProductExport.csv"


def shipstation_tags_path(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "shipstation" / "ShipStation_Tags.xlsx"


def data_archive_dir(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "archive"


def custom_label_support_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_CL, from_path) / "support"


def custom_label_database_dir(from_path: object | None = None) -> Path:
    """CL app-owned helpers (support/, Apparel Images/)."""
    return database_app_dir(DB_SLUG_CL, from_path)


# --- Packing (Order Packing List Generator) ---


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


# --- Queue (Production Design Queue Manager) ---


def queue_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Production Design Queue Manager"


def queue_database_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_QUEUE, from_path)


def queue_data_dir(from_path: object | None = None) -> Path:
    """Alias for queue_database_dir (workbook lives here)."""
    return queue_database_dir(from_path)


def queue_config_workbook_path(from_path: object | None = None) -> Path:
    return queue_database_dir(from_path) / "Configuration Workbook.xlsx"


def queue_runtime_dir(from_path: object | None = None) -> Path:
    return queue_app_dir(from_path)


def queue_input_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Input"


def queue_output_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Output"


def queue_logs_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Logs"


def queue_missing_size_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Missing Size Reference"


def queue_config_dir(from_path: object | None = None) -> Path:
    return queue_app_dir(from_path) / "config"


def queue_settings_path(from_path: object | None = None) -> Path:
    return queue_config_dir(from_path) / "queue_app_settings.json"


# --- Purchase Order Generator ---


def po_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Purchase Order Generator"


def po_data_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_PO, from_path)


def po_database_path(from_path: object | None = None) -> Path:
    return po_data_dir(from_path) / "Database.xlsx"


def po_packs_database_path(from_path: object | None = None) -> Path:
    return po_data_dir(from_path) / "Packs Database.xlsx"


def po_stock_csv_path(
    from_path: object | None = None,
    *,
    filename: str = "stock_levels_stock_id_fully_quoted.csv",
) -> Path:
    return po_data_dir(from_path) / filename


def po_runtime_dir(from_path: object | None = None) -> Path:
    return po_app_dir(from_path)


def po_output_dir(from_path: object | None = None) -> Path:
    return po_runtime_dir(from_path) / "output"


def po_config_dir(from_path: object | None = None) -> Path:
    """``config.py`` and GUI settings live at the PO app root config/."""
    return po_app_dir(from_path)


def po_config_py_path(from_path: object | None = None) -> Path:
    return po_config_dir(from_path) / "config.py"


def po_gui_settings_path(from_path: object | None = None) -> Path:
    return po_app_dir(from_path) / "config" / "gui_settings.json"


# --- Shipping Label Generator ---


def shipping_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Shipping Label Generator"


def shipping_database_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_SHIPPING, from_path)


def shipping_runtime_dir(from_path: object | None = None) -> Path:
    return shipping_app_dir(from_path)


def shipping_desfiles_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "DTF Des Files"


def shipping_desfiles_processed_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "DTF Des Files - Processed"


def shipping_output_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Output"


def shipping_logs_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Logs"


def shipping_reports_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Reports"


def shipping_manual_print_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Manual Print Input"


def shipping_void_input_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Void Label Input"


def shipping_errors_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Error and Failures"


def shipping_config_dir(from_path: object | None = None) -> Path:
    return shipping_app_dir(from_path)


def shipping_env_path(from_path: object | None = None) -> Path:
    return shipping_config_dir(from_path) / ".env"


def shipping_yaml_path(from_path: object | None = None) -> Path:
    return shipping_config_dir(from_path) / "shipping_config.yaml"


# --- ShipStation (shared credentials) ---


def shipstation_config_dir(from_path: object | None = None) -> Path:
    return config_root(from_path) / "ShipStation"


def shipstation_env_path(from_path: object | None = None) -> Path:
    """Warehouse ShipStation secrets file (REAL_API_*)."""
    return shipstation_config_dir(from_path) / ".env"


# --- Shared Inbox / images ---


def shared_inbox_dtf_des_root(from_path: object | None = None) -> Path:
    return runtime_root(from_path) / "SharedInbox" / "DTF Des"


def images_apparel_dir(from_path: object | None = None) -> Path:
    return custom_label_database_dir(from_path) / "Apparel Images"


def images_po_dir(from_path: object | None = None) -> Path:
    return po_app_dir(from_path) / "assets"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
