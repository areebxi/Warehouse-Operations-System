"""
Step 2: Enrich packing data from live Custom Label Database CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers

# Warehouse root shared matcher
_WAREHOUSE_ROOT = Path(__file__).resolve().parents[3]
if str(_WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE_ROOT))

from shared.cl_sku_match import (  # noqa: E402
    default_cl_csv_path,
    match_keys,
    resolve_label,
)

NEW_COLUMNS = [
    "Process and Item Number",
    "Gender Apparel",
    "Size",
    "Colour",
    "Picture Name",
    "Position",
    "Customise",
    "Prime",
    "Apparel Image",
    "Logo/Design Image",
]

# Map packing output columns -> candidate CL CSV headers (first present wins).
# Logo/Design Image has no CL CSV column — stays blank. Process and Item Number
# stays blank at Step 2 (Step 5 assigns).
CL_DB_COLUMN_ALIASES = {
    "Process and Item Number": ["Process and Item Number"],
    "Gender Apparel": ["Gender Apparel"],
    "Size": ["Size"],
    "Colour": ["Colour", "Colour Name", "Color"],
    "Picture Name": ["Apparel Image", "Picture Name"],
    "Position": ["Print Positions", "Position"],
    "Customise": ["Customise", "Customize"],
    "Prime": ["Amazon Prime", "Prime"],
    "Apparel Image": ["Apparel Image", "Apparel Picture"],
    "Logo/Design Image": ["Logo/Design Image", "Design Picture", "Logo/Design"],
}

CUSTOM_LABEL_COL = "Custom Label"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "Data"
DEFAULT_WORKBOOK = DATA_DIR / "Workbook.xlsx"
DEFAULT_CL_CSV = default_cl_csv_path(PROJECT_ROOT)

_ITEM_NAME_CUSTOM_KEYWORDS = (
    "personalised",
    "personalized",
    "custom",
    "customisable",
    "customizable",
)

_ITEM_OPTIONS_CUSTOM_PHRASES = (
    "message if you do need customisation",
    "back print option",
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


def load_cl_database(cl_csv_path: Path | None = None) -> pd.DataFrame:
    """Load live Custom_Label_Database.csv (not Workbook CL Database sheet)."""
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

        # Which strategy produced the hit
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


def enrich_packing_data(
    step1_csv_path: Path,
    workbook_path: Path | None = None,
    log: Optional[Callable[[str], None]] = None,
    *,
    cl_lookup: Optional[dict] = None,
    cl_csv_path: Path | None = None,
) -> pd.DataFrame:
    """
    Enrich Step 1 CSV from live CL CSV.

    ``workbook_path`` is unused for CL lookup (kept for call-site compatibility).
    Pass ``cl_csv_path`` to override the default Custom_Label_Database.csv path.
    """
    del workbook_path  # CL sheet retired; other pipeline steps still use Workbook.
    df = read_csv_with_order_numbers(step1_csv_path)
    if cl_lookup is None:
        path = Path(cl_csv_path) if cl_csv_path is not None else DEFAULT_CL_CSV
        cl_df = load_cl_database(path)
        lookup = build_cl_lookup(cl_df)
        if log:
            log(
                f"  Step 2 CL: loaded CL CSV {path.resolve()} ({len(cl_df)} rows); "
                f"{len(lookup)} lookup label(s)."
            )
    else:
        lookup = cl_lookup
        if log:
            log(f"  Step 2 CL: using preloaded lookup ({len(lookup)} label(s)).")
    return apply_cl_enrichment(df, lookup, log=log)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/enrich_cl_lookup.py <step1_csv> [cl_csv] [output_csv]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    step1 = sys.argv[1]
    cl_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CL_CSV

    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
    else:
        stem = Path(step1).stem
        prefix = "1_fetch_input_csv_"
        token = stem[len(prefix) :] if stem.startswith(prefix) else stem
        output_path = PROJECT_ROOT / "Output" / f"2_enrich_cl_lookup_{token}.csv"

    step1_path = Path(step1)
    output_path = Path(output_path)

    df = enrich_packing_data(step1_path, cl_csv_path=cl_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Enriched {len(df)} rows -> {output_path}")


if __name__ == "__main__":
    main()
