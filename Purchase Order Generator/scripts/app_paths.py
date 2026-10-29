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
ASSETS_DIR = wh.shared_brand_logos_dir()
OUTPUT_DIR = wh.po_output_dir()
DONE_DIR = APP_ROOT / "00-Done"
_LEGACY_BRAND_LOGOS = wh.po_app_dir() / "assets" / "brand_logos"

PRODUCT_DATABASE_FILENAME = "Plain Database.csv"
SHIPSTATION_TAGS_FILENAME = "ShipStation Tags.xlsx"
PACKS_DATABASE_FILENAME = "Packs Database.csv"


def data_path(filename: str) -> Path:
    """Resolve shared catalogs or a file under this app's database/ folder."""
    if filename == "BTC_Product_Data.csv":
        return wh.btc_product_data_path()
    if filename in ("ShipStation Tags.xlsx", "ShipStation_Tags.xlsx"):
        return wh.shipstation_tags_path()
    if filename in (PRODUCT_DATABASE_FILENAME, "Plain Database.xlsx", "Plain Database.csv"):
        return wh.plain_database_path()
    if filename in (PACKS_DATABASE_FILENAME, "Packs Database.xlsx"):
        return wh.packs_database_path()
    in_data = DATA_DIR / filename
    if in_data.exists():
        return in_data
    return in_data


def product_database_path() -> Path:
    return wh.plain_database_path()


def shipstation_tags_path() -> Path:
    return wh.shipstation_tags_path()


def packs_database_path() -> Path:
    return wh.packs_database_path()


def product_database_archive_dir() -> Path:
    return wh.plain_database_archive_dir()


def brand_logos_dir() -> Path:
    """Shared brand logos; temporary fallback to legacy app assets/brand_logos."""
    shared = wh.shared_brand_logos_dir()
    try:
        if shared.is_dir() and any(shared.iterdir()):
            return shared
    except OSError:
        pass
    if _LEGACY_BRAND_LOGOS.is_dir():
        try:
            if any(_LEGACY_BRAND_LOGOS.iterdir()):
                return _LEGACY_BRAND_LOGOS
        except OSError:
            pass
    return shared


def asset_path(*parts: str) -> Path:
    """Resolve brand logos (shared) or other paths under the logos root."""
    if parts == ("brand_logos",) or (len(parts) == 1 and parts[0] == "brand_logos"):
        return brand_logos_dir()
    return brand_logos_dir().joinpath(*parts)


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
