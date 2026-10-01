"""Apply + QA for phase3_cleanup."""
from __future__ import annotations

import pandas as pd

SIZE_TYPOS = {
    "Meduim": "Medium",
    "ExtraSmall": "Extra Small",
    "Wodium": "Medium",
}
COLOUR_EXPAND_PAIRS = [
    ("Navy", "Navy Blue"),
    ("Royal", "Royal Blue"),
]


def apply_phase3(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict, dict, int, int, int, dict, int]:
    df = df.copy()
    rows_before = len(df)

    size_counts: dict[str, int] = {}
    for src, dst in SIZE_TYPOS.items():
        mask = df["Size"] == src
        n = int(mask.sum())
        if n:
            size_counts[f"{src} -> {dst}"] = n
            df.loc[mask, "Size"] = dst

    cl = df["Custom Label"]
    vc = cl.value_counts()
    dup = df[cl.isin(vc[vc > 1].index)].copy()
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
            if colours == {short, long}:
                mask = (df["Custom Label"] == lab) & (df["Colour"] == short)
                n = int(mask.sum())
                if n:
                    df.loc[mask, "Colour"] = long
                    n_cells += n
                    labels_touched += 1
        if n_cells:
            d1_counts[key] = n_cells

    dup_mask = df.duplicated(keep="first")
    n_exact = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()
    rows_after = len(df)

    remaining_typos = {k: int((df["Size"] == k).sum()) for k in SIZE_TYPOS}
    cl = df["Custom Label"]
    vc = cl.value_counts()
    dup = df[cl.isin(vc[vc > 1].index)]
    stats = dup.groupby("Custom Label").agg(
        n_gender=("Gender Apparel", "nunique"),
        n_colour=("Colour", "nunique"),
        n_size=("Size", "nunique"),
    )
    colour_only = stats[
        (stats["n_gender"] == 1) & (stats["n_colour"] > 1) & (stats["n_size"] == 1)
    ].index
    remaining_nr = 0
    for lab in colour_only:
        colours = set(df.loc[df["Custom Label"] == lab, "Colour"].unique())
        if colours in ({"Navy", "Navy Blue"}, {"Royal", "Royal Blue"}):
            remaining_nr += 1

    core = dup["Gender Apparel"] + "||" + dup["Colour"] + "||" + dup["Size"]
    n_core = dup.assign(_core=core).groupby("Custom Label")["_core"].nunique()
    n_conflict = int((n_core > 1).sum())
    n_same_core_dup_labels = int((n_core == 1).sum())

    qa = {
        "remaining size typos": remaining_typos,
        "remaining Navy/Royal colour-only conflict labels": remaining_nr,
        "conflict labels remaining": n_conflict,
        "same-core duplicate labels remaining (3B skipped)": n_same_core_dup_labels,
        "exact dups remaining": int(df.duplicated().sum()),
    }
    return df, size_counts, d1_counts, n_exact, rows_before, rows_after, qa, labels_touched
