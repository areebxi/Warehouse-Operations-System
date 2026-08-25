"""
Project paths — single source of truth for data, assets, and output locations.
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


def _setup_import_paths() -> None:
    """Allow imports of config (app root) and app modules (scripts/)."""
    root = str(APP_ROOT)
    scripts = str(SCRIPTS_DIR)
    for entry in (root, scripts):
        if entry not in sys.path:
            sys.path.insert(0, entry)


APP_ROOT = get_app_root()
SCRIPTS_DIR = APP_ROOT / "scripts"
_setup_import_paths()
DATA_DIR = APP_ROOT / "data"
ASSETS_DIR = APP_ROOT / "assets"
OUTPUT_DIR = APP_ROOT / "output"
DONE_DIR = APP_ROOT / "00-Done"


def data_path(filename: str) -> Path:
    """Resolve a file in data/, with fallback to app root for legacy layouts."""
    in_data = DATA_DIR / filename
    if in_data.exists():
        return in_data
    legacy = APP_ROOT / filename
    if legacy.exists():
        return legacy
    return in_data


PRODUCT_DATABASE_FILENAME = "Database.xlsx"
_LEGACY_PRODUCT_DATABASE_FILENAME = "database.xlsx"

SHIPSTATION_TAGS_FILENAME = "ShipStation Tags.xlsx"
_LEGACY_SHIPSTATION_TAGS_FILENAME = "ShipStation_Tags.xlsx"

PACKS_DATABASE_FILENAME = "Packs Database.xlsx"
_LEGACY_PACKS_DATABASE_FILENAME = "01-Packs Database.xlsx"


def _first_existing_data_file(*filenames: str) -> Path:
    for name in filenames:
        path = data_path(name)
        if path.exists():
            return path
    return data_path(filenames[0])


def product_database_path() -> Path:
    """Product database for packing slips (SKU = BTC stock id). Prefers Database.xlsx."""
    return _first_existing_data_file(
        PRODUCT_DATABASE_FILENAME, _LEGACY_PRODUCT_DATABASE_FILENAME
    )


def shipstation_tags_path() -> Path:
    """ShipStation tag ID / process-no workbook. Prefers ShipStation Tags.xlsx."""
    return _first_existing_data_file(
        SHIPSTATION_TAGS_FILENAME, _LEGACY_SHIPSTATION_TAGS_FILENAME
    )


def packs_database_path() -> Path:
    """Packs component workbook. Prefers Packs Database.xlsx."""
    return _first_existing_data_file(
        PACKS_DATABASE_FILENAME, _LEGACY_PACKS_DATABASE_FILENAME
    )


def asset_path(*parts: str) -> Path:
    """Resolve a path under assets/, with fallback to app root."""
    in_assets = ASSETS_DIR.joinpath(*parts)
    if in_assets.exists():
        return in_assets
    legacy = APP_ROOT.joinpath(*parts)
    if legacy.exists():
        return legacy
    return in_assets


def output_date_dir(*, date: str | None = None) -> Path:
    """Today's output folder: output/{YYYY-MM-DD}/."""
    from datetime import datetime

    date_part = date or datetime.now().strftime("%Y-%m-%d")
    path = OUTPUT_DIR / date_part
    path.mkdir(parents=True, exist_ok=True)
    return path


def tag_output_dir(folder_name: str) -> Path:
    """Subfolder under output/{date}/ for a run or artifact group."""
    path = output_date_dir() / folder_name
    path.mkdir(parents=True, exist_ok=True)
    return path
