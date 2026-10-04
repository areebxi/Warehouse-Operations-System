"""ponytail: Supplier Name lock — fails if Absolute babysuit / Uneek / BTC routing drifts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.supplier_name import (
    ABSOLUTE_APPARELS,
    BTC_ACTIVEWEAR,
    UNEEK_CLOTHING,
    classify_cl_row,
    classify_packs_row,
    classify_plain_row,
    is_absolute_babysuit,
)


class _Cat:
    def __init__(self) -> None:
        self.btc_by_uid = {"214332": {}, "214332".casefold(): {}}
        self.btc_by_spc = {"61082": {}, "61082".casefold(): {}}
        self.uneek_by_short = {"805YWSM": {}, "805ywsm": {}}
        self.uneek_by_code = {"U100": {}, "u100": {}}


CAT = _Cat()


def test_absolute_babysuit_tokens() -> None:
    assert is_absolute_babysuit("C800T-BS")
    assert is_absolute_babysuit("M281-P5-C800T-30-18-24")
    assert is_absolute_babysuit("C8030T-BS")
    assert is_absolute_babysuit("C8020T-36-0>3")
    assert not is_absolute_babysuit("BZ10-Body Suit")
    assert not is_absolute_babysuit("Uneek Padded Bodywarmer")
    assert not is_absolute_babysuit("GILDAN Heavy Cotton Adult T-Shirt")
    assert not is_absolute_babysuit("C800")


def test_cl_absolute_wins_over_btc_name() -> None:
    assert (
        classify_cl_row(
            {
                "Custom_Label": "M281-P5-C800T-30-18-24",
                "Gender_Apparel": "C800T-BS",
                "Supplier_SKU": "214332",
                "Supplier_Name": "BTC Activewear",
            },
            CAT,
        )
        == ABSOLUTE_APPARELS
    )
    assert (
        classify_cl_row(
            {"Custom_Label": "AS7-BBe-C1-D9-E1N", "Gender_Apparel": "C800T-BS"},
            CAT,
        )
        == ABSOLUTE_APPARELS
    )
    assert (
        classify_cl_row(
            {"Custom_Label": "AS8-1", "Gender_Apparel": "C8030T-BS"},
            CAT,
        )
        == ABSOLUTE_APPARELS
    )


def test_cl_in_house_blank() -> None:
    assert (
        classify_cl_row(
            {"Custom_Label": "24LBL-A4-STCKR-45mm", "Gender_Apparel": "Sticker"},
            CAT,
        )
        == ""
    )
    assert (
        classify_cl_row(
            {"Custom_Label": "DTF-IronOn-A4", "Gender_Apparel": "DTF-IronOn-A4"},
            CAT,
        )
        == ""
    )


def test_cl_btc_and_uneek() -> None:
    assert (
        classify_cl_row(
            {
                "Custom_Label": "M260-214332",
                "Gender_Apparel": "FOTL Mens Valueweight T",
                "Supplier_SKU": "214332",
            },
            CAT,
        )
        == BTC_ACTIVEWEAR
    )
    assert (
        classify_cl_row(
            {"Custom_Label": "805YWSM", "Gender_Apparel": "Uneek Ladies Shirt"},
            CAT,
        )
        == UNEEK_CLOTHING
    )


def test_plain_leftover_is_btc_not_absolute() -> None:
    assert (
        classify_plain_row(
            {"SKU": "212103", "Product Code": "TU01T", "Brand": "Bella"},
            CAT,
        )
        == BTC_ACTIVEWEAR
    )
    assert classify_plain_row({"SKU": "214332", "Product Code": ""}, CAT) == BTC_ACTIVEWEAR
    assert classify_plain_row({"SKU": "805YWSM", "Product Code": ""}, CAT) == UNEEK_CLOTHING


def test_packs_item1_btc() -> None:
    assert (
        classify_packs_row(
            {"Item 1 SKU": "214332", "Product Code": "", "Channel Child SKU": "SET1"},
            CAT,
        )
        == BTC_ACTIVEWEAR
    )


def test_bz10_body_suit_is_not_absolute() -> None:
    assert (
        classify_cl_row(
            {"Custom_Label": "BZ10-WHT-0-3", "Gender_Apparel": "BZ10-Body Suit"},
            CAT,
        )
        == BTC_ACTIVEWEAR
    )


if __name__ == "__main__":
    test_absolute_babysuit_tokens()
    test_cl_absolute_wins_over_btc_name()
    test_cl_in_house_blank()
    test_cl_btc_and_uneek()
    test_plain_leftover_is_btc_not_absolute()
    test_packs_item1_btc()
    test_bz10_body_suit_is_not_absolute()
    print("ok")
