"""Plain and Packs fill blank Gender Apparel after Custom Label."""

from __future__ import annotations

import pandas as pd

from scripts.pipeline_cl_lookup.enrich_plain_packs import apply_plain_packs


def test_plain_stock_code_fills_when_cl_gender_blank():
    df = pd.DataFrame([{"Item SKU": "C2200-30-S", "Gender Apparel": ""}])
    plain = {
        "c2200-30-s": {
            "Department (Areeb)": "Mens",
            "Product Type (Areeb)": "Hoodie",
            "Size": "S",
            "Colour": "White",
            "Description": "Hood",
        }
    }
    out = apply_plain_packs(df, plain, {})
    assert out.at[0, "Gender Apparel"] == "Mens Hoodie"
    assert out.at[0, "Size"] == "S"
    assert out.at[0, "Colour"] == "White"


def test_printed_cl_gender_is_kept():
    df = pd.DataFrame(
        [{"Item SKU": "C2200-30-S", "Gender Apparel": "Printed Hoodie", "Size": "M", "Colour": "Black"}]
    )
    plain = {
        "c2200-30-s": {
            "Department (Areeb)": "Mens",
            "Product Type (Areeb)": "Hoodie",
            "Size": "S",
            "Colour": "White",
        }
    }
    out = apply_plain_packs(df, plain, {})
    assert out.at[0, "Gender Apparel"] == "Printed Hoodie"
    assert out.at[0, "Size"] == "M"


def test_pack_matches_whole_sku_only():
    df = pd.DataFrame([{"Item SKU": "SET01", "Gender Apparel": ""}])
    packs = {"set01": {"Product Type (Areeb)": "T-Shirt", "Pack Size": "S", "Pack Name": "Core"}}
    out = apply_plain_packs(df, {}, packs)
    assert out.at[0, "Gender Apparel"] == "T-Shirt"
    assert out.at[0, "Size"] == "S"


def test_plain_till_last_dash_beats_whole():
    df = pd.DataFrame([{"Item SKU": "C2200-30-S", "Gender Apparel": ""}])
    plain = {
        "c2200-30": {"Product Type (Areeb)": "From style", "Size": "M", "Colour": "Black"},
        "c2200-30-s": {"Product Type (Areeb)": "From stock code", "Size": "S", "Colour": "White"},
    }
    out = apply_plain_packs(df, plain, {})
    assert out.at[0, "Gender Apparel"] == "From style"
    assert out.at[0, "Size"] == "M"
