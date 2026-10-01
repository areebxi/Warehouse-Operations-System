"""Non-PE / non-print fill steps for fill_from_seeds."""
from __future__ import annotations

import pandas as pd

from fill_seeds_util import (
    DEDICATED_SUPPLIERS,
    apparel_image_slug,
    clean,
    customise_for_label,
    uid_from_custom_label,
)

def step_customise(df: pd.DataFrame, counts: dict) -> None:
    """Customise from Custom Label: -P{digit}- or Yes token => Yes; else not Yes."""
    if "Customise" not in df.columns:
        df["Customise"] = ""
    for idx in df.index:
        label = clean(df.at[idx, "Custom Label"])
        if not label:
            continue
        expected = customise_for_label(label)
        current = clean(df.at[idx, "Customise"])
        if expected:
            if current != "Yes":
                df.at[idx, "Customise"] = "Yes"
                counts["customise_set_yes"] += 1
        elif current.lower() == "yes":
            df.at[idx, "Customise"] = ""
            counts["customise_cleared_yes"] += 1


def step_areeb(df: pd.DataFrame, counts: dict) -> None:
    """Areeb 30-chain from Gender Apparel warehouse standard. Overwrites the four cells."""
    from shared.areeb_taxonomy import AREEB_COLS, apply_areeb, classify_cl

    for col in AREEB_COLS:
        if col not in df.columns:
            df[col] = ""
    for idx in df.index:
        row = {c: clean(df.at[idx, c]) if c in df.columns else "" for c in df.columns}
        values = classify_cl(row)
        patch = apply_areeb(row, values)
        if not patch:
            continue
        for col, val in patch.items():
            df.at[idx, col] = val
        counts["areeb_rows"] += 1
        counts[f"areeb_{values.source or 'none'}"] += 1


def step_supply(df: pd.DataFrame, counts: dict) -> None:
    """Supply Method from FOTL t-shirt / iron-on+sticker / everything-else lock. Overwrites."""
    from shared.supply_method import COL, classify_cl_row

    if COL not in df.columns:
        df[COL] = ""
    for idx in df.index:
        row = {c: clean(df.at[idx, c]) if c in df.columns else "" for c in df.columns}
        value = classify_cl_row(row)
        prev = clean(df.at[idx, COL]) if COL in df.columns else ""
        df.at[idx, COL] = value
        counts["supply_rows"] += 1
        counts[f"supply_{value}"] += 1
        if prev != value:
            counts["supply_changed"] += 1


def step_printing_type(df: pd.DataFrame, counts: dict) -> None:
    """Printing Type: mock DTF/Sublimation, else mugs Sublimation, else DTF. Overwrites."""
    from shared.printing_type import COL, classify_cl_row, load_mock_printing_types

    if COL not in df.columns:
        df[COL] = ""
    mock_types = load_mock_printing_types()
    for idx in df.index:
        row = {c: clean(df.at[idx, c]) if c in df.columns else "" for c in df.columns}
        value = classify_cl_row(row, mock_types=mock_types)
        prev = clean(df.at[idx, COL]) if COL in df.columns else ""
        df.at[idx, COL] = value
        counts["printing_type_rows"] += 1
        counts[f"printing_type_{value}"] += 1
        if prev != value:
            counts["printing_type_changed"] += 1


def step_supplier_name(df: pd.DataFrame, counts: dict) -> None:
    """Supplier Name: Absolute babysuits, else Uneek, else BTC. In-house blank. Overwrites."""
    from shared.areeb_taxonomy import load_catalogs
    from shared.supplier_name import COL, classify_cl_row

    if COL not in df.columns:
        df[COL] = ""
    cat = load_catalogs()
    for idx in df.index:
        row = {c: clean(df.at[idx, c]) if c in df.columns else "" for c in df.columns}
        value = classify_cl_row(row, cat)
        prev = clean(df.at[idx, COL]) if COL in df.columns else ""
        df.at[idx, COL] = value
        counts["supplier_name_rows"] += 1
        counts[f"supplier_name_{value or 'blank'}"] += 1
        if prev != value:
            counts["supplier_name_changed"] += 1


def step_supplier_sku(df: pd.DataFrame, counts: dict) -> None:
    """Fill blank Supplier SKU from Custom Label UID suffix."""
    if "Supplier SKU" not in df.columns:
        df["Supplier SKU"] = ""
    uids = df["Custom Label"].map(uid_from_custom_label)
    cur = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    mask = cur.eq("") & uids.ne("")
    df.loc[mask, "Supplier SKU"] = uids[mask]
    counts["sku_filled"] = int(mask.sum())



def step_dedicated_suppliers(df: pd.DataFrame, counts: dict) -> None:
    """Copy generic supplier fields into BTC/Ralawise/Absolute columns by name."""
    needed = ["Supplier Name", "Supplier SKU", "Supplier Product Code", "Supplier Stock"]
    for col in needed:
        if col not in df.columns:
            df[col] = ""
    for _, sku_c, pc_c, stock_c in DEDICATED_SUPPLIERS:
        for c in (sku_c, pc_c, stock_c):
            if c not in df.columns:
                df[c] = ""

    name = df["Supplier Name"].fillna("").astype(str).str.strip()
    name_l = name.str.lower()
    sku = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    pc = df["Supplier Product Code"].fillna("").astype(str).str.strip()
    stock = df["Supplier Stock"].fillna("").astype(str).str.strip()

    for key, sku_c, pc_c, stock_c in DEDICATED_SUPPLIERS:
        match = name_l.str.contains(key, na=False)
        counts[f"suppliers_{key}_rows"] = int(match.sum())

        m = match & df[sku_c].eq("") & sku.ne("")
        df.loc[m, sku_c] = sku[m]
        counts[f"filled_{sku_c}"] = int(m.sum())

        m = match & df[pc_c].eq("") & pc.ne("")
        df.loc[m, pc_c] = pc[m]
        counts[f"filled_{pc_c}"] = int(m.sum())

        m = match & df[stock_c].eq("") & stock.ne("")
        df.loc[m, stock_c] = stock[m]
        counts[f"filled_{stock_c}"] = int(m.sum())


def step_apparel_image(df: pd.DataFrame, counts: dict) -> None:
    if "Apparel Image" not in df.columns:
        df["Apparel Image"] = ""
    has_both = df["Gender Apparel"].ne("") & df["Colour"].ne("")
    slugs = pd.Series(
        [
            apparel_image_slug(g, c)
            for g, c in zip(df["Gender Apparel"], df["Colour"])
        ],
        index=df.index,
    )
    mask = has_both & df["Apparel Image"].eq("") & slugs.ne("")
    df.loc[mask, "Apparel Image"] = slugs[mask]
    counts["apparel_image_filled"] = int(mask.sum())

