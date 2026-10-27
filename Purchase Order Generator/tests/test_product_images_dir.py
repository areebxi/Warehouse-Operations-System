"""Product Images folder is required via gui_settings — no assets fallback."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from run_script_gui_settings import (  # noqa: E402
    KEY_PRODUCT_IMAGES,
    product_images_dir_setting,
    required_product_images_dir,
)


def test_empty_settings_not_assets_fallback(tmp_path: Path) -> None:
    assert product_images_dir_setting({}) == ""
    assert required_product_images_dir({}) is None
    assert required_product_images_dir({KEY_PRODUCT_IMAGES: ""}) is None
    missing = tmp_path / "nope"
    assert required_product_images_dir({KEY_PRODUCT_IMAGES: str(missing)}) is None


def test_existing_dir_wins(tmp_path: Path) -> None:
    folder = tmp_path / "shots"
    folder.mkdir()
    got = required_product_images_dir({KEY_PRODUCT_IMAGES: str(folder)})
    assert got == folder
