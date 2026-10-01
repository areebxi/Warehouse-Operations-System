"""Load reference workbooks for print_sizes_simulation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from print_sizes_sim_util import (
    extract_mock,
    nonempty,
    normalize_db_size_for_print,
    split_positions,
)

BASE = Path(r"d:\Custom Label Database")
UPDATED = BASE / "Custom Label Database_Updated.xlsx"
CONFIG = BASE / "Configuration Workbook.xlsx"
PRINT_SIZES = BASE / "Print Sizes.xlsx"

USECOLS = [
    "Custom Label",
    "Supplier SKU",
    "Supplier Product Code",
    "Supplier Name",
    "Category",
    "Sub-Category",
    "Gender Apparel",
    "Size",
    "Colour",
    "Print Positions",
    "Print Position Code",
    "Position 1 Name",
    "Print Size 1",
    "Width 1 (mm)",
    "Height 1 (mm)",
]


def load_print_sizes() -> pd.DataFrame:
    ps_raw = pd.read_excel(PRINT_SIZES, sheet_name=0, header=None)
    ps = ps_raw.iloc[2:].copy()
    ps.columns = ["Apparel Size", "A4_W", "A4_H", "A3_W", "A3_H", "Neck_W", "Neck_H"]
    ps = ps.dropna(subset=["Apparel Size"])
    for c in ["A4_W", "A4_H", "A3_W", "A3_H", "Neck_W", "Neck_H"]:
        ps[c] = pd.to_numeric(ps[c], errors="coerce")
    return ps


def load_size_ref() -> tuple[pd.DataFrame, pd.DataFrame]:
    size_ref = pd.read_excel(CONFIG, sheet_name="Size References")
    overrides = pd.read_excel(CONFIG, sheet_name="Override Print Size")
    sr = size_ref.copy()
    for col in sr.columns:
        sr[col] = sr[col].apply(lambda x: str(x).strip() if nonempty(x) else "")
    return sr, overrides


def load_db() -> pd.DataFrame:
    df = pd.read_excel(UPDATED, usecols=USECOLS)
    for c in df.columns:
        df[c] = df[c].apply(lambda x: str(x).strip() if nonempty(x) else "")
    df["Mock Code"] = df["Print Positions"].apply(extract_mock)
    df["Pos_List"] = df["Print Positions"].apply(split_positions)
    df["Pos_Count"] = df["Pos_List"].apply(len)
    return df


def enrich_apparel_keys(df: pd.DataFrame, ps: pd.DataFrame) -> pd.DataFrame:
    apparel_sizes = list(ps["Apparel Size"].astype(str))
    df = df.copy()
    df["Apparel_Size_Key"] = df.apply(
        lambda r: normalize_db_size_for_print(r["Size"], r["Gender Apparel"], apparel_sizes),
        axis=1,
    )
    return df


def print_sr_profiles(sr: pd.DataFrame) -> None:
    print("\n=== Size References row profiles ===")
    has_gender_size = (sr["Gender"] != "") & (sr["Size"] != "")
    has_print_pos = sr["Printing Position"] != ""
    has_product = sr["Product Code"] != ""
    has_suffix = sr["Suffix"] != ""
    has_print_size = sr["Printing Size"] != ""
    print(f"Total rows: {len(sr)}")
    print(f"  With Gender+Size: {has_gender_size.sum():,}")
    print(f"  With Printing Position: {has_print_pos.sum():,}")
    print(f"  With Product Code: {has_product.sum():,}")
    print(f"  With Suffix only (no gender): {(has_suffix & ~has_gender_size).sum():,}")
    print(f"  With Printing Size: {has_print_size.sum():,}")
    print(f"  Unique SKU Value: {sr['SKU Value'].nunique():,}")
    print("\nGender+Size sample:")
    print(sr[has_gender_size].head(10).to_string())
    print("\nPrinting Position sample:")
    print(sr[has_print_pos].drop_duplicates("Printing Position").head(10).to_string())
    print("\nSuffix distribution:")
    print(sr["Suffix"].value_counts().head(10))
    print("\nPrinting Size values:", sr["Printing Size"].value_counts().to_dict())
    print("\nTop SKU Value entries:")
    print(sr["SKU Value"].value_counts().head(20))
    paper = sr[sr["SKU Value"].isin(["A3", "A4", "A5", "A6", "A9", "A10"])]
    print("\nPaper size rows:")
    print(paper.to_string())
    print("\nProduct Code unique values:")
    for pc in sr["Product Code"].unique():
        if not pc:
            continue
        cnt = (sr["Product Code"] == pc).sum()
        print(f"  {pc[:60]}... : {cnt}" if len(pc) > 60 else f"  {pc}: {cnt}")

