"""ponytail: 1-SP JPEG is a hint — PNG queued, JPEG never placed."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from src.core.design_processing_personalised import process_personalised_designs
from src.core.design_processing_single import process_single_designs
from src.core.sku_position_hints import (
    POSITION_HINT_EXTENSIONS,
    POSITION_HINT_MM,
    POSITION_HINT_TOKENS,
    flags_for_position_token,
    normalize_position_token,
    target_mm_for_position_token,
)
from src.io.file_handlers import (
    find_design_file_vba_logic,
    find_sku_position_variant_files,
    resolve_sku_position_hint,
)
from src.io.file_utilities import IMAGE_EXTENSIONS

ORDER = "204-6115657-9842723"
SKU = "189397LG-M-T-BLK-4XL-YES"
KIDS_SKU = "189397LG-K-T-BLK-M-YES"
APPAREL_S_SKU = "189397LG-M-T-BLK-S-YES"
FACTOR = 1.0


def _png(folder: str, name: str, size: tuple[int, int] = (80, 100), color: str = "red") -> str:
    path = os.path.join(folder, name)
    Image.new("RGB", size, color=color).save(path)
    return path


def _jpg(folder: str, name: str, size: tuple[int, int] = (40, 50), color: str = "blue") -> str:
    path = os.path.join(folder, name)
    Image.new("RGB", size, color=color).save(path, format="JPEG")
    return path


def _entries(width: float = 200.0, height: float = 300.0, match: str = "cl-csv"):
    return [
        {
            "position": None,
            "size_info": {
                "width_px": int(width),
                "height_px": int(height),
                "width_mm": width,
                "height_mm": height,
                "size_code": "TEST",
                "match_type": match,
                "merge_entry": "TEST",
            },
        }
    ]


def _personalised(single: str, double: str, **kwargs):
    defaults = {
        "order_number": ORDER,
        "item_sku": SKU,
        "duplicate_index": 1,
        "is_duplicate_order": True,
        "single_designs_folder": single,
        "double_designs_folder": double,
        "mm_to_pixel_factor": FACTOR,
        "canvas_width_mm": None,
        "canvas_height_mm": None,
        "design_padding": 0,
        "cl_csv_path": Path("missing-cl-for-tests.csv"),
    }
    defaults.update(kwargs)
    with patch(
        "src.core.design_processing_personalised.get_cl_position_size_entries",
        return_value=defaults.pop("cl_entries", None),
    ):
        results = process_personalised_designs(**defaults)
    for item in results:
        image = item.get("image")
        if image is not None:
            image.close()
    return results


def _near(value: float, target: float, tol: float = 1.5) -> bool:
    return abs(value - target) <= tol

__all__ = [
    "Path",
    "process_personalised_designs",
    "ORDER",
    "SKU",
    "KIDS_SKU",
    "APPAREL_S_SKU",
    "FACTOR",
    "_png",
    "_jpg",
    "_entries",
    "_personalised",
    "_near",
    "tempfile",
    "os",
    "patch",
    "process_single_designs",
    "find_design_file_vba_logic",
    "find_sku_position_variant_files",
    "resolve_sku_position_hint",
    "POSITION_HINT_EXTENSIONS",
    "POSITION_HINT_MM",
    "POSITION_HINT_TOKENS",
    "flags_for_position_token",
    "normalize_position_token",
    "target_mm_for_position_token",
    "IMAGE_EXTENSIONS",
]
