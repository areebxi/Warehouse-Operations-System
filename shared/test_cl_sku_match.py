"""Smoke tests for shared CL SKU match."""

from shared.cl_sku_match import match_keys, resolve_label


def test_match_keys_order():
    assert match_keys("SHOP-CT001-2") == ["SHOP-CT001-2", "CT001-2", "SHOP-CT001"]
    assert match_keys("12343-1") == ["12343-1", "1", "12343"]
    assert match_keys("NODASH") == ["NODASH"]


def test_resolve_whole_first():
    idx = {"shop-ct001-2": "A", "ct001-2": "B", "shop-ct001": "C"}
    assert resolve_label("SHOP-CT001-2", idx) == "shop-ct001-2"


def test_resolve_after_first_then_till_last():
    idx = {"ct001-2": "B", "shop-ct001": "C"}
    assert resolve_label("SHOP-CT001-2", idx) == "ct001-2"
    idx2 = {"shop-ct001": "C"}
    assert resolve_label("SHOP-CT001-2", idx2) == "shop-ct001"
    assert resolve_label("12343-1", {"12343": "X"}) == "12343"
