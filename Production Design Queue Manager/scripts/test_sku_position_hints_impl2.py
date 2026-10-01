from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
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

def test_unique_order_ignores_sku_jpeg_hint() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, "12345.png", (200, 300))
        _jpg(single, f"12345-P-{SKU}.jpg")
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku=SKU,
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == "12345 (Single)"
        assert _near(results[0]["width_mm"], 200)
def test_apparel_size_s_in_sku_is_not_sleeve() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{APPAREL_S_SKU}.png", (200, 300))
        results = _personalised(
            single,
            double,
            item_sku=APPAREL_S_SKU,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single)"
        assert "Sleeve" not in results[0]["sku"]
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)
        assert resolve_sku_position_hint(ORDER, 1, APPAREL_S_SKU, single) == (None, False, False)
def test_kids_sku_filename_p_hint_is_80x100_not_65x80() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{KIDS_SKU}.png", (80, 100))
        _jpg(single, f"{ORDER}-1-P-{KIDS_SKU}.jpg")
        results = _personalised(
            single,
            double,
            item_sku=KIDS_SKU,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Pocket)"
        assert _near(results[0]["width_mm"], 80)
        assert _near(results[0]["height_mm"], 100)
        assert not _near(results[0]["width_mm"], 65)
def test_p_wins_over_later_tokens_and_index_zero_stem() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-{SKU}.png", (80, 100))
        _jpg(single, f"{ORDER}-S-{SKU}.jpg")
        _jpg(single, f"{ORDER}-P-{SKU}.jpg")
        _jpg(single, f"{ORDER}-S1-{SKU}.jpeg")
        token, is_pocket, is_sleeve = resolve_sku_position_hint(ORDER, 0, SKU, single)
        assert token == "P"
        assert is_pocket is True
        assert is_sleeve is False
        results = _personalised(single, double, duplicate_index=0)
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Pocket)"
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
def test_duplicate_png_plus_s1_jpeg() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{SKU}.png", (100, 100))
        jpg = _jpg(single, f"{ORDER}-1-S1-{SKU}.jpeg")
        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Sleeve-S1)"
        assert _near(results[0]["width_mm"], 100)
        assert _near(results[0]["height_mm"], 100)
        assert results[0]["path"] != jpg
def test_jpeg_only_falls_through_to_double() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        jpg = _jpg(single, f"{ORDER}-1-P-{SKU}.jpg")
        double_png = _png(double, f"{ORDER}-1-{SKU}.png", (120, 90), "yellow")
        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == double_png
        assert results[0]["design_type"] == "double"
        assert results[0]["sku"] == f"{ORDER} (Double)"
        assert results[0]["path"] != jpg
def test_double_folder_sku_png_unchanged() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        double_png = _png(double, f"{ORDER}-1-{SKU}.png", (150, 90), "yellow")
        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == double_png
        assert results[0]["design_type"] == "double"
        assert _near(results[0]["width_mm"], 150)
        assert _near(results[0]["height_mm"], 90)
def test_token_tables() -> None:
    assert POSITION_HINT_TOKENS == ("P", "S", "S1", "S2")
    assert POSITION_HINT_EXTENSIONS == (".jpg", ".jpeg")
    assert POSITION_HINT_MM["P"] == (80.0, 100.0)
    assert POSITION_HINT_MM["S"] == (100.0, 100.0)
    assert normalize_position_token("p") == "P"
    assert normalize_position_token("LOCATION") is None
    assert flags_for_position_token("P") == ("P", True, False)
    assert flags_for_position_token("S1") == ("S1", False, True)
    assert target_mm_for_position_token("P") == (80.0, 100.0)
    assert target_mm_for_position_token(None) is None
    assert IMAGE_EXTENSIONS == [".png"]
def _png(folder: str, name: str, size: tuple[int, int] = (80, 100), color: str = "red") -> str:
    path = os.path.join(folder, name)
    Image.new("RGB", size, color=color).save(path)
    return path
def _jpg(folder: str, name: str, size: tuple[int, int] = (40, 50), color: str = "blue") -> str:
    path = os.path.join(folder, name)
    Image.new("RGB", size, color=color).save(path, format="JPEG")
    return path
def _near(value: float, target: float, tol: float = 1.5) -> bool:
    return abs(value - target) <= tol
