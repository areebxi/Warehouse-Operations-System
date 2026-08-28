"""
Restore Apparel Image from Workbook Picture Name; fill blank M## from GA+Colour.

Rules (supervisor 23 Aug 2026):
  1) Match Custom Label -> Workbook `Picture Name`; restore (sanitized).
  2) M## mocks still blank after restore -> Gender Apparel + Colour (maker style).
  3) Apparel Image: letters, digits, dash only (no other special chars).
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

import sys

_REPO = Path(__file__).resolve().parents[1]
_WAREHOUSE = _REPO.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

DB = wh.cl_csv_path(_WAREHOUSE)
WORKBOOK = wh.custom_label_support_dir(_WAREHOUSE) / "Workbook.xlsx"
BACKUPS = wh.cl_backups_dir(_WAREHOUSE)

RE_MOCK = re.compile(r"(?i)^M\d+")
RE_NON_SAFE = re.compile(r"[^A-Za-z0-9-]+")


def sanitize_apparel_name(value: str) -> str:
    """Whitespace/special -> dash; collapse; letters/digits/dash only."""
    s = (value or "").strip()
    if not s:
        return ""
    s = re.sub(r"\s+", "-", s)
    s = RE_NON_SAFE.sub("-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def apparel_image_slug(gender_apparel: str, colour: str) -> str:
    """Maker-style: (Gender Apparel)-(Colour) with spaces as dashes."""
    g = sanitize_apparel_name(gender_apparel)
    c = sanitize_apparel_name(colour)
    if not g and not c:
        return ""
    if not g:
        return c
    if not c:
        return g
    return f"{g}-{c}"


def main() -> None:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUPS / f"Custom_Label_Database_preApparelRestore_{stamp}.csv"
    print(f"Backup -> {backup}", flush=True)
    shutil.copy2(DB, backup)

    print("Loading Workbook Picture Name...", flush=True)
    wb = pd.read_excel(WORKBOOK, sheet_name="CL Database", dtype=str)
    for c in wb.columns:
        wb[c] = wb[c].fillna("").astype(str).str.strip()
    pic_map = (
        wb.loc[wb["Picture Name"].ne(""), ["Custom Label", "Picture Name"]]
        .drop_duplicates("Custom Label", keep="first")
        .set_index("Custom Label")["Picture Name"]
    )
    print(f"  workbook picture keys: {len(pic_map):,}", flush=True)

    print("Loading DB...", flush=True)
    df = pd.read_csv(DB, dtype=str, low_memory=False)
    for c in ["Custom Label", "Gender Apparel", "Colour", "Apparel Image"]:
        if c not in df.columns:
            raise SystemExit(f"Missing column: {c}")
        df[c] = df[c].fillna("").astype(str).str.strip()

    before = df["Apparel Image"].copy()

    # 1) Restore from workbook where Custom Label matches
    restored_src = df["Custom Label"].map(pic_map).fillna("")
    restore_mask = restored_src.ne("")
    restored_clean = restored_src.map(sanitize_apparel_name)
    df.loc[restore_mask, "Apparel Image"] = restored_clean[restore_mask]
    n_restore = int(restore_mask.sum())
    n_restore_changed = int((restore_mask & (before != df["Apparel Image"])).sum())

    # 2) Blank M## only -> GA + Colour slug
    is_mock = df["Custom Label"].str.match(RE_MOCK, na=False)
    blank = df["Apparel Image"].eq("")
    mock_fill_mask = is_mock & blank
    slugs = [
        apparel_image_slug(g, c)
        for g, c in zip(
            df.loc[mock_fill_mask, "Gender Apparel"],
            df.loc[mock_fill_mask, "Colour"],
        )
    ]
    df.loc[mock_fill_mask, "Apparel Image"] = slugs
    n_mock_filled = int((mock_fill_mask & df["Apparel Image"].ne("")).sum())
    n_mock_still_blank = int((is_mock & df["Apparel Image"].eq("")).sum())

    # 3) Final sanitize pass on any remaining AI with unsafe chars (do not invent values)
    unsafe = df["Apparel Image"].ne("") & df["Apparel Image"].str.contains(
        r"[^A-Za-z0-9\-]", regex=True, na=False
    )
    if unsafe.any():
        df.loc[unsafe, "Apparel Image"] = df.loc[unsafe, "Apparel Image"].map(
            sanitize_apparel_name
        )
    n_sanitized = int(unsafe.sum())

    changed = before != df["Apparel Image"]
    print(
        f"\nRestore from workbook: {n_restore:,} rows "
        f"({n_restore_changed:,} values changed vs previous)",
        flush=True,
    )
    print(f"M## blank filled from GA+Colour: {n_mock_filled:,}", flush=True)
    print(f"M## still blank: {n_mock_still_blank:,}", flush=True)
    print(f"Extra sanitize (special chars): {n_sanitized:,}", flush=True)
    print(f"Total Apparel Image cells changed: {int(changed.sum()):,}", flush=True)

    samples = df.loc[changed, ["Custom Label", "Apparel Image"]].head(8)
    print("\nSample changes (Custom Label -> Apparel Image):", flush=True)
    for _, r in samples.iterrows():
        print(f"  {r['Custom Label'][:40]} -> {r['Apparel Image'][:60]}", flush=True)

    bad = df["Apparel Image"].str.contains(r"[^A-Za-z0-9\-]", regex=True, na=False)
    print(f"\nQA: Apparel Image with non dash specials: {int(bad.sum())}", flush=True)

    print(f"\nWriting {DB} ...", flush=True)
    tmp = DB.with_name(DB.stem + "_apparel_restored.tmp.csv")
    df.to_csv(tmp, index=False)
    try:
        shutil.move(str(tmp), str(DB))
    except PermissionError:
        alt = DB.with_name("Custom_Label_Database_apparel_restored.csv")
        shutil.move(str(tmp), str(alt))
        print(
            f"Permission denied on {DB.name}. Wrote {alt.name} instead — "
            "close the CSV in Excel/Cursor and replace, or tell me to retry.",
            flush=True,
        )
        return
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
