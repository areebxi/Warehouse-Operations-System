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
from test_merge_group_exclusion_expand import (
    _stem_maps_ok,
    test_expand_pulls_merge_siblings_by_order_number,
    test_expand_qty_gt_1_is_merge_even_single_row,
    test_expand_singleton_issue_stays_local,
    test_expand_prefers_order_number_base,
    test_step4_split_pulls_merge_siblings_into_unmatched,
    test_step4_split_singleton_unmatched_stays_alone,
)
def test_filter_missing_logos_excludes_merge_group(tmp_path: Path):
    csv_path = tmp_path / "Process_1.csv"
    df = pd.DataFrame(
        {
            "Order Number": ["M1", "M1", "OK1"],
            "Order Number (Base)": ["M1", "M1", "OK1"],
            "Item Quantity": [1, 1, 1],
            "Customise": ["No", "No", "No"],
            "Item SKU": ["SKU-A", "SKU-B", "SKU-C"],
            "Logo/Design Image": ["TOK-MISS", "TOK-OK", "TOK-OK"],
        }
    )
    df.to_csv(csv_path, index=False, encoding="utf-8")

    missing_flags = pd.Series([True, False, False], index=df.index)
    apparel_flags = pd.Series([False, False, False], index=df.index)

    with (
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.build_preflight_stem_maps",
            return_value=_stem_maps_ok(tmp_path),
        ),
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.flag_missing_images",
            return_value=(missing_flags, apparel_flags),
        ),
    ):
        kept, missing_path, n_excluded = filter_step6_csvs_for_missing_logos(
            [csv_path],
            output_root=tmp_path,
            token="tok",
            logo_custom_single_dir=None,
            logo_custom_double_dir=None,
            logo_normal_dir=tmp_path,
        )

    assert n_excluded == 2
    assert missing_path is not None and missing_path.exists()
    excluded = pd.read_csv(missing_path)
    assert len(excluded) == 2
    assert set(excluded["Order Number (Base)"].astype(str)) == {"M1"}
    assert len(kept) == 1
    kept_df = pd.read_csv(kept[0])
    assert kept_df["Order Number"].tolist() == ["OK1"]
def test_filter_then_naming_has_no_process_item_gaps(tmp_path: Path):
    """Supervisor 2026-09-17: strip missing logos before Step 6 naming so PIN has no holes."""
    csv_path = tmp_path / "5_assign_process_number_tok.csv"
    base = "4000-PRINTED-2-WAREHOUSE STOCK-P-S1-5"
    df = pd.DataFrame(
        {
            "Order Number": ["A", "B", "C"],
            "Item Quantity": [1, 1, 1],
            "Customise": ["No", "No", "No"],
            "Item SKU": ["SKU-A", "SKU-B", "SKU-C"],
            "Logo/Design Image": ["TOK-OK", "TOK-MISS", "TOK-OK"],
            "Process and Item Number": [base, base, base],
            "Gender Apparel": ["Men", "Men", "Women"],
            "Size": ["S", "M", "L"],
            "Colour": ["Red", "Blue", "Green"],
        }
    )
    df.to_csv(csv_path, index=False, encoding="utf-8")

    def fake_flag(frame, **_kw):
        miss = frame["Logo/Design Image"].astype(str).eq("TOK-MISS")
        return miss, pd.Series(False, index=frame.index)

    with (
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.build_preflight_stem_maps",
            return_value=_stem_maps_ok(tmp_path),
        ),
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.flag_missing_images",
            side_effect=fake_flag,
        ),
    ):
        kept, _, n_excluded = filter_step6_csvs_for_missing_logos(
            [csv_path],
            output_root=tmp_path,
            token="tok",
            logo_custom_single_dir=None,
            logo_custom_double_dir=None,
            logo_normal_dir=tmp_path,
        )

    assert n_excluded == 1
    assert len(kept) == 1
    kept_df = pd.read_csv(kept[0])
    named = _sort_and_assign_merge_first(
        kept_df, size_to_rank=None, use_simple_process_format=True
    )
    pins = named["Process and Item Number"].tolist()
    assert pins == [
        f"Process {base}-1 Item-1",
        f"Process {base}-2 Item-1",
    ]
def test_filter_excludes_customise_qty2_when_second_stem_missing(tmp_path: Path):
    csv_path = tmp_path / "5_assign_process_number_tok.csv"
    df = pd.DataFrame(
        {
            "Order Number": ["ORD"],
            "Item Quantity": [2],
            "Customise": ["Yes"],
            "Item SKU": ["SKU-A"],
            "Logo/Design Image": ["ORD"],
            "Recipient Name": ["Pat"],
        }
    )
    df.to_csv(csv_path, index=False, encoding="utf-8")

    seen = {}

    def fake_flag(frame, **_kw):
        seen["stems"] = frame["Logo/Design Image"].astype(str).tolist()
        miss = pd.Series(
            [stem.endswith("-1") for stem in seen["stems"]], index=frame.index
        )
        return miss, pd.Series(False, index=frame.index)

    with (
        patch(
                "scripts.pipeline_runtime.filter_missing_logos.build_preflight_stem_maps",
                return_value=_stem_maps_ok(tmp_path, {"ORD": tmp_path / "ok.png"}),
        ),
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.flag_missing_images",
            side_effect=fake_flag,
        ),
    ):
        kept, missing_path, n_excluded = filter_step6_csvs_for_missing_logos(
            [csv_path],
            output_root=tmp_path,
            token="tok",
            logo_custom_single_dir=None,
            logo_custom_double_dir=None,
            logo_normal_dir=tmp_path,
        )

    assert seen["stems"] == ["ORD", "ORD-1"]
    assert n_excluded == 2
    assert kept == []
    assert not csv_path.exists()
    excluded = pd.read_csv(missing_path)
    assert len(excluded) == 2
    assert excluded["Logo/Design Image"].astype(str).tolist() == ["ORD", "ORD-1"]
