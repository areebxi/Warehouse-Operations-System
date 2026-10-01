"""
Phase 3 cleanup — supervisor choices:
  3A exact dups: YES
  3B same-core keep richest: NO
  3C size typos: YES
  D1 Navy/Royal expand only inside colour-only conflicts: YES
  D2 gender-only prefer brand: NO
  D3 true conflicts report only: NO
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from scripts.phase3_apply import apply_phase3
from scripts.phase3_log import write_phase3_changelog

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
BACKUP = BASE / (
    f"Custom Label Database_Updated_prePhase3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
)
OUT = SRC
LOG = BASE / "docs" / "PHASE_3_CHANGELOG.md"


def main():
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)

    df, size_counts, d1_counts, n_exact, rows_before, rows_after, qa, labels_touched = (
        apply_phase3(df)
    )
    print(f"Rows before: {rows_before}", flush=True)
    print(f"3C size typos: {size_counts}", flush=True)
    print(f"D1 colour expand: {d1_counts} labels_touched~={labels_touched}", flush=True)
    print(f"3A exact dups removed: {n_exact}", flush=True)
    print(f"Rows after: {rows_after}", flush=True)
    print(f"QA: {qa}", flush=True)

    print(f"Writing {OUT} ...", flush=True)
    df.to_excel(OUT, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

    write_phase3_changelog(
        LOG,
        backup_name=BACKUP.name,
        rows_before=rows_before,
        rows_after=rows_after,
        n_exact=n_exact,
        size_counts=size_counts,
        d1_counts=d1_counts,
        qa=qa,
    )
    print(f"Changelog: {LOG}", flush=True)
    print("Phase 3 complete.", flush=True)


if __name__ == "__main__":
    main()
