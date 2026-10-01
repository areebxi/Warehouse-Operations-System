"""Tests for Step 2 Customise rules (Item Options phrase)."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import pytest
from scripts.pipeline_cl_lookup.enrich_cl_lookup import (
    _item_options_indicates_custom,
    enrich_packing_data,
)
from scripts.pipeline_cl_lookup.fetch_input_csv import OUTPUT_COLUMNS, write_fetched_csv
def test_fetch_input_csv_maps_item_options(tmp_path: Path):
    from scripts.pipeline_cl_lookup.fetch_input_csv import fetch_input_csv

    raw = tmp_path / "raw.csv"
    raw.write_text(
        "Order - Number,Item - SKU,Item - Name,Item - Options,Quantity,Recipient\n"
        'ORD-1,SKU-1,Name,Message if you do need customisation: x,1,Alice\n',
        encoding="utf-8",
    )
    rows = fetch_input_csv(raw, warn_missing_columns=False)
    assert len(rows) == 1
    assert rows[0]["Item Options"] == "Message if you do need customisation: x"
    assert set(rows[0].keys()) == set(OUTPUT_COLUMNS)
def test_fetch_input_csv_maps_gift_message(tmp_path: Path):
    from scripts.pipeline_cl_lookup.fetch_input_csv import fetch_input_csv

    raw = tmp_path / "raw.csv"
    raw.write_text(
        "Order - Number,Gift - Message,Item - Image URL,Quantity,Item - SKU,Item - Name,Recipient\n"
        'ORD-1,https://example.com/gift.jpg,,1,SKU-1,Name,Alice\n',
        encoding="utf-8",
    )
    rows = fetch_input_csv(raw, warn_missing_columns=False)
    assert rows[0]["Gift Message"] == "https://example.com/gift.jpg"
    assert rows[0]["Item Image URL"] == ""
def test_fetch_input_csv_maps_notes_from_buyer(tmp_path: Path):
    from scripts.pipeline_cl_lookup.fetch_input_csv import fetch_input_csv

    raw = tmp_path / "raw.csv"
    raw.write_text(
        "Order - Number,Notes - From Buyer,Quantity,Item - SKU,Item - Name,Recipient\n"
        'ORD-1,"Please ship ASAP",1,SKU-1,Name,Alice\n',
        encoding="utf-8",
    )
    rows = fetch_input_csv(raw, warn_missing_columns=False)
    assert rows[0]["Notes From Buyer"] == "Please ship ASAP"
    assert set(rows[0].keys()) == set(OUTPUT_COLUMNS)
def test_fetch_input_csv_skips_discount_item_name(tmp_path: Path):
    from scripts.pipeline_cl_lookup.fetch_input_csv import fetch_input_csv

    raw = tmp_path / "raw.csv"
    raw.write_text(
        "Order - Number,Item - SKU,Item - Name,Quantity,Recipient\n"
        "ORD-1,SKU-1,Plain T-Shirt,1,Alice\n"
        "ORD-2,,Discount,1,Bob\n"
        "ORD-3,,DISCOUNT CODE,1,Carol\n",
        encoding="utf-8",
    )
    rows = fetch_input_csv(raw, warn_missing_columns=False)
    assert len(rows) == 1
    assert rows[0]["Order Number"] == "ORD-1"
    assert rows[0]["Item Name"] == "Plain T-Shirt"
