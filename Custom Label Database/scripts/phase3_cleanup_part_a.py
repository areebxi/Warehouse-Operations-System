from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

def _main_part_a():
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows_before = len(df)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)
    print(f"Rows before: {rows_before}", flush=True)

    # --- 3C size typos (global) ---
    size_counts: dict[str, int] = {}
    for src, dst in SIZE_TYPOS.items():
        mask = df["Size"] == src
        n = int(mask.sum())
        if n:
            size_counts[f"{src} -> {dst}"] = n
            df.loc[mask, "Size"] = dst
    print(f"3C size typos: {size_counts}", flush=True)

    # --- D1: colour expand only inside colour-only conflict labels ---
    cl = df["Custom Label"]
    vc = cl.value_counts()
    dup_labels = vc[vc > 1].index
    dup = df[cl.isin(dup_labels)].copy()

    # Per-label uniqueness
    stats = dup.groupby("Custom Label").agg(
        n_gender=("Gender Apparel", "nunique"),
        n_colour=("Colour", "nunique"),
        n_size=("Size", "nunique"),
    )
    colour_only = stats[
        (stats["n_gender"] == 1) & (stats["n_colour"] > 1) & (stats["n_size"] == 1)
    ].index

    d1_counts: dict[str, int] = {}
    labels_touched = 0
    for short, long in COLOUR_EXPAND_PAIRS:
        key = f"{short} -> {long} (colour-only conflicts)"
        n_cells = 0
        for lab in colour_only:
            colours = set(df.loc[df["Custom Label"] == lab, "Colour"].unique())
            # Only when the label's colours are exactly {short, long}
            if colours == {short, long}:
                mask = (df["Custom Label"] == lab) & (df["Colour"] == short)
                n = int(mask.sum())
                if n:
                    df.loc[mask, "Colour"] = long
                    n_cells += n
                    labels_touched += 1
        if n_cells:
            d1_counts[key] = n_cells
    print(f"D1 colour expand: {d1_counts} labels_touched~={labels_touched}", flush=True)

    # --- 3A exact full-row duplicates (after 3C/D1 so newly identical rows collapse) ---
    dup_mask = df.duplicated(keep="first")
    n_exact = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()
    rows_after = len(df)
    print(f"3A exact dups removed: {n_exact}", flush=True)

    return {"c": c, "cl": cl, "colour_only": colour_only, "colours": colours, "d1_counts": d1_counts, "df": df, "dst": dst, "dup": dup, "dup_labels": dup_labels, "dup_mask": dup_mask, "key": key, "lab": lab, "labels_touched": labels_touched, "long": long, "mask": mask, "n": n, "n_cells": n_cells, "n_exact": n_exact, "rows_after": rows_after, "rows_before": rows_before, "short": short, "size_counts": size_counts, "src": src, "stats": stats, "vc": vc}
