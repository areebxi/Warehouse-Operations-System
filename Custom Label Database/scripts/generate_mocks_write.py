"""Append generated seed rows to Custom Label Database."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from generate_mocks_load import load_db, save_db
from generate_mocks_util import SEED_COLS
from shared import paths as wh

BACKUPS = wh.cl_backups_dir()


def append_to_db(db_path: Path, new_rows: pd.DataFrame, backup: bool) -> None:
    if backup:
        BACKUPS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = BACKUPS / f"{db_path.stem}_preGenerate_{stamp}{db_path.suffix}"
        print(f"Backup -> {bak}", flush=True)
        shutil.copy2(db_path, bak)

    print(f"Loading DB for append: {db_path}", flush=True)
    df = load_db(db_path)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)

    for c in SEED_COLS:
        if c not in df.columns:
            df[c] = ""

    blank = {c: "" for c in df.columns}
    add = []
    for _, row in new_rows.iterrows():
        rec = dict(blank)
        for c in SEED_COLS:
            rec[c] = row[c]
        add.append(rec)

    out = pd.concat([df, pd.DataFrame(add)], ignore_index=True)
    print(f"Writing {db_path} ({len(df):,} -> {len(out):,} rows) ...", flush=True)
    save_db(out, db_path)
    print("Done.", flush=True)
