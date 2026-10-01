"""Load mocks / PE / CL for generate_from_mocks."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from generate_mocks_util import clean

SHEET = "Data"


def load_pe(pe_path: Path) -> pd.DataFrame:
    pe = pd.read_excel(pe_path, sheet_name="staff", dtype=str)
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = pe[c].map(clean)
    return pe


def existing_mock_ids(db: pd.DataFrame) -> set[str]:
    labels = db["Custom Label"].map(clean)
    mocks = labels.str.extract(r"^(M\d+)", expand=False).dropna()
    return {m.upper() for m in mocks if m}


def load_mocks(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str)
    raw["Pasting Mocks ID"] = raw["Pasting Mocks ID"].map(clean)
    mocks = raw[raw["Pasting Mocks ID"].str.match(r"^M\d+$", na=False)].copy()
    mocks = mocks.drop_duplicates(subset=["Pasting Mocks ID"], keep="first")
    return mocks


def load_db(db_path: Path) -> pd.DataFrame:
    if db_path.suffix.lower() == ".csv":
        return pd.read_csv(db_path, dtype=str, low_memory=False)
    return pd.read_excel(db_path, sheet_name=SHEET, dtype=str)


def save_db(df: pd.DataFrame, db_path: Path) -> None:
    if db_path.suffix.lower() == ".csv":
        df.to_csv(db_path, index=False)
    else:
        df.to_excel(db_path, sheet_name=SHEET, index=False)
