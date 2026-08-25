"""Estimate Phase 4 ProductExport fill opportunities on Updated workbook."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Custom Label Database")
CLD = BASE / "Custom Label Database_Updated.xlsx"
PE = BASE / "ProductExport.xlsx"

print("Loading CLD...", flush=True)
df = pd.read_excel(CLD, sheet_name="Data", dtype=str)
for c in df.columns:
    df[c] = df[c].fillna("").astype(str)
print(f"CLD rows: {len(df)}", flush=True)

print("Loading PE...", flush=True)
pe = pd.read_excel(PE, sheet_name="staff", dtype=str)
if str(pe.iloc[0].get("UID", "")).startswith("["):
    pe = pe.iloc[1:].reset_index(drop=True)
for c in pe.columns:
    pe[c] = pe[c].fillna("").astype(str)
print(f"PE rows: {len(pe)}", flush=True)

df["sku"] = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
pe["UID"] = pe["UID"].str.strip()
pe_idx = pe.drop_duplicates("UID").set_index("UID")

matched = df["sku"].ne("") & df["sku"].isin(pe_idx.index)
print(f"Rows with Supplier SKU matching PE UID: {matched.sum()}")
print(f"Unique matched SKUs: {df.loc[matched, 'sku'].nunique()}")
print(f"Rows with blank Supplier SKU: {(df['sku'] == '').sum()}")
print(f"Rows with SKU but no PE match: {((df['sku'] != '') & ~df['sku'].isin(pe_idx.index)).sum()}")

sub = df.loc[matched].copy()
sub["pe_dept"] = sub["sku"].map(pe_idx["Department"])
sub["pe_sub"] = sub["sku"].map(pe_idx["Sub Department"])
sub["pe_img"] = sub["sku"].map(pe_idx["image_url_high_res"])
sub["pe_brand"] = sub["sku"].map(pe_idx["Brand"])
sub["pe_desc"] = sub["sku"].map(pe_idx["Description"])
sub["pe_colour"] = sub["sku"].map(pe_idx["Colour Name"])
sub["pe_size"] = sub["sku"].map(pe_idx["Size"])
sub["pe_spc"] = sub["sku"].map(pe_idx["SPC"])

print("\n=== Fill candidates among matched rows ===")
print(f"Category blank (all are blank globally?): {(df['Category'] == '').sum()} global")
print(f"Sub-Category blank global: {(df['Sub-Category'] == '').sum()}")
print(f"Matched + PE dept available: {(sub['pe_dept'] != '').sum()}")
print(f"Matched + PE sub available: {(sub['pe_sub'] != '').sum()}")
print(f"Apparel Image blank + PE img: {((sub['Apparel Image'] == '') & (sub['pe_img'] != '')).sum()}")
print(f"Supplier Name blank + matched: {(sub['Supplier Name'] == '').sum()}")
print(f"Supplier Product Code blank + PE SPC: {((sub['Supplier Product Code'] == '') & (sub['pe_spc'] != '')).sum()}")
print(f"Colour blank + PE colour: {((sub['Colour'] == '') & (sub['pe_colour'] != '')).sum()}")
print(f"Size blank + PE size: {((sub['Size'] == '') & (sub['pe_size'] != '')).sum()}")

print("\n=== PE Department value counts (top 15) ===")
print(sub["pe_dept"].value_counts().head(15).to_string())
print("\n=== PE Sub Department value counts (top 15) ===")
print(sub["pe_sub"].value_counts().head(15).to_string())

print("\n=== Supplier Name among matched ===")
print(sub["Supplier Name"].value_counts().head(10).to_string())

print("\n=== Also try Custom Label suffix -> UID for unmatched ===")
import re
suffix = df["Custom Label"].str.extract(r"-(\d+)$")[0]
suffix_match = (df["sku"] == "") & suffix.notna() & suffix.isin(pe_idx.index)
print(f"Blank SKU but suffix matches PE UID: {suffix_match.sum()}")

print("\nDone.", flush=True)
