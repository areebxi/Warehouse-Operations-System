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


def test_unique_order_png_size_reference() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        single = os.path.join(tmp, "1-SP")
        double = os.path.join(tmp, "2-DP")
        os.makedirs(single)
        os.makedirs(double)
        png = _png(single, "12345.png", (200, 300))
        results = _personalised(
            single,
            double,
            order_number="12345",
            item_sku="77989LG-M-T-BLK-M",
            duplicate_index=0,
            is_duplicate_order=False,
            cl_entries=_entries(200, 300),
        )
        assert len(results) == 1
        assert results[0]["path"] == png
        assert results[0]["sku"] == "12345 (Single)"
        assert _near(results[0]["width_mm"], 200)
        assert _near(results[0]["height_mm"], 300)


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


def main() -> None:
    test_token_tables()
    test_unique_order_png_size_reference()
    test_legacy_pocket_sleeve_png_kids_65x80()
    test_duplicate_png_plus_p_jpeg_queues_png_only()
    test_duplicate_png_plus_s1_jpeg()
    test_apparel_size_s_in_sku_is_not_sleeve()
    test_jpeg_only_falls_through_to_double()
    test_double_folder_sku_png_unchanged()
    test_normal_mode_ignores_jpeg_hints()
    test_kids_sku_filename_p_hint_is_80x100_not_65x80()
    test_p_wins_over_later_tokens_and_index_zero_stem()
    test_slash_in_sku_becomes_hyphen()
    test_unique_order_ignores_sku_jpeg_hint()
    print("sku_position_hints ok")


if __name__ == "__main__":
    main()
