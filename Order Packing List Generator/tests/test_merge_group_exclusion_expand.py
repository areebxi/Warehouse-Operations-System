"""Tests for merge-group issue expansion, Step 4 sibling pull-in, and missing-logo filter."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from scripts.pipeline_runtime.filter_missing_logos import filter_step6_csvs_for_missing_logos
from scripts.pipeline_split_by_process_item.grouping_assign import _sort_and_assign_merge_first
from scripts.pipeline_split_by_process_item.merge_group_mask import (
    expand_issue_mask_to_merge_groups,
)
from scripts.pipeline_split_position.transform_position_codes import split_matched_unmatched
def _stem_maps_ok(tmp_path: Path, stems: dict[str, Path] | None = None):
    """7-tuple from build_preflight_stem_maps (apparel, normal, custom, + 4 dirs)."""
    return (
        None,
        stems if stems is not None else {"TOK-OK": tmp_path / "ok.png"},
        None,
        None,
        tmp_path,
        None,
        None,
    )
def test_expand_pulls_merge_siblings_by_order_number():
    df = pd.DataFrame(
        {
            "Order Number": ["A", "A", "B"],
            "Item Quantity": [1, 1, 1],
        }
    )
    issue = pd.Series([True, False, False], index=df.index)
    out = expand_issue_mask_to_merge_groups(df, issue)
    assert out.tolist() == [True, True, False]
def test_expand_qty_gt_1_is_merge_even_single_row():
    df = pd.DataFrame(
        {
            "Order Number": ["ONLY"],
            "Item Quantity": [3],
        }
    )
    issue = pd.Series([True], index=df.index)
    out = expand_issue_mask_to_merge_groups(df, issue)
    assert out.tolist() == [True]
def test_expand_singleton_issue_stays_local():
    df = pd.DataFrame(
        {
            "Order Number": ["S1", "S2"],
            "Item Quantity": [1, 1],
        }
    )
    issue = pd.Series([True, False], index=df.index)
    out = expand_issue_mask_to_merge_groups(df, issue)
    assert out.tolist() == [True, False]
def test_expand_prefers_order_number_base():
    df = pd.DataFrame(
        {
            "Order Number": ["A", "A-1", "B"],
            "Order Number (Base)": ["A", "A", "B"],
            "Item Quantity": [1, 1, 1],
        }
    )
    issue = pd.Series([True, False, False], index=df.index)
    out = expand_issue_mask_to_merge_groups(df, issue)
    assert out.tolist() == [True, True, False]
def test_step4_split_pulls_merge_siblings_into_unmatched():
    df = pd.DataFrame(
        {
            "Order Number": ["ORD1", "ORD1"],
            "Item Quantity": [1, 1],
            "Gender Apparel": ["", "Mens Tee"],
            "Position": ["Front", "Front"],
        }
    )
    matched, unmatched = split_matched_unmatched(df)
    assert len(matched) == 0
    assert len(unmatched) == 2
    assert set(unmatched["Gender Apparel"].fillna("").astype(str).str.strip()) == {"", "Mens Tee"}
def test_step4_split_singleton_unmatched_stays_alone():
    df = pd.DataFrame(
        {
            "Order Number": ["X", "Y"],
            "Item Quantity": [1, 1],
            "Gender Apparel": ["", "Womens Tee"],
            "Position": ["Front", "Back"],
        }
    )
    matched, unmatched = split_matched_unmatched(df)
    assert len(matched) == 1
    assert matched.iloc[0]["Order Number"] == "Y"
    assert len(unmatched) == 1
    assert unmatched.iloc[0]["Order Number"] == "X"
