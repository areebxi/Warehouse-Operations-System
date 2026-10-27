"""Paper detection and slot targets for ISO A3–A6 rewrite."""
from __future__ import annotations

import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from rewrite_paper_sizes import paper_of, slot_kind, target_mm


def test_size_and_ga() -> None:
    assert paper_of({"Size": "A4", "Custom Label": "x", "Gender Apparel": ""}) == "A4"
    assert paper_of({"Size": "A5 15mm", "Custom Label": "A515", "Gender Apparel": ""}) == "A5"
    assert paper_of({"Size": "A5-Rectangle", "Custom Label": "x", "Gender Apparel": ""}) == "A5"
    assert paper_of({"Size": "", "Custom Label": "x", "Gender Apparel": "Photo Acrylic A6"}) == "A6"


def test_cl_token() -> None:
    assert paper_of({"Size": "", "Custom Label": "DTF-IronOn-A3", "Gender Apparel": ""}) == "A3"
    assert paper_of({"Size": "", "Custom Label": "ACLR-5mm-A6-POR-4C", "Gender Apparel": ""}) == "A6"
    # Leading design prefix — not paper unless confirmed.
    assert paper_of({"Size": "Large", "Custom Label": "A3-F/B-K-H-BLK-YXL-YES", "Gender Apparel": "Kids-Hoodie"}) is None
    assert paper_of({"Size": "S", "Custom Label": "A3-5000-NAT-S", "Gender Apparel": "Mens-T-Shirt"}) is None
    assert paper_of({"Size": "", "Custom Label": "A4-STCKR", "Gender Apparel": "Sticker"}) == "A4"


def test_slots() -> None:
    assert slot_kind("Front Center") == "body"
    assert slot_kind("Back Centre") == "body"
    assert slot_kind("Front Left Pocket") == "pocket"
    assert slot_kind("Right Sleeve") == "sleeve"
    assert slot_kind("Front Top Centre") is None
    assert target_mm("A4", "body") == ("210", "297")
    assert target_mm("A3", "body") == ("297", "420")
    assert target_mm("A5", "pocket") == ("80", "100")
    assert target_mm("A6", "sleeve") == ("100", "100")


if __name__ == "__main__":
    test_size_and_ga()
    test_cl_token()
    test_slots()
    print("ok")
