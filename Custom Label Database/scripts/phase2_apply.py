"""Maps and apply helpers for phase2_cleanup."""
from __future__ import annotations

import pandas as pd

COLOUR_TYPOS = {
    "Fuschia": "Fuchsia",
    "Colbalt Blue": "Cobalt Blue",
    "Sport Grey": "Sports Grey",
    "Light-Pink": "Light Pink",
}
COLOUR_ABBREV = {
    "Dark Heather": "Dark Heather Grey",
    "Azure": "Azure Blue",
}
SIZE_TO_WORD = {
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "XL": "Extra Large",
    "XS": "Extra Small",
}


def apply_map(series: pd.Series, mapping: dict[str, str]) -> tuple[pd.Series, dict[str, int]]:
    counts: dict[str, int] = {}
    out = series.copy()
    for src, dst in mapping.items():
        mask = out == src
        n = int(mask.sum())
        if n:
            counts[f"{src} -> {dst}"] = n
            out = out.mask(mask, dst)
    return out, counts


def apply_phase2(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, int]], dict]:
    all_counts: dict[str, dict[str, int]] = {}
    df = df.copy()

    df["Colour"], c1 = apply_map(df["Colour"], COLOUR_TYPOS)
    df["Colour"], c2 = apply_map(df["Colour"], COLOUR_ABBREV)
    all_counts["A_colour_typos"] = c1
    all_counts["Bplus_colour_abbrev"] = c2

    df["Size"], c3 = apply_map(df["Size"], SIZE_TO_WORD)
    all_counts["C_size_to_words"] = c3

    ga = df["Gender Apparel"]
    ga2 = ga.str.replace(r" {2,}", " ", regex=True)
    n_space = int((ga2 != ga).sum())
    ga = ga2
    n_mens = int(ga.str.contains("Men's", regex=False).sum())
    ga = ga.str.replace("Men's", "Mens", regex=False)
    n_sweat = int((ga == "Womens-Sweat-Shirt").sum())
    ga = ga.mask(ga == "Womens-Sweat-Shirt", "Womens-Sweatshirt")
    df["Gender Apparel"] = ga
    all_counts["D_gender_apparel"] = {
        "collapse_double_spaces": n_space,
        "Men's -> Mens": n_mens,
        "Womens-Sweat-Shirt -> Womens-Sweatshirt": n_sweat,
    }

    pp = df["Print Positions"]
    n_fp = int((pp == "Front Print").sum())
    df["Print Positions"] = pp.mask(pp == "Front Print", "Front Center")
    all_counts["E_print_positions"] = {"Front Print -> Front Center": n_fp}

    qa = {
        "remaining Fuschia": int((df["Colour"] == "Fuschia").sum()),
        "remaining Colbalt Blue": int((df["Colour"] == "Colbalt Blue").sum()),
        "remaining Sport Grey": int((df["Colour"] == "Sport Grey").sum()),
        "remaining Dark Heather": int((df["Colour"] == "Dark Heather").sum()),
        "remaining Azure (exact)": int((df["Colour"] == "Azure").sum()),
        "remaining letter S/M/L/XL/XS": int(df["Size"].isin(SIZE_TO_WORD).sum()),
        "remaining Men's": int(df["Gender Apparel"].str.contains("Men's", regex=False).sum()),
        "remaining double spaces in Gender Apparel": int(
            df["Gender Apparel"].str.contains(r" {2,}", regex=True).sum()
        ),
        "remaining Front Print": int((df["Print Positions"] == "Front Print").sum()),
        "Royal unchanged count": int((df["Colour"] == "Royal").sum()),
        "Navy unchanged count": int((df["Colour"] == "Navy").sum()),
    }
    return df, all_counts, qa
