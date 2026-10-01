"""Paths, constants, and shared helpers for fill_from_seeds."""
from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
_WAREHOUSE = SCRIPT_DIR.parent.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

BASE = SCRIPT_DIR.parent  # app folder (code only)
SUPPORT = wh.custom_label_support_dir()
BACKUPS = wh.cl_backups_dir()

DEFAULT_DB = wh.cl_csv_path()
DEFAULT_PE = wh.btc_product_data_path()
DEFAULT_CONFIG = SUPPORT / "Size References.csv"
DEFAULT_PRINT_SIZES = SUPPORT / "Shirts Print Sizes.csv"

BTC_SUPPLIER = "BTC Activewear"
POCKET_WH = (80, 100)
MAX_SLOTS = 4
SHEET = "Data"

RE_MOCK = re.compile(r"\(M(\d+)\)", re.I)
RE_UID = re.compile(r"-(\d+)$")
RE_P_PERSONAL = re.compile(r"(?:^|-)P\d+-", re.I)
RE_CRLF = re.compile(r"[\r\n]+")

ALL_STEPS = ("sku", "pe", "suppliers", "image", "print", "customise", "areeb", "supply", "printing_type", "supplier_name")

# Supplier Name keyword -> (SKU col, Product Code col, Stock col)
DEDICATED_SUPPLIERS = (
    ("btc", "BTC SKU", "BTC Product Code", "BTC Supplier Stock"),
    ("ralawise", "Ralawise SKU", "Ralawise Product Code", "Ralawise Supplier Stock"),
    ("absolute", "Absolute SKU", "Absolute Product Code", "Absolute Supplier Stock"),
)


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return RE_CRLF.sub(" ", s).strip()


def to_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        n = float(s)
        if n != n:
            return None
        return int(n) if n == int(n) else n
    except (TypeError, ValueError):
        return None


def mm_str(val) -> str:
    if val is None or val == "":
        return ""
    return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)


def uid_from_custom_label(label: str) -> str:
    """Last numeric segment: M260-P6-349876 -> 349876.

    Skip C800T age tokens (``M281-P5-C800T-30-18-24`` ends in 24, not a PE UID).
    Skip DTF gang-sheet labels (``Transfer-1M-1`` ends in 1, not a PE UID).
    Whole-label digits (``208544``) are a BTC UID with no dash.
    """
    s = clean(label)
    if not s or "C800T" in s.upper() or "TRANSFER" in s.upper():
        return ""
    if s.isdigit():
        return s
    m = RE_UID.search(s)
    return m.group(1) if m else ""


def customise_for_label(label: str) -> str:
    """Personalised => Yes: ``-P{digit}-``, leading ``P{digit}-``, or a ``Yes`` token.

    Supervisor (4 Sep 2026): any ``Yes`` in our SKU/Custom Label means personalised
    (e.g. ``W101-SkyBe-O/S-Yes``, ``M-T-NAVBE-3XL-Yes``), not only ``-P#-``.
    Leading ``P5-ACPPLQ-…`` is the same P-token when the mock prefix is omitted.
    Supervisor (22 Sep 2026): size-only acrylic listing SKU ``A515`` (whole label
    ``A[4-6]`` + two digits) is always personalised. ``A515-PHOTO`` is not this path.
    """
    s = clean(label)
    if not s:
        return ""
    if RE_P_PERSONAL.search(s):
        return "Yes"
    # Exact Yes segment (dash or slash separators), case-insensitive
    if any(p.casefold() == "yes" for p in re.split(r"[-/]", s) if p):
        return "Yes"
    if re.fullmatch(r"A[4-6]\d{2}", s, re.I):
        return "Yes"
    return ""



def hyphen_tshirt_in_slug(slug: str) -> str:
    """Apparel Image token is T-Shirt, never TShirt."""
    return (slug or "").replace("TShirt", "T-Shirt")


def apparel_image_slug(gender_apparel: str, colour: str) -> str:
    """Maker-style GA+Colour slug; letters/digits/dash only (blank cells only)."""

    def part(s: str) -> str:
        s = re.sub(r"\s+", "-", (s or "").strip())
        s = re.sub(r"[^A-Za-z0-9-]+", "-", s)
        s = re.sub(r"-+", "-", s)
        return s.strip("-")

    g, c = part(gender_apparel), part(colour)
    if not g and not c:
        return ""
    if not g:
        return hyphen_tshirt_in_slug(c)
    if not c:
        return hyphen_tshirt_in_slug(g)
    return hyphen_tshirt_in_slug(f"{g}-{c}")


def extract_mock(pp: str) -> str:
    m = RE_MOCK.search(pp)
    return f"M{m.group(1)}" if m else ""


def split_positions(pp: str) -> list[str]:
    pp = RE_MOCK.sub("", pp)
    parts = re.split(r"\s*,\s*|\s*&\s*", pp)
    return [p.strip() for p in parts if p.strip()]


def write_db(df: pd.DataFrame, db_path: Path, sheet: str, *, no_backup: bool) -> None:
    """Backup (unless no_backup) then write CSV/Excel; fallback file if locked."""
    if not no_backup:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        BACKUPS.mkdir(parents=True, exist_ok=True)
        backup = BACKUPS / f"{db_path.stem}_preFill_{stamp}{db_path.suffix}"
        print(f"\nBackup -> {backup}", flush=True)
        shutil.copy2(db_path, backup)
    print(f"Writing {db_path} ...", flush=True)
    try:
        if db_path.suffix.lower() == ".csv":
            df.to_csv(db_path, index=False)
        else:
            df.to_excel(db_path, sheet_name=sheet, index=False)
        print("Done.", flush=True)
    except PermissionError:
        fallback = db_path.with_name(db_path.stem + "_write_fallback" + db_path.suffix)
        print(f"  live file locked, writing fallback -> {fallback}", flush=True)
        if db_path.suffix.lower() == ".csv":
            df.to_csv(fallback, index=False)
        else:
            df.to_excel(fallback, sheet_name=sheet, index=False)
        print(
            "Done (fallback). Close the live CSV in Excel/Cursor and I can replace it.",
            flush=True,
        )
