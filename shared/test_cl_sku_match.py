"""Smoke tests for shared CL SKU match (case-sensitive)."""

from shared.cl_sku_match import match_keys, normalize_label, resolve_label


def test_match_keys_order():
    assert match_keys("SHOP-CT001-2") == ["SHOP-CT001-2", "CT001-2", "SHOP-CT001"]
    assert match_keys("12343-1") == ["12343-1", "1", "12343"]
    assert match_keys("NODASH") == ["NODASH"]


def test_normalize_label_preserves_case():
    assert normalize_label("  DTF-IronOn-A4-YES  ") == "DTF-IronOn-A4-YES"
    assert normalize_label("nan") == ""


def test_resolve_whole_first():
    idx = {"SHOP-CT001-2": "A", "CT001-2": "B", "SHOP-CT001": "C"}
    assert resolve_label("SHOP-CT001-2", idx) == "SHOP-CT001-2"


def test_resolve_after_first_then_till_last():
    idx = {"CT001-2": "B", "SHOP-CT001": "C"}
    assert resolve_label("SHOP-CT001-2", idx) == "CT001-2"
    idx2 = {"SHOP-CT001": "C"}
    assert resolve_label("SHOP-CT001-2", idx2) == "SHOP-CT001"
    assert resolve_label("12343-1", {"12343": "X"}) == "12343"


def test_resolve_is_case_sensitive():
    idx = {"DTF-IronOn-A4-YES": "A"}
    assert resolve_label("190917LG-DTF-IronOn-A4-Yes", idx) is None
    assert resolve_label("190917LG-DTF-IronOn-A4-YES", idx) == "DTF-IronOn-A4-YES"
