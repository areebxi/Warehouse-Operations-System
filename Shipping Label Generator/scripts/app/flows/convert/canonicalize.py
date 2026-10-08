from __future__ import annotations

import pandas as pd


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

    proc = df["Process Number"].astype("string")
    sk = proc.str.fullmatch(r"\d+").fillna(False)
    df["_sk"] = 0
    df.loc[sk, "_sk"] = proc[sk].astype(int)
    df["Source Index"] = pd.to_numeric(df["Source Index"], errors="coerce").fillna(0).astype(int)
    df["Source File"] = df["Source File"].astype("string").fillna("").astype("string")

    # Keep DTF file order, then process number within each file.
    df = df.sort_values(
        by=["Source Index", "_sk", "Process Number"],
        ascending=[True, True, True],
        kind="mergesort",
    )
    df = df.drop(columns=["_sk"])
    return df[OUTPUT_COLUMNS]
