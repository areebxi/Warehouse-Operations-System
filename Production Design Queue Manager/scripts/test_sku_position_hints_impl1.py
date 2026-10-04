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
from sku_position_hints_fixtures import FACTOR, ORDER, SKU, _entries, _jpg, _near, _personalised, _png

def test_legacy_pocket_sleeve_png_kids_65x80() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        pocket = _png(single, "12345-P.png", (65, 80))
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku="77989LG-K-T-BLK-M",
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == pocket
        assert results[0]["sku"] == "12345 (Single-Pocket)"
        assert _near(results[0]["width_mm"], 65)
        assert _near(results[0]["height_mm"], 80)

        os.remove(pocket)
        sleeve = _png(single, "12345-S.png", (100, 100), "green")
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku="77989LG-K-T-BLK-M",
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == sleeve
        assert results[0]["sku"] == "12345 (Single-Sleeve)"
        assert _near(results[0]["width_mm"], 100)
        assert _near(results[0]["height_mm"], 100)
def test_duplicate_png_plus_p_jpeg_queues_png_only() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, f"{ORDER}-1-{SKU}.png", (80, 100))
        jpg = _jpg(single, f"{ORDER}-1-P-{SKU}.jpg")
        path, design_type, is_pocket, is_sleeve = find_design_file_vba_logic(
            ORDER,
            1,
            single_designs_folder=single,
            double_designs_folder=double,
            folder_type="single",
            item_sku=SKU,
            is_duplicate_order=True,
        )
        assert path == png
        assert design_type == "single"
        assert is_pocket is False
        assert is_sleeve is False

        token, hinted_p, hinted_s = resolve_sku_position_hint(ORDER, 1, SKU, single)
        assert token == "P"
        assert hinted_p is True
        assert hinted_s is False
        companions = find_sku_position_variant_files(ORDER, 1, SKU, single)
        assert [c["token"] for c in companions] == ["P"]
        assert companions[0]["path"] == jpg

        results = _personalised(single, double)
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == f"{ORDER} (Single-Pocket)"
        assert _near(results[0]["width_mm"], 80)
        assert _near(results[0]["height_mm"], 100)
        assert all(r["path"] != jpg for r in results)
        assert all(not str(r["path"]).lower().endswith((".jpg", ".jpeg")) for r in results)
def test_normal_mode_ignores_jpeg_hints() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        designs = os.path.join(tmp, "normal")
        os.makedirs(designs)
        png = _png(designs, f"{SKU}.png", (200, 300))
        _jpg(designs, f"P-{SKU}.jpg")
        _jpg(designs, f"{ORDER}-P-{SKU}.jpg")
        with patch(
            "src.core.design_processing_single.get_cl_position_size_entries",
            return_value=_entries(200, 300),
        ):
            results = process_single_designs(
                SKU,
                designs,
                FACTOR,
                canvas_width_mm=None,
                canvas_height_mm=None,
                design_padding=0,
                cl_csv_path=Path("missing-cl-for-tests.csv"),
            )
        for item in results:
            image = item.get("image")
            if image is not None:
                image.close()
        assert len(results) == 1
        assert results[0]["path"] == png
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)
        assert all(not str(r["path"]).lower().endswith((".jpg", ".jpeg")) for r in results)
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
def test_unique_order_png_size_reference() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        sku = "77989LG-M-T-BLK-M"
        # Unique orders prefer {Order}-{SKU}.png first.
        png = _png(single, f"12345-{sku}.png", (200, 300))
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku=sku,
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == "12345 (Single)"
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)
def test_slash_in_sku_becomes_hyphen() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        os.makedirs(single)
        sku = "BG/BG140S"
        png = _png(single, f"{ORDER}-1-BG-BG140S.png", (80, 100))
        _jpg(single, f"{ORDER}-1-P-BG-BG140S.jpg")
        path, _, is_pocket, is_sleeve = find_design_file_vba_logic(
            ORDER,
            1,
            single_designs_folder=single,
            item_sku=sku,
            is_duplicate_order=True,
        )
        assert path == png
        assert is_pocket is False
        token, hinted_p, _ = resolve_sku_position_hint(ORDER, 1, sku, single)
        assert token == "P"
        assert hinted_p is True
