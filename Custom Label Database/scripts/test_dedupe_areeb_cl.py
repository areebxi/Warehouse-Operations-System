"""Keep-rule and fix helpers for Areeb CL dedupe."""
from __future__ import annotations

import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from dedupe_areeb_cl_lib import (
    fix_kt_mens_youth,
    fix_lone_back,
    is_long_supplier_ga,
    is_short_ga,
    pick_winner,
    strength,
    token_score,
    youth_size,
)


def test_youth_and_ga_style() -> None:
    assert youth_size("K-T-RED-Y2XL-YES") == "14-15 Years"
    assert is_short_ga("Kids-T-Shirt")
    assert is_short_ga("Mens-Hoodie")
    assert not is_short_ga("FOTL Kids Valueweight T")
    assert is_long_supplier_ga("FOTL Kids Valueweight T")
    assert is_long_supplier_ga("GILDAN Softstyle Midw Fleece Youth Hoodie")
    assert not is_long_supplier_ga("Kids-Hoodie")


def test_token_prefers_kids_y2xl() -> None:
    cl = "K-T-RED-Y2XL-YES"
    mens = {"Gender Apparel": "Mens-T-Shirt", "Size": "Medium"}
    kids = {"Gender Apparel": "Kids-T-Shirt", "Size": "14-15 Years"}
    assert token_score(cl, kids) > token_score(cl, mens)
    win = pick_winner(cl, [(0, mens), (1, kids)])
    assert win[1] is kids


def test_supplier_ga_beats_short_when_tokens_tie() -> None:
    cl = "M260-P5-17098"
    short = {
        "Gender Apparel": "Kids-T-Shirt", "Size": "5-6 Years",
        "Colour": "x", "Apparel Image": "", "Print Positions": "",
        "Position 1 Name": "", "Width 1 (mm)": "", "Height 1 (mm)": "",
        "Supply Method": "Warehouse Stock", "Supplier Name": "",
        "BTC SKU": "", "Printing Type": "", "Category (Areeb)": "",
        "Product Type (Areeb)": "", "Brand": "",
    }
    long = dict(short)
    long["Gender Apparel"] = "FOTL Kids Valueweight T"
    assert strength(cl, long, 0) > strength(cl, short, 1)
    win = pick_winner(cl, [(0, short), (1, long)])
    assert win[1]["Gender Apparel"] == "FOTL Kids Valueweight T"


def test_kt_mens_fix_and_lone_back() -> None:
    rows = [
        {
            "Custom Label": "K-T-DSY-Y2XL",
            "Gender Apparel": "Mens-T-Shirt",
            "Size": "Small",
            "Colour": "Daisy",
        },
        {
            "Custom Label": "K-T-RED-Y2XL-YES",
            "Gender Apparel": "Kids-T-Shirt",
            "Size": "14-15 Years",
            "Colour": "Red",
            "BTC SKU": "138251",
            "Print Positions": "Front Center",
            "Position 1 Name": "Front Center",
            "Print Position Code": "F4",
            "Width 1 (mm)": "237",
            "Height 1 (mm)": "336",
        },
    ]
    log = fix_kt_mens_youth(rows)
    assert len(log) == 1
    assert rows[0]["Gender Apparel"] == "Kids-T-Shirt"
    assert rows[0]["Size"] == "14-15 Years"

    group = [
        {
            "Custom Label": "M260-P3-36488", "Colour": "Light Pink",
            "Print Positions": "Front Center", "Position 1 Name": "Front Center",
            "Print Position Code": "F4",
        },
        {
            "Custom Label": "M260-P3-36489", "Colour": "Light Pink",
            "Print Positions": "Front Center", "Position 1 Name": "Front Center",
            "Print Position Code": "F4",
        },
        {
            "Custom Label": "M260-P3-36490", "Colour": "Light Pink",
            "Print Positions": "Back Center", "Position 1 Name": "Back Center",
            "Print Position Code": "B4",
        },
    ]
    fixed = fix_lone_back(group)
    assert "M260-P3-36490" in fixed
    assert group[2]["Print Positions"] == "Front Center"
    assert group[2]["Print Position Code"] == "F4"


if __name__ == "__main__":
    test_youth_and_ga_style()
    test_token_prefers_kids_y2xl()
    test_supplier_ga_beats_short_when_tokens_tie()
    test_kt_mens_fix_and_lone_back()
    print("ok")
