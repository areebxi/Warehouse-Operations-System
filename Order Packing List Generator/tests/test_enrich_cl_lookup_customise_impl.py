from __future__ import annotations
from pathlib import Path
import pandas as pd
import pytest
from scripts.pipeline_cl_lookup.enrich_cl_lookup import (
    _item_options_indicates_custom,
    enrich_packing_data,
)
from scripts.pipeline_cl_lookup.fetch_input_csv import OUTPUT_COLUMNS, write_fetched_csv

def test_enrich_item_options_skipped_when_cl_already_customise_yes(tmp_path: Path):
    cl_csv = tmp_path / "cl.csv"
    step1 = tmp_path / "step1.csv"
    pd.DataFrame(
        {"Custom Label": ["MATCH-LABEL"], "Customise": ["Yes"]}
    ).to_csv(cl_csv, index=False, encoding="utf-8")
    _write_step1_csv(
        step1,
        [
            {
                "Order Number": "25-00002-00002",
                "Ship By": "",
                "Item Quantity": "1",
                "Item Image URL": "",
                "Item SKU": "PREFIX-MATCH-LABEL",
                "Item Name": "Plain T-Shirt",
                "Item Options": "Message if you do need customisation: Test",
                "Recipient Name": "Test User",
                "Tags": "",
            }
        ],
    )
    logs: list[str] = []

    def log(msg: str) -> None:
        logs.append(msg)

    df = enrich_packing_data(step1, cl_csv_path=cl_csv, log=log)
    assert df.at[0, "Customise"] == "Yes"
    assert not any("from Item Options phrases" in line for line in logs)
def test_enrich_sets_customise_from_back_print_option(tmp_path: Path):
    cl_csv = tmp_path / "cl.csv"
    step1 = tmp_path / "step1.csv"
    _write_min_cl_csv(cl_csv)
    _write_step1_csv(
        step1,
        [
            {
                "Order Number": "25-00004-00004",
                "Ship By": "",
                "Item Quantity": "1",
                "Item Image URL": "",
                "Item SKU": "NO-MATCH-SKU",
                "Item Name": "Plain T-Shirt",
                "Item Options": "Back Print Option: Company Logo",
                "Recipient Name": "Test User",
                "Tags": "",
            }
        ],
    )
    df = enrich_packing_data(step1, cl_csv_path=cl_csv)
    assert df.at[0, "Customise"] == "Yes"
def test_enrich_sets_customise_from_item_options(tmp_path: Path):
    cl_csv = tmp_path / "cl.csv"
    step1 = tmp_path / "step1.csv"
    _write_min_cl_csv(cl_csv)
    _write_step1_csv(
        step1,
        [
            {
                "Order Number": "25-00001-00001",
                "Ship By": "",
                "Item Quantity": "1",
                "Item Image URL": "",
                "Item SKU": "NO-MATCH-SKU",
                "Item Name": "Plain T-Shirt",
                "Item Options": "Message if you do need customisation: Test",
                "Recipient Name": "Test User",
                "Tags": "",
            }
        ],
    )
    df = enrich_packing_data(step1, cl_csv_path=cl_csv)
    assert df.at[0, "Customise"] == "Yes"
def test_enrich_no_phrase_leaves_customise_empty(tmp_path: Path):
    cl_csv = tmp_path / "cl.csv"
    step1 = tmp_path / "step1.csv"
    _write_min_cl_csv(cl_csv)
    _write_step1_csv(
        step1,
        [
            {
                "Order Number": "25-00003-00003",
                "Ship By": "",
                "Item Quantity": "1",
                "Item Image URL": "",
                "Item SKU": "NO-MATCH-SKU",
                "Item Name": "Plain T-Shirt",
                "Item Options": "Size: Large",
                "Recipient Name": "Test User",
                "Tags": "",
            }
        ],
    )
    df = enrich_packing_data(step1, cl_csv_path=cl_csv)
    assert df.at[0, "Customise"] == ""
@pytest.mark.parametrize(
    "value,expected",
    [
        ("Message if you do need customisation: Hello", True),
        ("MESSAGE IF YOU DO NEED CUSTOMISATION", True),
        ("Back Print Option: Logo", True),
        ("BACK PRINT OPTION", True),
        ("Size: 2XL", False),
        ("", False),
        (None, False),
    ],
)
def test_item_options_indicates_custom(value, expected):
    assert _item_options_indicates_custom(value) is expected
def _write_min_cl_csv(path: Path) -> None:
    pd.DataFrame({"Custom Label": []}).to_csv(path, index=False, encoding="utf-8")
def _write_step1_csv(path: Path, rows: list[dict]) -> None:
    write_fetched_csv(rows, path)
