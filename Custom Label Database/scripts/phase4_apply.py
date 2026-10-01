"""PE fill helpers for phase4_cleanup."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

BTC_SUPPLIER = "BTC Activewear"
BASE = Path(r"D:\Custom Label Database")
PE_PATH = BASE / "ProductExport.xlsx"


def g1_format(text: str) -> str:
    """Title-case PE department strings, preserving hyphenated parts."""
    if not text:
        return text
    words = text.split()
    out: list[str] = []
    for word in words:
        if "-" in word:
            out.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)


def apparel_image_slug(gender_apparel: str, colour: str) -> str:
    """Gender Apparel + Colour with spaces as dashes, no double dashes."""
    combined = f"{gender_apparel} {colour}".strip()
    if not combined:
        return ""
    slug = re.sub(r"\s+", "-", combined)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def load_pe() -> pd.DataFrame:
    pe = pd.read_excel(PE_PATH, sheet_name="staff", dtype=str)
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = pe[c].fillna("").astype(str).str.strip()
    return pe.drop_duplicates("UID").set_index("UID", drop=False)


def apply_phase4(df: pd.DataFrame, pe_index: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int], object, int, int]:
    df = df.copy()
    df["sku"] = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    df["suffix"] = df["Custom Label"].str.extract(r"-(\d+)$")[0].fillna("")

    def resolve_pe_uid(row: pd.Series) -> str:
        sku = row.get("sku", "")
        if sku and sku in pe_index.index:
            return sku
        suffix = row.get("suffix", "")
        if not row.get("sku", "") and suffix and suffix in pe_index.index:
            return suffix
        return ""

    counts: dict[str, int] = {}
    pe_uids = df.apply(resolve_pe_uid, axis=1)
    matched = pe_uids.ne("")
    counts["rows_with_pe_match"] = int(matched.sum())
    counts["match_via_supplier_sku"] = int(
        (df["sku"].ne("") & df["sku"].isin(pe_index.index)).sum()
    )
    counts["match_via_suffix_f1"] = int(
        (df["sku"].eq("") & df["suffix"].ne("") & df["suffix"].isin(pe_index.index)).sum()
    )

    pe_dept = pe_uids.map(pe_index["Department"])
    pe_sub = pe_uids.map(pe_index["Sub Department"])
    pe_spc = pe_uids.map(pe_index["SPC"])

    mask = matched & df["Category"].eq("") & pe_dept.ne("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Category"] = pe_dept[mask].map(g1_format)
        counts["4A_category_filled"] = n

    mask = matched & df["Sub-Category"].eq("") & pe_sub.ne("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Sub-Category"] = pe_sub[mask].map(g1_format)
        counts["4B_subcategory_filled"] = n

    mask = matched & df["Supplier Name"].eq("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Supplier Name"] = BTC_SUPPLIER
        counts["4D_supplier_name_filled"] = n

    mask = matched & df["Supplier Product Code"].eq("") & pe_spc.ne("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Supplier Product Code"] = pe_spc[mask]
        counts["4E_spc_filled"] = n

    has_both = df["Gender Apparel"].ne("") & df["Colour"].ne("")
    combined = df["Gender Apparel"] + " " + df["Colour"]
    new_images = (
        combined.str.replace(r"\s+", "-", regex=True)
        .str.replace(r"-+", "-", regex=True)
        .str.strip("-")
    )
    changed_img = has_both & (df["Apparel Image"] != new_images)
    n_img = int(changed_img.sum())
    df.loc[has_both, "Apparel Image"] = new_images[has_both]
    counts["4C_apparel_image_set_or_updated"] = n_img
    counts["4C_apparel_image_total_with_both_fields"] = int(has_both.sum())

    df.drop(columns=["sku", "suffix"], inplace=True)
    sample = df.loc[has_both, ["Gender Apparel", "Colour", "Apparel Image"]].head(5)
    double_dash = int(df["Apparel Image"].str.contains(r"--", regex=True, na=False).sum())
    empty_cat_matched = int((matched & df["Category"].eq("")).sum())
    return df, counts, sample, double_dash, empty_cat_matched
