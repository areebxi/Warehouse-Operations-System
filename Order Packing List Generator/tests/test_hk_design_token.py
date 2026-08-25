"""Tests for HK design-token recognition in steps 3 and 7."""

from __future__ import annotations

from scripts.pipeline_fill_prime_images.helpers import (
    _extract_normal_logo_tokens,
    _first_logo_id,
)
from scripts.pipeline_generate_excel_outputs.helpers import (
    _dtf_split_design_prefix,
    _split_item_sku_by_lg,
)


def test_extract_hk_token_from_sku():
    assert _extract_normal_logo_tokens("4486HK-White-M-T-BLK-L") == "4486HK"


def test_first_logo_id_hk():
    assert _first_logo_id("4486HK-White-M-T-BLK-L") == "4486HK"


def test_dtf_split_design_prefix_hk():
    assert _dtf_split_design_prefix("4486HK-White-M-T-BLK-L") == (
        "4486HK-",
        "White-M-T-BLK-L",
    )


def test_split_item_sku_by_hk_multi_design():
    segments = _split_item_sku_by_lg("111HK-M-T-BLK-M-222HK-M-T-WHI-L")
    assert segments == ["111HK-M-T-BLK-M-", "222HK-M-T-WHI-L"]
