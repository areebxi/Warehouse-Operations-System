"""PE and Shirts Print Sizes loaders for fill_from_seeds."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from fill_seeds_util import clean, to_num

def _read_pe_table(pe_path: Path, usecols: list[str] | None = None) -> pd.DataFrame:
    if pe_path.suffix.lower() != ".csv":
        kwargs = {"sheet_name": "staff", "dtype": str}
        if usecols:
            kwargs["usecols"] = usecols
        return pd.read_excel(pe_path, **kwargs)
    last_err: Exception | None = None
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            kwargs = {"dtype": str, "encoding": enc}
            if usecols:
                kwargs["usecols"] = usecols
            return pd.read_csv(pe_path, **kwargs)
        except UnicodeDecodeError as e:
            last_err = e
            continue
    raise last_err or UnicodeDecodeError("utf-8", b"", 0, 1, "PE decode failed")


def load_pe_index(pe_path: Path) -> pd.DataFrame:
    pe = _read_pe_table(pe_path)
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = pe[c].fillna("").astype(str).str.strip()
    return pe.drop_duplicates("UID").set_index("UID", drop=False)


def pe_sizes_from_index(pe_index: pd.DataFrame) -> dict[str, str]:
    """Size lookup from an already-loaded PE index (avoids a second PE read)."""
    out: dict[str, str] = {}
    if "UID" not in pe_index.columns or "Size" not in pe_index.columns:
        return out
    for uid, size in zip(pe_index["UID"].map(clean), pe_index["Size"].map(clean)):
        if uid and uid not in out:
            out[uid] = size
    return out


def load_pe_sizes(pe_path: Path) -> dict[str, str]:
    pe = _read_pe_table(pe_path, usecols=["UID", "Size"])
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    return pe_sizes_from_index(pe)


def load_print_sizes(path: Path) -> dict[str, dict[str, tuple[int, int]]]:
    if path.suffix.lower() == ".csv":
        raw = pd.read_csv(path, header=None, dtype=str)
    else:
        raw = pd.read_excel(path, sheet_name=0, header=None)
    table: dict[str, dict[str, tuple[int, int]]] = {}
    for _, row in raw.iloc[2:].iterrows():
        key = clean(row.iloc[0])
        if not key:
            continue
        a4w, a4h = to_num(row.iloc[1]), to_num(row.iloc[2])
        a3w, a3h = to_num(row.iloc[3]), to_num(row.iloc[4])
        entry: dict[str, tuple[int, int]] = {}
        if a4w is not None and a4h is not None:
            entry["A4"] = (int(a4w), int(a4h))
        if a3w is not None and a3h is not None:
            entry["A3"] = (int(a3w), int(a3h))
        if len(row) > 6:
            nw, nh = to_num(row.iloc[5]), to_num(row.iloc[6])
            if nw is not None and nh is not None:
                entry["NECK"] = (int(nw), int(nh))
        if entry:
            table[key] = entry
    return table

