"""Tests for config-driven packing rules (Item Quantity correction)."""

from __future__ import annotations

import pandas as pd

from scripts.pipeline_packing_rules.rules import apply_packing_rules, row_matches_rule

MATCHING_SKU = "17786LG-DTF-IronOn-A6"
MATCHING_NAME = "England Crest Set of 5 Ready to Press"
RULE = {
    "sku": MATCHING_SKU,
    "item_name_contains": "Set of 5",
    "set_item_quantity": 5,
}


def _row(*, sku: str = MATCHING_SKU, name: str = MATCHING_NAME, qty: int = 1) -> dict:
    return {
        "Order Number": "206-7017360-0269934",
        "Item SKU": sku,
        "Item Name": name,
        "Item Quantity": qty,
    }


def test_matching_row_sets_qty_to_five():
    df = pd.DataFrame([_row()])
    out, stats = apply_packing_rules(df, [RULE])
    assert out.at[0, "Item Quantity"] == 5
    assert stats["total_updated"] == 1
    assert stats["rule_hits"][0]["count"] == 1


def test_case_insensitive_match():
    df = pd.DataFrame(
        [
            _row(
                sku="17786lg-dtf-ironon-a6",
                name="Product SET OF 5 pack",
                qty=1,
            )
        ]
    )
    out, stats = apply_packing_rules(df, [RULE])
    assert out.at[0, "Item Quantity"] == 5
    assert stats["total_updated"] == 1
    assert row_matches_rule(out.loc[0], RULE)


def test_missing_phrase_unchanged():
    df = pd.DataFrame([_row(name="England Crest Single Print", qty=1)])
    out, stats = apply_packing_rules(df, [RULE])
    assert out.at[0, "Item Quantity"] == 1
    assert stats["total_updated"] == 0
    assert stats["rule_hits"][0]["count"] == 0


def test_wrong_sku_unchanged():
    df = pd.DataFrame([_row(sku="OTHER-SKU", qty=1)])
    out, stats = apply_packing_rules(df, [RULE])
    assert out.at[0, "Item Quantity"] == 1
    assert stats["total_updated"] == 0


def test_override_when_qty_already_higher():
    df = pd.DataFrame([_row(qty=10)])
    out, stats = apply_packing_rules(df, [RULE])
    assert out.at[0, "Item Quantity"] == 5
    assert stats["total_updated"] == 1
    assert stats["rule_hits"][0]["count"] == 1


def test_empty_rules_list_unchanged():
    df = pd.DataFrame([_row(qty=1)])
    out, stats = apply_packing_rules(df, [])
    assert out.at[0, "Item Quantity"] == 1
    assert stats["total_updated"] == 0
    assert stats["rule_hits"] == []


def test_already_correct_qty_counts_match_but_no_update():
    df = pd.DataFrame([_row(qty=5)])
    out, stats = apply_packing_rules(df, [RULE])
    assert out.at[0, "Item Quantity"] == 5
    assert stats["total_updated"] == 0
    assert stats["rule_hits"][0]["count"] == 1
