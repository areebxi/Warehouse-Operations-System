"""BTC Product Data enrich step for fill_from_seeds."""
from __future__ import annotations

import re

import pandas as pd

from fill_seeds_apparel import g1_format
from fill_seeds_util import BTC_SUPPLIER, clean, uid_from_custom_label

def _pe_column(pe_index: pd.DataFrame, *names: str) -> str:
    """Resolve a PE header, ignoring hyphen/space/case."""
    def norm(s: str) -> str:
        return re.sub(r"[\s_\-]+", "", s).lower()

    by_norm = {norm(c): c for c in pe_index.columns}
    for name in names:
        if name in pe_index.columns:
            return name
        hit = by_norm.get(norm(name))
        if hit:
            return hit
    return ""


# DB column <- PE column. Title-case matches the existing Category fill.
PE_TAXONOMY = (
    ("Category", "Department", True),
    ("Sub-Category", "Sub Department", True),
    ("Department", "Department", True),
    ("Sub-Department", "Sub Department", True),
    ("Brand", "Brand", False),
)
# These four track PE Department / Sub Department. When PE is corrected, overwrite them.
PE_TAXONOMY_REFRESH = frozenset(
    {"Category", "Sub-Category", "Department", "Sub-Department"}
)


def step_pe_enrich(
    df: pd.DataFrame,
    pe_index: pd.DataFrame,
    counts: dict,
    overwrite_taxonomy: bool = False,
) -> None:
    """Fill Supplier Name / SPC / Brand (blank only) and PE taxonomy."""
    for col in (
        "Supplier Name",
        "Supplier Product Code",
        "Category",
        "Sub-Category",
        "Department",
        "Sub-Department",
        "Brand",
    ):
        if col not in df.columns:
            df[col] = ""

    sku = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    suffix = df["Custom Label"].map(uid_from_custom_label)

    pe_uids = []
    via_sku = 0
    via_suffix = 0
    for s, suf in zip(sku, suffix):
        if s and s in pe_index.index:
            pe_uids.append(s)
            via_sku += 1
        elif (not s) and suf and suf in pe_index.index:
            pe_uids.append(suf)
            via_suffix += 1
        else:
            pe_uids.append("")
    pe_uids_s = pd.Series(pe_uids, index=df.index)
    matched = pe_uids_s.ne("")
    counts["pe_matched"] = int(matched.sum())
    counts["pe_via_sku"] = via_sku
    counts["pe_via_suffix"] = via_suffix

    def pe_col(uid: str, col: str) -> str:
        if not uid or not col or col not in pe_index.columns:
            return ""
        val = pe_index.at[uid, col]
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return clean(val)

    pe_spc = pe_uids_s.map(lambda u: pe_col(u, "SPC"))

    mask = matched & df["Supplier Name"].eq("")
    df.loc[mask, "Supplier Name"] = BTC_SUPPLIER
    counts["supplier_name_filled"] = int(mask.sum())

    mask = matched & df["Supplier Product Code"].eq("") & pe_spc.ne("")
    df.loc[mask, "Supplier Product Code"] = pe_spc[mask]
    counts["spc_filled"] = int(mask.sum())

    pe_dept_col = _pe_column(pe_index, "Department")
    pe_sub_col = _pe_column(pe_index, "Sub Department", "Sub-Department")
    pe_brand_col = _pe_column(pe_index, "Brand")
    pe_src = {
        "Department": pe_dept_col,
        "Sub Department": pe_sub_col,
        "Brand": pe_brand_col,
    }

    for db_col, pe_name, title_case in PE_TAXONOMY:
        src = pe_src.get(pe_name, "")
        incoming = pe_uids_s.map(
            lambda u, c=src, tc=title_case: (
                g1_format(pe_col(u, c)) if tc else pe_col(u, c)
            )
            if c
            else ""
        )
        already = matched & df[db_col].ne("") & incoming.ne("")
        differ = already & (df[db_col] != incoming)
        counts[f"{db_col}_already_differs"] = int(differ.sum())
        blank_mask = matched & df[db_col].eq("") & incoming.ne("")
        if overwrite_taxonomy and db_col in PE_TAXONOMY_REFRESH:
            over_mask = differ
            df.loc[over_mask, db_col] = incoming[over_mask]
            df.loc[blank_mask, db_col] = incoming[blank_mask]
            counts[f"{db_col}_overwritten"] = int(over_mask.sum())
            counts[f"{db_col}_filled"] = int(blank_mask.sum())
        else:
            df.loc[blank_mask, db_col] = incoming[blank_mask]
            counts[f"{db_col}_filled"] = int(blank_mask.sum())
            counts[f"{db_col}_overwritten"] = 0
        counts[f"{db_col}_still_blank"] = int((df[db_col].map(clean) == "").sum())

