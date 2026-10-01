"""
Generate Custom Label Database seed rows from the Mocks Database Guide.

Creates rows with ONLY these seed columns filled:
  Custom Label, Gender Apparel, Colour, Size, Apparel Image, Print Positions

Rules:
  - Custom Label = {Pasting Mocks ID}-{UID}  (e.g. M01-120877)
  - UID comes from BTC Product Data rows whose SPC matches a Product Code on the mock
  - Gender Apparel = "{Brand Code} {Description}" (Men's->Mens, Kid's->Kids, Ladies'->Ladies)
  - Colour / Size from BTC Product Data (with Phase-2 style size/colour normalize)
  - Apparel Image = slug(Gender Apparel + Colour)
  - Print Positions mapped from mock Printing Position
  - Skip entire mock IDs already present in the Custom Label Database
  - Skip any mock / UID where any of the 6 seed columns cannot be filled

Examples:

  python scripts/generate_from_mocks.py --dry-run
  python scripts/generate_from_mocks.py --mock M01,M03
  python scripts/generate_from_mocks.py
  python scripts/generate_from_mocks.py --no-backup
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
_WAREHOUSE = SCRIPT_DIR.parent.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
from scripts.generate_from_mocks_impl1 import generate_rows, append_to_db, map_print_positions, normalize_size, save_db
from scripts.generate_from_mocks_impl2 import split_product_codes, strip_special, normalize_description, load_mocks, clean, apparel_image_slug, gender_apparel_from_pe, normalize_colour, load_pe, existing_mock_ids, load_db

BASE = SCRIPT_DIR.parent
SUPPORT = wh.custom_label_support_dir()
BACKUPS = wh.cl_backups_dir()

DEFAULT_DB = wh.cl_csv_path()
DEFAULT_PE = wh.btc_product_data_path()
DEFAULT_MOCKS = wh.mocks_database_csv_path()
SHEET = "Data"

SEED_COLS = [
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
]

SIZE_TO_WORD = {
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "XL": "Extra Large",
    "XS": "Extra Small",
}

AGE_BANDS = {
    "1-2",
    "2-3",
    "3-4",
    "5-6",
    "7-8",
    "9-11",
    "12-13",
    "12-14",
    "14-15",
}

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

# Mock Printing Position -> Print Positions cell (without mock suffix)
PRINT_POS_MAP = {
    "Front Print": "Front Center",
    "Back Print": "Back Center",
    "Left Chest": "Front Left Pocket",
    "Front & Back Print": "Front Center, Back Center",
    "Left Chest & Back Print": "Front Left Pocket, Back Center",
    "Front  Print with Both Sleeves": "Front Center, Sleeve",
    "Front Print with Both Sleeves": "Front Center, Sleeve",
    "Front & Back with Both Sleeves": "Front Center, Back Center, Sleeve",
    "Front & Back with Right Sleeve": "Front Center, Back Center, Right Sleeve",
    "Front & Back with Left Sleeve": "Front Center, Back Center, Sleeve",
    "Left Chest & Left Sleeves": "Front Left Pocket, Sleeve",
    "Left Neck & Left Sleeve Bottom": "Front Left Pocket, Sleeve",
    "Front Print & Inside Print": "Front Center, Inside",
    "Front Print & Front Pocket": "Front Center, Front Left Pocket",
}

RE_CRLF = re.compile(r"[\r\n]+")
RE_MOCK_ID = re.compile(r"^M\d+$", re.I)
# Letters, digits, space, dash, comma, (), /, ., +, # — strip ™ & ' etc.
RE_SPECIAL = re.compile(r"[^A-Za-z0-9 ,\-/().+#]")


def main() -> int:
    p = argparse.ArgumentParser(description="Generate seed rows from Mocks Guide + BTC Product Data")
    p.add_argument("--file", type=Path, default=DEFAULT_DB, help="Custom_Label_Database.csv (or .xlsx)")
    p.add_argument("--pe", type=Path, default=DEFAULT_PE, help="BTC Product Data CSV/XLSX")
    p.add_argument("--mocks", type=Path, default=DEFAULT_MOCKS, help="Mocks Database Guide CSV")
    p.add_argument("--mock", default="", help="Comma list of mock IDs to process (default: all eligible)")
    p.add_argument("--dry-run", action="store_true", help="Report only; do not write")
    p.add_argument("--no-backup", action="store_true", help="Skip backup before write")
    args = p.parse_args()

    only_mocks = None
    if clean(args.mock):
        only_mocks = {m.strip().upper() for m in args.mock.split(",") if m.strip()}

    print(f"Loading mocks: {args.mocks}", flush=True)
    mocks = load_mocks(args.mocks)
    print(f"  mock rows={len(mocks):,}", flush=True)

    print(f"Loading PE: {args.pe}", flush=True)
    pe = load_pe(args.pe)
    print(f"  PE rows={len(pe):,}", flush=True)

    print(f"Loading DB: {args.file}", flush=True)
    db = load_db(args.file)
    for c in db.columns:
        db[c] = db[c].fillna("").astype(str)
    print(f"  DB rows={len(db):,}", flush=True)

    skip_ids = existing_mock_ids(db)
    print(f"  Mock IDs already in DB (will skip): {len(skip_ids)}", flush=True)

    new_rows, meta = generate_rows(mocks, pe, skip_ids, only_mocks)
    counts = meta["counts"]
    skip_reasons = meta["skip_reasons"]

    print("\n=== Counts ===", flush=True)
    for k in sorted(counts):
        if k.startswith("rows_M"):
            continue
        print(f"  {k}: {counts[k]:,}", flush=True)

    print(f"\nNew seed rows ready: {len(new_rows):,}", flush=True)
    if len(new_rows):
        print("\nSample (first 5):", flush=True)
        print(new_rows.head(5).to_string(index=False), flush=True)
        print("\nPer-mock new rows:", flush=True)
        per = new_rows["Custom Label"].str.extract(r"^(M\d+)", expand=False).value_counts()
        for mid, n in per.items():
            print(f"  {mid}: {n:,}", flush=True)

    # Show skip summary (limit)
    interesting = {
        k: v
        for k, v in skip_reasons.items()
        if not v.startswith("mock already in")
    }
    if interesting:
        print(f"\nSkipped mocks (non-already-in-DB): {len(interesting)}", flush=True)
        for mid, reason in list(interesting.items())[:40]:
            print(f"  {mid}: {reason}", flush=True)
        if len(interesting) > 40:
            print(f"  ... and {len(interesting) - 40} more", flush=True)

    if args.dry_run:
        print("\nDry-run: no file written.", flush=True)
        return 0

    if new_rows.empty:
        print("Nothing to write.", flush=True)
        return 0

    append_to_db(args.file, new_rows, backup=not args.no_backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
