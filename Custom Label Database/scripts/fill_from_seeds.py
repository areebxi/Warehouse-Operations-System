"""
Reusable filler for Custom Label Database.csv (preferred) or .xlsx

Use when you add rows with seed columns only:
  Custom Label, Gender Apparel, Colour, Size, Apparel Image,
  Print Positions, Customise

Fills what it can:
  1) Supplier SKU  <- last numeric UID from Custom Label
        (M260-214332 / M261-P4-24786 -> 214332 / 24786)
  2) BTC Product Data enrich: Supplier Name, SPC, Brand (blank only);
     Category / Department ← PE Department, Sub-Category / Sub-Department
     ← PE Sub Department (blank only, or --overwrite-pe-taxonomy after PE corrections)
  3) Dedicated supplier cols (BTC / Ralawise / Absolute) from Supplier Name
  4) Apparel Image slug from Gender Apparel + Colour (blank only)
  5) Print sizes: shirts from Shirts Print Sizes.csv (size band);
     other / bags / paper / exact mock+UID from Size References.csv
     (blank Width/Height only; Number of Designs; Print Positions names)

Examples (from repo root):

  python scripts/fill_from_seeds.py
  python scripts/fill_from_seeds.py --dry-run
  python scripts/fill_from_seeds.py --steps sku,pe,suppliers,image,print,customise,areeb,supply,printing_type,supplier_name
  python scripts/fill_from_seeds.py --steps print --only-missing-wh
  python scripts/fill_from_seeds.py --iloc-from 124109
  python scripts/fill_from_seeds.py --steps sku,pe --overwrite-pe-taxonomy --dry-run
  python scripts/fill_from_seeds.py --no-backup
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from fill_seeds_exports import *  # noqa: F401,F403,E402
from fill_seeds_exports import ALL_STEPS, DEFAULT_CONFIG, DEFAULT_DB, DEFAULT_PE, DEFAULT_PRINT_SIZES, SHEET  # noqa: E402
from fill_seeds_run import run_fill  # noqa: E402

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fill Custom Label Database from seed columns + helpers."
    )
    p.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_DB,
        help=f"Working DB (default: {DEFAULT_DB.name})",
    )
    p.add_argument("--pe", type=Path, default=DEFAULT_PE, help="BTC Product Data CSV/XLSX")
    p.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Size References.csv (or Configuration Workbook.xlsx)",
    )
    p.add_argument(
        "--print-sizes",
        type=Path,
        default=DEFAULT_PRINT_SIZES,
        help="Shirts Print Sizes.csv",
    )
    p.add_argument(
        "--steps",
        default=",".join(ALL_STEPS),
        help="Comma list: sku,pe,suppliers,image,print,customise,areeb,supply,printing_type (default: all)",
    )
    p.add_argument(
        "--only-missing-wh",
        action="store_true",
        help="Print step: only process rows that still have any blank Width 1-4",
    )
    p.add_argument(
        "--shirts-only",
        action="store_true",
        help="Print step: only t-shirt / polo / M-T W-T K-T rows",
    )
    p.add_argument(
        "--w1-blank",
        action="store_true",
        help="Print step: only rows with blank Width 1 (mm)",
    )
    p.add_argument(
        "--iloc-from",
        type=int,
        default=None,
        metavar="N",
        help="Only fill rows from this 0-based index to the end (appended block).",
    )
    p.add_argument(
        "--overwrite-pe-taxonomy",
        action="store_true",
        help=(
            "PE step: overwrite Category, Sub-Category, Department, "
            "Sub-Department from current PE (after Department/Sub Department corrections). "
            "Brand stays blank-only."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report counts; do not write Excel",
    )
    p.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip timestamped backup before write",
    )
    p.add_argument(
        "--sheet",
        default=SHEET,
        help=f"Excel sheet name (default: {SHEET})",
    )
    return p.parse_args(argv)



def main(argv: list[str] | None = None) -> int:
    return run_fill(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
