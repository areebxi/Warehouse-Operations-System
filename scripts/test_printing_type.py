"""ponytail: Printing Type lock — fails if DTF / mug-sublimation routing drifts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.printing_type import (
    DTF,
    SUBLIMATION,
    classify_cl_row,
    mock_id_from_label,
)


MOCKS = {"m260": DTF, "m61": SUBLIMATION, "m64": SUBLIMATION}


def test_mock_id_leading_m_digits_only() -> None:
    assert mock_id_from_label("M260-214332") == "M260"
    assert mock_id_from_label("M61-1D1") == "M61"
    assert mock_id_from_label("M-T-BLK-M") == ""
    assert mock_id_from_label("DTF-IronOn-A4") == ""
    assert mock_id_from_label("24LBL-A4-STCKR-45mm") == ""


def test_mock_printing_type_wins() -> None:
    assert (
        classify_cl_row(
            {"Custom Label": "M260-214332", "Gender Apparel": "FOTL Mens Valueweight T"},
            mock_types=MOCKS,
        )
        == DTF
    )
    assert (
        classify_cl_row(
            {"Custom Label": "M61-1D1", "Gender Apparel": "Mug-M61", "Category (Areeb)": "Mugs"},
            mock_types=MOCKS,
        )
        == SUBLIMATION
    )


def test_mugs_without_mock_are_sublimation() -> None:
    assert (
        classify_cl_row(
            {
                "Custom Label": "ATQ-B2c-C1-D4-E13",
                "Gender Apparel": "Mug",
                "Category (Areeb)": "Mugs",
            },
            mock_types=MOCKS,
        )
        == SUBLIMATION
    )


def test_everything_else_is_dtf() -> None:
    for row in (
        {"Custom Label": "M-T-BLK-M", "Gender Apparel": "Mens-T-Shirt", "Category (Areeb)": "T-SHIRTS"},
        {"Custom Label": "DTF-IronOn-A4", "Gender Apparel": "DTF-IronOn-A4", "Category (Areeb)": "Iron-On"},
        {"Custom Label": "24LBL-A4-STCKR-45mm", "Gender Apparel": "Sticker", "Category (Areeb)": "Stickers"},
        {"Custom Label": "BG-Chinabag-BLK-O/S", "Gender Apparel": "BG-China-Bag", "Category (Areeb)": "Bags"},
    ):
        assert classify_cl_row(row, mock_types=MOCKS) == DTF, row


def test_junk_mock_type_falls_through() -> None:
    assert (
        classify_cl_row(
            {"Custom Label": "M99-1", "Gender Apparel": "Mens-T-Shirt", "Category (Areeb)": "T-SHIRTS"},
            mock_types={"m99": "Asif - Laiba Awan"},
        )
        == DTF
    )


if __name__ == "__main__":
    test_mock_id_leading_m_digits_only()
    test_mock_printing_type_wins()
    test_mugs_without_mock_are_sublimation()
    test_everything_else_is_dtf()
    test_junk_mock_type_falls_through()
    print("ok")
