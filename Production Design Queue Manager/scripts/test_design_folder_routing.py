"""ponytail: Customise folder gate must match Packing — no cross-fallback."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from src.core.design_folder_routing import find_designs_for_dtf_row, is_customise_yes


def test_is_customise_yes() -> None:
    assert is_customise_yes("Yes")
    assert is_customise_yes(" yes ")
    assert not is_customise_yes("")
    assert not is_customise_yes(None)
    assert not is_customise_yes("No")


def test_customise_yes_only_searches_personalised() -> None:
    fake = [{"sku": "x", "path": "p"}]
    with patch(
        "src.core.design_folder_routing.process_personalised_designs",
        return_value=fake,
    ) as personalised, patch(
        "src.core.design_folder_routing.process_single_designs",
        return_value=[{"sku": "should-not"}],
    ) as standard:
        items, source = find_designs_for_dtf_row(
            order_number="ORD1",
            item_sku="SKU1",
            customise="Yes",
            duplicate_index=0,
            is_duplicate_order=False,
            designs_folder="N",
            single_designs_folder="S",
            double_designs_folder="D",
            mm_to_pixel=1.0,
            canvas_width_mm=100,
            canvas_height_mm=100,
            design_padding=1,
            print_size_overrides=None,
        )
    assert source == "personalised"
    assert items == fake
    personalised.assert_called_once()
    standard.assert_not_called()


def test_customise_blank_only_searches_normal() -> None:
    fake = [{"sku": "n", "path": "p"}]
    with patch(
        "src.core.design_folder_routing.process_personalised_designs",
        return_value=[{"sku": "should-not"}],
    ) as personalised, patch(
        "src.core.design_folder_routing.process_single_designs",
        return_value=fake,
    ) as standard:
        items, source = find_designs_for_dtf_row(
            order_number="ORD1",
            item_sku="SKU1",
            customise="",
            duplicate_index=0,
            is_duplicate_order=False,
            designs_folder="N",
            single_designs_folder="S",
            double_designs_folder="D",
            mm_to_pixel=1.0,
            canvas_width_mm=100,
            canvas_height_mm=100,
            design_padding=1,
            print_size_overrides=None,
        )
    assert source == "standard"
    assert items == fake
    standard.assert_called_once()
    personalised.assert_not_called()


def main() -> None:
    test_is_customise_yes()
    test_customise_yes_only_searches_personalised()
    test_customise_blank_only_searches_normal()
    print("design_folder_routing ok")


if __name__ == "__main__":
    main()
