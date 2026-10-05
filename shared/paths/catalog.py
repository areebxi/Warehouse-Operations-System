from __future__ import annotations

from pathlib import Path

from shared.paths.root import DB_SLUG_CL, database_app_dir, database_shared_dir, warehouse_root_from

def cl_app_dir(from_path: object | None = None) -> Path:
    """Custom Label Database app folder (scripts/docs only)."""
    return warehouse_root_from(from_path) / "Custom Label Database"


def cl_csv_path(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "custom_label" / "Custom_Label_Database.csv"


def backups_root(from_path: object | None = None) -> Path:
    """Repo-root folder for snapshots, old code copies, and doc archives."""
    return warehouse_root_from(from_path) / "backups"


def cl_backups_dir(from_path: object | None = None) -> Path:
    return backups_root(from_path) / "custom-label"


def btc_product_data_path(from_path: object | None = None) -> Path:
    """Shared BTC supplier catalog (same role as Uneek Product Data)."""
    return database_shared_dir(from_path) / "btc_product_data" / "BTC_Product_Data.csv"


def uneek_product_data_path(from_path: object | None = None) -> Path:
    """Shared Uneek supplier catalog (same role as BTC Product Data)."""
    return database_shared_dir(from_path) / "uneek_product_data" / "Uneek_Product_Data.xlsx"


def absolute_product_data_path(from_path: object | None = None) -> Path:
    """Shared Absolute Apparels supplier catalog (same role as BTC / Uneek Product Data)."""
    return database_shared_dir(from_path) / "absolute_product_data" / "Absolute_Product_Data.xlsx"


def shipstation_tags_path(from_path: object | None = None) -> Path:
    return database_shared_dir(from_path) / "shipstation_tags" / "ShipStation_Tags.xlsx"


def plain_database_path(from_path: object | None = None) -> Path:
    """Shared Plain Database (grouping + PO slips; not PO-app-owned)."""
    return database_shared_dir(from_path) / "plain" / "Plain Database.xlsx"


def plain_database_archive_dir(from_path: object | None = None) -> Path:
    return backups_root(from_path) / "plain"


def packs_database_path(from_path: object | None = None) -> Path:
    """Shared Packs Database (grouping + PO slips; not PO-app-owned)."""
    return database_shared_dir(from_path) / "packs" / "Packs Database.xlsx"


def packs_database_archive_dir(from_path: object | None = None) -> Path:
    return backups_root(from_path) / "packs"


def data_archive_dir(from_path: object | None = None) -> Path:
    return backups_root(from_path) / "shared"


def size_references_backups_dir(from_path: object | None = None) -> Path:
    return backups_root(from_path) / "size-references"


def database_transfer_backups_dir(from_path: object | None = None) -> Path:
    return backups_root(from_path) / "database-transfer"


def custom_label_support_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_CL, from_path) / "support"


def custom_label_database_dir(from_path: object | None = None) -> Path:
    """CL app-owned helpers (support/, Apparel Images/)."""
    return database_app_dir(DB_SLUG_CL, from_path)


def size_references_csv_path(from_path: object | None = None) -> Path:
    return custom_label_support_dir(from_path) / "Size References.csv"


def mocks_database_csv_path(from_path: object | None = None) -> Path:
    """CL support Mocks Database (print positions / printing type by Pasting Mocks ID)."""
    return custom_label_support_dir(from_path) / "Mocks Database.csv"


def database_transfer_dir(from_path: object | None = None) -> Path:
    """Supervisor upload mirrors of CL Database + Size References (not live)."""
    return warehouse_root_from(from_path) / "Database Transfer"


def database_transfer_workbook_path(from_path: object | None = None) -> Path:
    return database_transfer_dir(from_path) / "Workbook.xlsx"


def database_transfer_config_workbook_path(from_path: object | None = None) -> Path:
    return database_transfer_dir(from_path) / "Configuration Workbook.xlsx"

__all__ = [
    "cl_app_dir",
    "cl_csv_path",
    "backups_root",
    "cl_backups_dir",
    "btc_product_data_path",
    "uneek_product_data_path",
    "absolute_product_data_path",
    "shipstation_tags_path",
    "plain_database_path",
    "plain_database_archive_dir",
    "packs_database_path",
    "packs_database_archive_dir",
    "data_archive_dir",
    "size_references_backups_dir",
    "database_transfer_backups_dir",
    "custom_label_support_dir",
    "custom_label_database_dir",
    "size_references_csv_path",
    "mocks_database_csv_path",
    "database_transfer_dir",
    "database_transfer_workbook_path",
    "database_transfer_config_workbook_path",
]
