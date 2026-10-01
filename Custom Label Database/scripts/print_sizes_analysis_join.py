"""Join-key probes for print_sizes_analysis."""
from __future__ import annotations

import re

import pandas as pd

from print_sizes_analysis_util import CONFIG, PRINT_SIZES, fill_rate, nonempty


def report_print_fill_rates(df: pd.DataFrame, print_cols: list[str]) -> None:
    print(f"Total rows: {len(df)}")
    for col in print_cols:
        if col in df.columns:
            pct, n = fill_rate(df, col)
            print(f"  {col}: {pct:.1f}% ({n:,})")

    if "Print Positions" not in df.columns:
        return
    from collections import Counter

    pp = df["Print Positions"].fillna("").astype(str).str.strip()
    has_pp = pp != ""
    print(f"\nPrint Positions non-empty: {has_pp.sum():,}")
    m_codes = pp.str.findall(r"\(M(\d+)\)")
    all_codes = [c for codes in m_codes for c in codes]
    print("Top (M###) codes in Print Positions:", Counter(all_codes).most_common(15))
    w1 = df.get("Width 1 (mm)", pd.Series([""] * len(df)))
    has_w1 = w1.apply(nonempty)
    print(f"Rows with Print Positions but no Width 1: {(has_pp & ~has_w1).sum():,}")
    print(f"Rows with no Print Positions: {(~has_pp).sum():,}")


def report_join_overlaps(df: pd.DataFrame, size_ref: pd.DataFrame | None, size_ref_sheet) -> None:
    print_sizes_df = pd.read_excel(PRINT_SIZES, sheet_name=0)
    print(f"\nSize ref sheet used: {size_ref_sheet if size_ref is not None else 'NOT FOUND'}")
    if size_ref is not None:
        print("Size ref columns:", list(size_ref.columns))
        print("Size ref unique key candidates:")
        for c in size_ref.columns:
            u = size_ref[c].dropna().nunique()
            print(f"  {c}: {u} unique, sample: {size_ref[c].dropna().head(3).tolist()}")

    print("\nPrint Sizes columns:", list(print_sizes_df.columns))
    for c in print_sizes_df.columns:
        print(f"  {c}: {print_sizes_df[c].dropna().nunique()} unique")

    if size_ref is None:
        return

    if "Category" in df.columns:
        db_cats = set(df["Category"].dropna().astype(str).str.strip().unique())
        ref_cols = [
            c
            for c in size_ref.columns
            if "category" in c.lower() or "department" in c.lower() or "product" in c.lower()
        ]
        for rc in ref_cols:
            ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
            overlap = db_cats & ref_vals
            print(
                f"\nDB Category vs SizeRef[{rc}]: DB={len(db_cats)}, Ref={len(ref_vals)}, "
                f"overlap={len(overlap)}"
            )
            if len(overlap) < 30:
                print("  Overlap:", sorted(overlap)[:20])
            missing = db_cats - ref_vals
            print(f"  DB categories not in ref: {len(missing)}")
            if missing and len(missing) <= 25:
                print("  ", sorted(missing))

    for rc in [c for c in size_ref.columns if "sub" in c.lower()]:
        if "Category" in df.columns:
            db_subs = set(df["Sub-Category"].dropna().astype(str).str.strip().unique())
            ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
            overlap = db_subs & ref_vals
            print(
                f"\nDB Sub-Category vs SizeRef[{rc}]: overlap={len(overlap)} / "
                f"DB={len(db_subs)} / Ref={len(ref_vals)}"
            )

    ga_cols = [
        c
        for c in size_ref.columns
        if any(x in c.lower() for x in ["gender", "apparel", "style", "product"])
    ]
    print("\nPotential product-type columns in size ref:", ga_cols)
    for rc in ga_cols[:5]:
        ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
        if "Gender Apparel" in df.columns:
            db_ga = set(df["Gender Apparel"].dropna().astype(str).str.strip().unique())
            overlap = db_ga & ref_vals
            print(
                f"  DB Gender Apparel vs [{rc}]: overlap={len(overlap)} / "
                f"DB={len(db_ga)} / Ref={len(ref_vals)}"
            )

    pos_cols = [c for c in size_ref.columns if "position" in c.lower() or "print" in c.lower()]
    print("\nPosition-related columns in size ref:", pos_cols)
    if "Print Positions" in df.columns:
        db_pos = set()
        for val in df["Print Positions"].dropna():
            for part in re.split(r",\s*", str(val)):
                part = re.sub(r"\s*\(M\d+\)\s*$", "", part.strip())
                if part:
                    db_pos.add(part)
        for rc in pos_cols:
            ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
            overlap = db_pos & ref_vals
            print(
                f"  DB position segments vs [{rc}]: overlap={len(overlap)} / "
                f"DB={len(db_pos)} / Ref={len(ref_vals)}"
            )
            db_only = db_pos - ref_vals
            if db_only:
                print(f"    DB-only positions (sample): {sorted(db_only)[:15]}")

    if "Size" in df.columns:
        size_cols = [c for c in size_ref.columns if "size" in c.lower()]
        db_sizes = set(df["Size"].dropna().astype(str).str.strip().unique())
        print(f"\nDB has {len(db_sizes)} unique Size values")
        for rc in size_cols:
            ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
            overlap = db_sizes & ref_vals
            print(f"  DB Size vs [{rc}]: overlap={len(overlap)} / Ref={len(ref_vals)}")

    mm_cols = [
        c for c in size_ref.columns if "width" in c.lower() or "height" in c.lower() or "mm" in c.lower()
    ]
    print("MM columns in size ref:", mm_cols)
    print_sizes_mm = [
        c
        for c in print_sizes_df.columns
        if "width" in c.lower() or "height" in c.lower() or "mm" in c.lower()
    ]
    print("MM columns in Print Sizes:", print_sizes_mm)
