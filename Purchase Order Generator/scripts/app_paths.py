"""
Project paths — thin wrapper over warehouse shared.paths.
Supports running from source (python scripts/run_script_gui.py) or a frozen executable.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    here = Path(__file__).resolve().parent
    if here.name == "scripts":
        return here.parent
    return here


def _ensure_warehouse_on_path() -> None:
    root = get_app_root().parent
    shared = root / "shared"
    if shared.is_dir() and str(root) not in sys.path:
        sys.path.insert(0, str(root))


_ensure_warehouse_on_path()

from shared import paths as wh  # noqa: E402


def _setup_import_paths() -> None:
    """Allow imports of config (Config/purchase_order) and app modules (scripts/)."""
    root = str(APP_ROOT)
    scripts = str(SCRIPTS_DIR)
    cfg = str(wh.po_config_dir())
    for entry in (cfg, root, scripts):
        if entry not in sys.path:
            sys.path.insert(0, entry)


APP_ROOT = get_app_root()
SCRIPTS_DIR = APP_ROOT / "scripts"
_setup_import_paths()

DATA_DIR = wh.po_data_dir()
ASSETS_DIR = wh.images_po_dir()
OUTPUT_DIR = wh.po_output_dir()
DONE_DIR = APP_ROOT / "00-Done"


def data_path(filename: str) -> Path:
    """Resolve a file under Data/PurchaseOrder (or shared ProductExport / Tags)."""
    if filename in ("ProductExport.csv", "ProductExport.xlsx"):
        return wh.product_export_path() if filename.endswith(".csv") else wh.data_archive_dir() / "PO_ProductExport.xlsx"
    if filename in ("ShipStation Tags.xlsx", "ShipStation_Tags.xlsx"):
        return wh.shipstation_tags_path()
    in_data = DATA_DIR / filename
    if in_data.exists():
        return in_data
    return in_data


PRODUCT_DATABASE_FILENAME = "Database.xlsx"
SHIPSTATION_TAGS_FILENAME = "ShipStation Tags.xlsx"
PACKS_DATABASE_FILENAME = "Packs Database.xlsx"


def product_database_path() -> Path:
    return wh.po_database_path()


def shipstation_tags_path() -> Path:
    return wh.shipstation_tags_path()


def packs_database_path() -> Path:
    return wh.po_packs_database_path()


def asset_path(*parts: str) -> Path:
    """Resolve under Data/Images/PurchaseOrder/."""
    in_assets = ASSETS_DIR.joinpath(*parts)
    if in_assets.exists():
        return in_assets
    return in_assets


def output_date_dir(*, date: str | None = None) -> Path:
    from datetime import datetime

    date_part = date or datetime.now().strftime("%Y-%m-%d")
    path = OUTPUT_DIR / date_part
    path.mkdir(parents=True, exist_ok=True)
    return path


def tag_output_dir(folder_name: str) -> Path:
    path = output_date_dir() / folder_name
    path.mkdir(parents=True, exist_ok=True)
    return path
