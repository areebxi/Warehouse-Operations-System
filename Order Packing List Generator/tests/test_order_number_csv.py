"""Regression tests for Order Number dtype handling."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.pipeline_runtime.order_number_csv import (
    coerce_order_number_columns,
    order_number_to_str,
    read_csv_with_order_numbers,
)
from scripts.pipeline_split_by_process_item.grouping_assign import (
    _sort_and_assign_merge_first,
)


def test_order_number_to_str_large_int():
    assert order_number_to_str(4064592969) == "4064592969"
    assert order_number_to_str(4064592969.0) == "4064592969"
    assert order_number_to_str(np.int64(4064592969)) == "4064592969"


def test_coerce_order_number_columns_from_int64():
    df = pd.DataFrame({"Order Number": [4064592969, 4064592969]})
    out = coerce_order_number_columns(df)
    assert out["Order Number"].dtype == object
    assert out["Order Number"].tolist() == ["4064592969", "4064592969"]


def test_coerce_order_number_columns_from_nullable_int64():
    df = pd.DataFrame({"Order Number": pd.Series([4064592969, 4064592969], dtype="Int64")})
    out = coerce_order_number_columns(df)
    assert out["Order Number"].dtype == object
    assert out["Order Number"].tolist() == ["4064592969", "4064592969"]


def test_read_csv_with_order_numbers(tmp_path):
    path = tmp_path / "orders.csv"
    path.write_text(
        "Order Number,Customise,Process and Item Number,Size,Colour,Recipient Name,Item Quantity\n"
        "4064592969,Yes,4200,Medium,Black,Alison Murray,1\n"
        "4064592969,Yes,4200,Large,Black,Alison Murray,1\n",
        encoding="utf-8",
    )
    df = read_csv_with_order_numbers(path)
    assert df["Order Number"].dtype == object
    assert df["Order Number"].iloc[0] == "4064592969"


def test_coerce_logo_design_image_accepts_customise_stem():
    df = pd.DataFrame(
        {
            "Order Number": [4184116956, 4184116956],
            "Logo/Design Image": [4184116956, 4184116956],
        }
    )
    out = coerce_order_number_columns(df)
    out.loc[1, "Logo/Design Image"] = "4184116956-1"
    assert out["Logo/Design Image"].tolist() == ["4184116956", "4184116956-1"]


def test_read_csv_forces_logo_design_image_string(tmp_path):
    path = tmp_path / "logo.csv"
    path.write_text(
        "Order Number,Logo/Design Image\n4184116956,4184116956\n",
        encoding="utf-8",
    )
    df = read_csv_with_order_numbers(path)
    assert df["Logo/Design Image"].dtype == object
    assert df["Logo/Design Image"].iloc[0] == "4184116956"


def test_merge_suffix_assignment_does_not_raise_on_int64_input():
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

