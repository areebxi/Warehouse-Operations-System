"""Tests for duplicate-order base / base-1 / base-2 suffix assignment."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from scripts.pipeline_preflight_issues.service import _process_one_csv
from scripts.pipeline_split_by_process_item.duplicate_order_suffixes import (
    assign_merge_order_number_suffixes,
)
from scripts.pipeline_split_by_process_item.grouping_assign import (
    _sort_and_assign_merge_first,
)


def test_three_customise_rows_get_n_n1_n2_logo_tokens():
    df = pd.DataFrame(
        {
            "Order Number": ["23097214817", "23097214817", "23097214817"],
            "Customise": ["Yes", "Yes", "Yes"],
            "Recipient Name": ["Taseer Hasan", "Taseer Hasan", "Taseer Hasan"],
            "Item Quantity": [1, 1, 1],
            "Logo/Design Image": ["23097214817", "23097214817", "23097214817"],
        }
    )
    out = assign_merge_order_number_suffixes(df)
    assert out["Order Number"].tolist() == [
        "23097214817",
        "23097214817-1",
        "23097214817-2",
    ]
    assert out["Logo/Design Image"].tolist() == [
        "23097214817",
        "23097214817-1",
        "23097214817-2",
    ]
    assert out["Order Number (Base)"].tolist() == [
        "23097214817",
        "23097214817",
        "23097214817",
    ]


def test_mixed_customise_advances_position_only_yes_updates_logo():
    df = pd.DataFrame(
        {
            "Order Number": ["ORD-1", "ORD-1", "ORD-1"],
            "Customise": ["Yes", "No", "Yes"],
            "Recipient Name": ["Alex", "Alex", "Alex"],
            "Item Quantity": [1, 1, 1],
            "Logo/Design Image": ["ORD-1", "8513LG", "ORD-1"],
        }
    )
    out = assign_merge_order_number_suffixes(df)
    assert out["Order Number"].tolist() == ["ORD-1", "ORD-1-1", "ORD-1-2"]
    assert out["Logo/Design Image"].tolist() == ["ORD-1", "8513LG", "ORD-1-2"]


def test_single_row_order_no_suffix():
    df = pd.DataFrame(
        {
            "Order Number": ["ONLY-ONE"],
            "Customise": ["Yes"],
            "Recipient Name": ["Sam"],
            "Item Quantity": [1],
            "Logo/Design Image": ["ONLY-ONE"],
        }
    )
    out = assign_merge_order_number_suffixes(df)
    assert out["Order Number"].tolist() == ["ONLY-ONE"]
    assert out["Logo/Design Image"].tolist() == ["ONLY-ONE"]
    assert out["Order Number (Base)"].tolist() == ["ONLY-ONE"]


def test_grouping_assign_still_assigns_suffixes_and_logos():
    df = pd.DataFrame(
        {
            "Order Number": [4064592969, 4064592969],
            "Customise": ["Yes", "Yes"],
            "Process and Item Number": ["4200", "4200"],
            "Size": ["Medium", "Large"],
            "Colour": ["Black", "Black"],
            "Recipient Name": ["Alison Murray", "Alison Murray"],
            "Item Quantity": [1, 1],
            "Logo/Design Image": ["", ""],
            "_orig_idx": [0, 1],
        }
    )
    out = _sort_and_assign_merge_first(df, size_to_rank=None)
    assert out["Order Number"].tolist() == ["4064592969", "4064592969-1"]
    assert out["Logo/Design Image"].tolist() == ["4064592969", "4064592969-1"]


def test_process_one_csv_expands_quantity_before_suffixes(monkeypatch, tmp_path: Path):
    csv_path = tmp_path / "4000.csv"
    csv_path.write_text("x\n", encoding="utf-8")

    step4_df = pd.DataFrame(
        {
            "Order Number": ["204-7249793-7733914"] * 4,
            "Customise": ["Yes"] * 4,
            "Recipient Name": ["Kirsty"] * 4,
            "Item Quantity": [1, 2, 1, 5],
            "Gender Apparel": ["Mens-T-Shirt"] * 4,
            "Item SKU": [
                "98765PER-M-T-WHI-S-Yes",
                "98765PER-M-T-WHI-L-Yes",
                "98765PER-M-T-WHI-XL-Yes",
                "98765PER-M-T-WHI-M-Yes",
            ],
            "Logo/Design Image": ["204-7249793-7733914"] * 4,
        }
    )

    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.fetch_input_csv",
        lambda *_a, **_k: [{"Order Number": "1"}],
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.coerce_order_number_columns",
        lambda df: df,
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.apply_cl_enrichment",
        lambda df, *_a, **_k: df.assign(**{"Gender Apparel": "Men"}),
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.fill_packing_columns_df",
        lambda df, **_k: df,
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.transform_step4_df",
        lambda *_a, **_k: (step4_df.copy(), None),
    )

    cache = MagicMock()
    cache.cl_lookup = {}
    cache.logo_id_to_position = None
    cache.default_code = "P"
    cache.position_to_code = {}
    cache.multiple_positions_df = None

    out = _process_one_csv(csv_path, cache)
    assert out is not None
    assert len(out) == 9
    assert out["Item Quantity"].astype(int).tolist() == [1] * 9
    assert out["Logo/Design Image"].tolist() == [
        "204-7249793-7733914",
        "204-7249793-7733914-1",
        "204-7249793-7733914-2",
        "204-7249793-7733914-3",
        "204-7249793-7733914-4",
        "204-7249793-7733914-5",
        "204-7249793-7733914-6",
        "204-7249793-7733914-7",
        "204-7249793-7733914-8",
    ]
    assert out["Item SKU"].tolist() == [
        "98765PER-M-T-WHI-S-Yes",
        "98765PER-M-T-WHI-L-Yes",
        "98765PER-M-T-WHI-L-Yes",
        "98765PER-M-T-WHI-XL-Yes",
        "98765PER-M-T-WHI-M-Yes",
        "98765PER-M-T-WHI-M-Yes",
        "98765PER-M-T-WHI-M-Yes",
        "98765PER-M-T-WHI-M-Yes",
        "98765PER-M-T-WHI-M-Yes",
    ]


def test_process_one_csv_applies_merge_suffixes(monkeypatch, tmp_path: Path):
    csv_path = tmp_path / "8050.csv"
    csv_path.write_text("x\n", encoding="utf-8")

    step4_df = pd.DataFrame(
        {
            "Order Number": ["23097214817", "23097214817", "23097214817"],
            "Customise": ["Yes", "Yes", "Yes"],
            "Recipient Name": ["Taseer Hasan", "Taseer Hasan", "Taseer Hasan"],
            "Item Quantity": [1, 1, 1],
            "Gender Apparel": ["Men", "Men", "Men"],
            "Logo/Design Image": ["23097214817", "23097214817", "23097214817"],
        }
    )

    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.fetch_input_csv",
        lambda *_a, **_k: [{"Order Number": "1"}],
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.coerce_order_number_columns",
        lambda df: df,
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.apply_cl_enrichment",
        lambda df, *_a, **_k: df.assign(**{"Gender Apparel": "Men"}),
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.fill_packing_columns_df",
        lambda df, **_k: df,
    )
    monkeypatch.setattr(
        "scripts.pipeline_preflight_issues.service.transform_step4_df",
        lambda *_a, **_k: (step4_df.copy(), None),
    )

    cache = MagicMock()
    cache.cl_lookup = {}
    cache.logo_id_to_position = None
    cache.default_code = "P"
    cache.position_to_code = {}
    cache.multiple_positions_df = None

    out = _process_one_csv(csv_path, cache)
    assert out is not None
    assert out["Logo/Design Image"].tolist() == [
        "23097214817",
        "23097214817-1",
        "23097214817-2",
    ]
    assert out["Order Number"].tolist() == [
        "23097214817",
        "23097214817-1",
        "23097214817-2",
    ]
