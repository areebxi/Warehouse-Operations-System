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
