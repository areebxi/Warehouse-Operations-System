"""Apply CL lookup columns + Customise keyword overrides."""

from __future__ import annotations

from typing import Callable, Optional

import pandas as pd

from shared.cl_sku_match import match_keys, resolve_label

from .enrich_cl_const import (
    CUSTOM_LABEL_COL,
    CL_DB_COLUMN_ALIASES,
    NEW_COLUMNS,
    _ITEM_NAME_CUSTOM_KEYWORDS,
    _ITEM_OPTIONS_CUSTOM_PHRASES,
)


def key_after_first_dash(item_sku: str) -> str:
    """Kept for callers/tests; shared matcher owns the live match order."""
    from shared.cl_sku_match import key_after_first_dash as _k

    return _k(item_sku)


def _item_name_indicates_custom(item_name) -> bool:
    if pd.isna(item_name):
        return False
    s = str(item_name).strip().lower()
    if not s:
        return False
    return any(kw in s for kw in _ITEM_NAME_CUSTOM_KEYWORDS)


def _item_options_indicates_custom(item_options) -> bool:
    if pd.isna(item_options):
        return False
    s = str(item_options).strip().lower()
    if not s:
        return False
    return any(phrase in s for phrase in _ITEM_OPTIONS_CUSTOM_PHRASES)


def _customise_is_yes(val) -> bool:
    if pd.isna(val):
        return False
    return str(val).strip().lower() == "yes"


def load_cl_database(cl_csv_path) -> pd.DataFrame:
    """Load live Custom_Label_Database.csv (not Workbook CL Database sheet)."""
    from pathlib import Path

    from .enrich_cl_const import DEFAULT_CL_CSV

    path = Path(cl_csv_path) if cl_csv_path is not None else DEFAULT_CL_CSV
    if not path.is_file():
        raise FileNotFoundError(f"Custom Label Database CSV not found: {path}")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if CUSTOM_LABEL_COL not in df.columns:
        raise ValueError(f"CL CSV must have a column named '{CUSTOM_LABEL_COL}': {path}")
    df[CUSTOM_LABEL_COL] = df[CUSTOM_LABEL_COL].astype(str).str.strip()
    return df


def build_cl_lookup(cl_df: pd.DataFrame) -> dict:
    cl_col_to_out = {}
    for out_col, candidates in CL_DB_COLUMN_ALIASES.items():
        for c in candidates:
            if c in cl_df.columns:
                cl_col_to_out[out_col] = c
                break

    lookup = {}
    for _, row in cl_df.iterrows():
        label = row.get(CUSTOM_LABEL_COL)
        if pd.isna(label) or label == "" or str(label).lower() == "nan":
            continue
        key = str(label).casefold()
        if key in lookup:
            continue
        entry = {}
        for out_col, cl_col in cl_col_to_out.items():
            val = row.get(cl_col)
            if pd.isna(val) or val == "":
                entry[out_col] = ""
            else:
                entry[out_col] = str(val).strip() if isinstance(val, str) else val
        lookup[key] = entry
    return lookup


def apply_cl_enrichment(
    df: pd.DataFrame,
    lookup: dict,
    log: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """Apply CL lookup columns using universal match order."""
    df = df.copy()
    for col in NEW_COLUMNS:
        df[col] = ""

    matched_by_strategy = {"whole": 0, "after-first-dash": 0, "till-last-dash": 0}
    unmatched_rows = 0
    sample_unmatched: list[str] = []
    matched_examples: list[str] = []

    strategy_names = ("whole", "after-first-dash", "till-last-dash")

    for idx, row in df.iterrows():
        item_sku = row.get("Item SKU", "")
        keys = match_keys(item_sku)
        matched_key = resolve_label(item_sku, lookup)
        if matched_key is None:
            unmatched_rows += 1
            if len(sample_unmatched) < 25:
                sample_unmatched.append("" if pd.isna(item_sku) else str(item_sku).strip())
            continue

        strategy = "whole"
        for i, candidate in enumerate(keys):
            if candidate.casefold() == matched_key:
                strategy = strategy_names[min(i, 2)]
                break
        matched_by_strategy[strategy] = matched_by_strategy.get(strategy, 0) + 1

        for out_col, value in lookup[matched_key].items():
            df.at[idx, out_col] = value
        if len(matched_examples) < 10:
            bits = [f"{c}={str(df.at[idx, c])[:55]}" for c in NEW_COLUMNS]
            matched_examples.append(
                f"[{strategy}] lookup_key={matched_key!r} item_sku={str(item_sku)[:100]} | "
                + " | ".join(bits)
            )

    name_to_custom = 0
    if "Item Name" in df.columns:
        for idx, row in df.iterrows():
            if _item_name_indicates_custom(row.get("Item Name")) and not _customise_is_yes(
                row.get("Customise")
            ):
                df.at[idx, "Customise"] = "Yes"
                name_to_custom += 1

    options_to_custom = 0
    if "Item Options" in df.columns:
        for idx, row in df.iterrows():
            if _item_options_indicates_custom(row.get("Item Options")) and not _customise_is_yes(
                row.get("Customise")
            ):
                df.at[idx, "Customise"] = "Yes"
                options_to_custom += 1

    if log:
        n = len(df)
        log(
            f"  Step 2 CL: matched whole={matched_by_strategy['whole']}/{n}, "
            f"after-first-dash={matched_by_strategy['after-first-dash']}/{n}, "
            f"till-last-dash={matched_by_strategy['till-last-dash']}/{n}; "
            f"{unmatched_rows} unmatched (columns stay blank)."
        )
        if matched_examples:
            log(f"  Step 2 CL: example CL matches (up to {len(matched_examples)}):")
            for ex in matched_examples:
                log(f"    {ex}")
        if sample_unmatched and unmatched_rows:
            log(f"  Step 2 CL: sample Item SKU with no match (up to 25): {', '.join(sample_unmatched)}")
        if name_to_custom:
            log(
                f"  Step 2 CL: set Customise=Yes on {name_to_custom} row(s) from Item Name keywords "
                f"(personalised/custom, etc.) where Customise was not already Yes."
            )
        if options_to_custom:
            log(
                f"  Step 2 CL: set Customise=Yes on {options_to_custom} row(s) from Item Options phrases "
                f"({', '.join(repr(p) for p in _ITEM_OPTIONS_CUSTOM_PHRASES)}) where Customise was not already Yes."
            )

    return df
