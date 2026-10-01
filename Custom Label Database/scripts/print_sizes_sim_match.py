"""Match-strategy counts for print_sizes_simulation."""
from __future__ import annotations

from collections import Counter, defaultdict

import pandas as pd

from print_sizes_sim_util import db_gender


def build_sr_indexes(sr: pd.DataFrame) -> tuple[dict, dict, dict, dict]:
    has_gender_size = (sr["Gender"] != "") & (sr["Size"] != "")
    sku_suffix = {}
    for _, r in sr.iterrows():
        if r["SKU Value"]:
            key = (r["SKU Value"].upper(), r["Suffix"].upper())
            sku_suffix[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

    gss_lookup = {}
    for _, r in sr[has_gender_size].iterrows():
        key = (r["Gender"], r["Size"], r["Printing Position"])
        gss_lookup[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

    gs_lookup = {}
    for _, r in sr[
        (sr["Gender"] != "") & (sr["Size"] != "") & (sr["Printing Position"] == "")
    ].iterrows():
        key = (r["Gender"], r["Size"])
        gs_lookup[key] = (r["Size Width"], r["Size Height"], r["Printing Size"])

    sr_by_sku: dict[str, list] = defaultdict(list)
    for _, r in sr.iterrows():
        if r["SKU Value"]:
            sr_by_sku[r["SKU Value"].upper()].append(r)
    return sku_suffix, gss_lookup, gs_lookup, sr_by_sku


def run_match_strategies(
    df: pd.DataFrame, sr: pd.DataFrame, ps: pd.DataFrame, gs_lookup: dict, sr_by_sku: dict
) -> Counter:
    stats: Counter = Counter()
    match_a = sum(1 for _, row in df.iterrows() if row["Supplier Product Code"].upper() in sr_by_sku)
    stats["A: Supplier Product Code in SKU Value"] = match_a

    match_b = sum(1 for _, row in df.iterrows() if row["Supplier SKU"].upper() in sr_by_sku)
    stats["B: Supplier SKU in SKU Value"] = match_b

    match_c = sum(1 for _, row in df.iterrows() if row["Custom Label"].upper() in sr_by_sku)
    stats["C: Custom Label exact in SKU Value"] = match_c

    ps_index = ps.set_index("Apparel Size")
    match_d = sum(
        1
        for _, row in df.iterrows()
        if row["Apparel_Size_Key"] and row["Apparel_Size_Key"] in ps_index.index
    )
    stats["D: Print Sizes apparel key match"] = match_d

    match_e = sum(
        1 for _, row in df.iterrows() if row["Print Positions"] and row["Apparel_Size_Key"]
    )
    stats["E: Has Print Positions + apparel size key"] = match_e

    match_f = 0
    for _, row in df.iterrows():
        g = db_gender(row["Gender Apparel"])
        if g and row["Size"] and (g, row["Size"]) in gs_lookup:
            match_f += 1
    stats["F: Gender+Size in Size Ref (no pos)"] = match_f

    product_codes = set(sr["Product Code"].unique()) - {""}
    match_g = 0
    for _, row in df.iterrows():
        spc = row["Supplier Product Code"]
        for pc in product_codes:
            if spc and spc in pc.split("-"):
                match_g += 1
                break
    stats["G: Supplier Product Code in Product Code list"] = match_g
    return stats


def print_spc_detail(df: pd.DataFrame, sr_by_sku: dict) -> None:
    spc_matched = df[df["Supplier Product Code"].str.upper().isin(sr_by_sku.keys())]
    print(f"Rows with SPC in SKU Value: {len(spc_matched):,}")
    if not len(spc_matched):
        return
    sample_spc = spc_matched["Supplier Product Code"].value_counts().head(5).index
    for spc in sample_spc:
        rows = sr_by_sku[spc.upper()]
        print(
            f"\n  SPC={spc}: {len(rows)} ref rows, "
            f"DB rows={(spc_matched['Supplier Product Code'] == spc).sum()}"
        )
        for r in rows[:6]:
            print(
                f"    suffix={r['Suffix']!r} W={r['Size Width']} "
                f"H={r['Size Height']} designs={r['Number of Designs']}"
            )


def print_multi_design(sr: pd.DataFrame) -> None:
    multi = sr[sr["Number of Designs"].astype(str).isin(["4", "4.0", "2", "2.0", "3", "3.0"])]
    print(f"\nMulti-design rows: {len(multi):,}")
    print("Sample multi-design SKU Values:")
    for sku in multi["SKU Value"].value_counts().head(5).index:
        sub = sr[sr["SKU Value"] == sku]
        print(f"\n  SKU={sku}, designs={sub['Number of Designs'].iloc[0]}")
        print(sub[["Suffix", "Size Width", "Size Height", "Printing Size"]].to_string())


def sim_fill_counts(df: pd.DataFrame) -> tuple[int, int]:
    sim_front = sim_multi = 0
    for _, row in df.iterrows():
        if not row["Print Positions"]:
            continue
        positions = row["Pos_List"]
        akey = row["Apparel_Size_Key"]
        if len(positions) == 1 and positions[0] == "Front Center" and akey:
            sim_front += 1
        if len(positions) >= 2 and akey:
            sim_multi += 1
    return sim_front, sim_multi


def override_match_count(df: pd.DataFrame, overrides: pd.DataFrame) -> int:
    ov_match = 0
    for _, row in df.iterrows():
        label = row["Custom Label"] + row["Supplier Product Code"] + row["Supplier SKU"]
        for _, ov in overrides.iterrows():
            if str(ov["SKU Contain"]) in label:
                ov_match += 1
                break
    return ov_match


def print_spc_fill_rates(df: pd.DataFrame, sr_by_sku: dict) -> None:
    spc_nonempty = df["Supplier Product Code"] != ""
    print(f"\nSupplier Product Code filled: {spc_nonempty.sum():,} ({100 * spc_nonempty.mean():.1f}%)")
    spc_in_ref = df["Supplier Product Code"].str.upper().isin(sr_by_sku.keys()).sum()
    print(f"SPC in Size Ref SKU Value: {spc_in_ref:,}")
    partial = 0
    for _, row in df[spc_nonempty].iterrows():
        spc = row["Supplier Product Code"].upper()
        for sku_val in sr_by_sku:
            if spc in sku_val or sku_val in spc:
                partial += 1
                break
    print(f"SPC partial match to SKU Value: {partial:,}")
