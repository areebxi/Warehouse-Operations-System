"""Nearest-band map for the locked hoodie chart."""
from __future__ import annotations

import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from rewrite_hoodie_sizes import band, is_body, is_kids


def test_kids_ages() -> None:
    assert band("3-4 Years", True) == (170, 170)
    assert band("YXS", True) == (170, 170)
    assert band("5-6 Years", True) == (190, 190)
    assert band("YS", True) == (190, 190)
    assert band("7-8 Years", True) == (210, 210)
    assert band("YM", True) == (210, 210)
    assert band("9-11 Years", True) == (230, 230)
    assert band("12-14 Years", True) == (250, 250)
    assert band("14-15 Years", True) == (250, 250)
    assert band("Y2XL", True) == (250, 250)


def test_adult_words() -> None:
    assert band("Extra Small", False) == (250, 250)
    assert band("S (8-10)", False) == (250, 250)
    assert band("Medium", False) == (270, 270)
    assert band("M (12-14)", False) == (270, 270)
    assert band("Extra Large", False) == (310, 310)
    assert band("2XL (22-24)", False) == (330, 330)
    assert band("5XL (34-36)", False) == (390, 390)
    assert band("6XL", False) is None


def test_kids_detect() -> None:
    assert is_kids("Kids-Hoodie", "Medium")
    assert is_kids("GILDAN Softstyle Midw Fleece Youth Hoodie", "Small")
    assert is_kids("SF500B-Hoodie", "12-14 Years")
    assert not is_kids("Mens-Hoodie", "Large")
    assert not is_kids("Uneek Eco Hoodie", "6XL")


def test_body_slots() -> None:
    assert is_body("Front Center")
    assert is_body("Back Center")
    assert not is_body("Front Left Pocket")
    assert not is_body("Sleeve")
    assert not is_body("Front Bottom Right Corner")


if __name__ == "__main__":
    test_kids_ages()
    test_adult_words()
    test_kids_detect()
    test_body_slots()
    print("ok")
