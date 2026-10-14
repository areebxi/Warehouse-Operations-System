from __future__ import annotations

import pandas as pd

from scripts.app.util.process_numbers import process_number_sort_key


OUTPUT_COLUMNS = [
    "Process Number",
    "orders Numbers",
    "Customer Name",
    "Source File",
    "Source Index",
]


def canonicalize_orders(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    if not dfs:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    tagged: list[pd.DataFrame] = []
    for i, raw in enumerate(dfs):
        df = raw.copy()
        if "Customer Name" not in df.columns:
            df["Customer Name"] = ""
        if "Source File" not in df.columns:
            df["Source File"] = ""
        if "Source Index" not in df.columns:
            df["Source Index"] = int(i)
        tagged.append(df)

    df = pd.concat(tagged, ignore_index=True)

    # De-dupe by order number (keep first = earlier source file / row).
    df = df.drop_duplicates(subset=["orders Numbers"], keep="first")

    df["Source Index"] = pd.to_numeric(df["Source Index"], errors="coerce").fillna(0).astype(int)
    df["Source File"] = df["Source File"].astype("string").fillna("").astype("string")
    # 1, 2, … 10 — not 1, 10, 2. Same for B100-S1-1 vs B100-S1-10.
    df["_sk"] = df["Process Number"].map(process_number_sort_key)

    df = df.sort_values(
        by=["Source Index", "_sk"],
        ascending=[True, True],
        kind="mergesort",
    )
    df = df.drop(columns=["_sk"])
    return df[OUTPUT_COLUMNS]
