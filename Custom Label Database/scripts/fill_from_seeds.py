"""
Reusable filler for Custom Label Database.csv (preferred) or .xlsx

Use when you add rows with seed columns only:
  Custom Label, Gender Apparel, Colour, Size, Apparel Image,
  Print Positions, Customise

Fills what it can:
  1) Supplier SKU  <- last numeric UID from Custom Label
        (M260-214332 / M261-P4-24786 -> 214332 / 24786)
  2) ProductExport enrich: Supplier Name, SPC, Brand (blank only);
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
  python scripts/fill_from_seeds.py --steps sku,pe,suppliers,image,print
  python scripts/fill_from_seeds.py --steps print --only-missing-wh
  python scripts/fill_from_seeds.py --iloc-from 124109
  python scripts/fill_from_seeds.py --steps sku,pe --overwrite-pe-taxonomy --dry-run
  python scripts/fill_from_seeds.py --no-backup
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

# Allow `python scripts/fill_from_seeds.py` imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from size_code_logic import (  # noqa: E402
    load_overrides,
    load_size_ref_index,
    resolve_print_dims,
)

# ---------------------------------------------------------------------------
# Paths — CL app CSV + support/ + data/product_export
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
_WAREHOUSE = SCRIPT_DIR.parent.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

BASE = SCRIPT_DIR.parent  # app folder (code only)
SUPPORT = wh.custom_label_support_dir()
BACKUPS = wh.cl_backups_dir()

DEFAULT_DB = wh.cl_csv_path()
DEFAULT_PE = wh.product_export_path()
DEFAULT_CONFIG = SUPPORT / "Size References.csv"
DEFAULT_PRINT_SIZES = SUPPORT / "Shirts Print Sizes.csv"

BTC_SUPPLIER = "BTC Activewear"
POCKET_WH = (80, 100)
MAX_SLOTS = 4
SHEET = "Data"

RE_MOCK = re.compile(r"\(M(\d+)\)", re.I)
RE_UID = re.compile(r"-(\d+)$")
RE_P_PERSONAL = re.compile(r"-P\d+-", re.I)
RE_CRLF = re.compile(r"[\r\n]+")

# DB Size aliases -> Shirts Print Sizes.csv "Apparel Size" key
AGE_TO_PRINT = {
    "1-2 Years": "1-2 Years",
    "1-2Y": "1-2 Years",
    "2-3 Years": "2-3 Years",
    "2-3Y": "2-3 Years",
    "3-4 Years": "3-4 Years/YXS",
    "3-4Y": "3-4 Years/YXS",
    "3-4 Years/YXS": "3-4 Years/YXS",
    "3-4Y/YXS": "3-4 Years/YXS",
    "YXS": "3-4 Years/YXS",
    "5-6 Years": "5-6 Years/YS",
    "5-6Y": "5-6 Years/YS",
    "5-6 Years/YS": "5-6 Years/YS",
    "5-6Y/YS": "5-6 Years/YS",
    "YS": "5-6 Years/YS",
    "7-8 Years": "7-8 Years/YM",
    "7-8Y": "7-8 Years/YM",
    "7-8 Years/YM": "7-8 Years/YM",
    "7-8Y/YM": "7-8 Years/YM",
    "YM": "7-8 Years/YM",
    "9-11 Years": "9-11 Years/YL",
    "9-11Y": "9-11 Years/YL",
    "9-11 Years/YL": "9-11 Years/YL",
    "9-11Y/YL": "9-11 Years/YL",
    "YL": "9-11 Years/YL",
    "12-13 Years": "12-13 Years/YXL",
    "12-13Y": "12-13 Years/YXL",
    "12-13 Years/YXL": "12-13 Years/YXL",
    "12-13Y/YXL": "12-13 Years/YXL",
    "YXL": "12-13 Years/YXL",
}

AGE_TO_SR = {
    "1-2 Years": "1-2Y",
    "1-2Y": "1-2Y",
    "2-3 Years": "2-3Y",
    "2-3Y": "2-3Y",
    "3-4 Years": "3-4Y",
    "3-4Y": "3-4Y",
    "5-6 Years": "5-6Y",
    "5-6Y": "5-6Y",
    "7-8 Years": "7-8Y",
    "7-8Y": "7-8Y",
    "9-11 Years": "9-11Y",
    "9-11Y": "9-11Y",
    "12-13 Years": "12-13Y",
    "12-13Y": "12-13Y",
    "12-14 Years": "14-15Y",
    "14-15 Years": "14-15Y",
    "14-15Y": "14-15Y",
}

LETTER_TO_SR = {
    "Extra Small": "XS",
    "XS": "XS",
    "Small": "Small",
    "S": "Small",
    "Medium": "Medium",
    "M": "Medium",
    "Large": "Large",
    "L": "Large",
    "Extra Large": "XL",
    "XL": "XL",
    "2XL": "2XL",
    "XXL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

LETTER_TO_MEN_PRINT = {
    "Extra Small": "Small",
    "XS": "Small",
    "Small": "Small",
    "S": "Small",
    "Medium": "Medium",
    "M": "Medium",
    "Large": "Large",
    "L": "Large",
    "Extra Large": "XL",
    "XL": "XL",
    "2XL": "2XL",
    "XXL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

RE_SHIRT_GA = re.compile(
    r"t-?shirt|\btee\b|\bpolo\b|hoodie|sweat|\btank\b|"
    r"original t\b|iconic \d+ t\b|valueweight t\b",
    re.I,
)
RE_NOT_SHIRT_GA = re.compile(
    r"bag|tote|apron|beanie|\bhat\b|\bcap\b|iron.?on|"
    r"romper|bodysuit|waistcoat|sticker|\bmug\b|\bmask\b",
    re.I,
)
RE_SHIRT_SKU = re.compile(r"(^|-)[MWK]-T(-|$)", re.I)

PE_AGE = {
    "1-2": "1-2Y",
    "2-3": "2-3Y",
    "3-4": "3-4Y",
    "5-6": "5-6Y",
    "7-8": "7-8Y",
    "9-11": "9-11Y",
    "12-13": "12-13Y",
    "14-15": "14-15Y",
}

SUFFIX_TO_NAME = {
    "P": "Front Left Pocket",
    "F": "Front Center",
    "B": "Back Center",
    "S": "Sleeve",
    "S-1": "Sleeve",
}

KNOWN_HUMAN = {
    "front center",
    "back center",
    "front left pocket",
    "front right pocket",
    "front bottom left corner",
    "front bottom right corner",
    "right sleeve",
    "sleeve",
    "inside",
}

ALL_STEPS = ("sku", "pe", "suppliers", "image", "print", "customise")

# Supplier Name keyword -> (SKU col, Product Code col, Stock col)
DEDICATED_SUPPLIERS = (
    ("btc", "BTC SKU", "BTC Product Code", "BTC Supplier Stock"),
    ("ralawise", "Ralawise SKU", "Ralawise Product Code", "Ralawise Supplier Stock"),
    ("absolute", "Absolute SKU", "Absolute Product Code", "Absolute Supplier Stock"),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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
    """Last numeric segment: M260-P6-349876 -> 349876."""
    m = RE_UID.search(clean(label))
    return m.group(1) if m else ""


def customise_for_label(label: str) -> str:
    """-P{digit}- in Custom Label => personalised (Yes); else blank."""
    return "Yes" if RE_P_PERSONAL.search(clean(label)) else ""


def g1_format(text: str) -> str:
    if not text:
        return text
    out: list[str] = []
    for word in text.split():
        if "-" in word:
            out.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)


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
        return c
    if not c:
        return g
    return f"{g}-{c}"


def extract_mock(pp: str) -> str:
    m = RE_MOCK.search(pp)
    return f"M{m.group(1)}" if m else ""


def split_positions(pp: str) -> list[str]:
    pp = RE_MOCK.sub("", pp)
    parts = re.split(r"\s*,\s*|\s*&\s*", pp)
    return [p.strip() for p in parts if p.strip()]


def is_age_size(size: str) -> bool:
    s = size.lower()
    return (
        "year" in s
        or size in PE_AGE
        or size in AGE_TO_PRINT
        or size in AGE_TO_SR
        or bool(re.match(r"^\d+-\d+y", s, re.I))
    )


def sr_gender(gender_apparel: str, size: str) -> str:
    if is_age_size(size):
        return "Kids"
    g = gender_apparel.lower()
    if any(x in g for x in ("kid", "child", "youth", "junior", "infant", "baby", "toddler")):
        return "Kids"
    if any(x in g for x in ("women", "woman", "ladies", "lady", "girl", "female")):
        return "Women"
    return "Men"


def map_sr_size(size: str) -> str:
    if size in AGE_TO_SR:
        return AGE_TO_SR[size]
    if size in LETTER_TO_SR:
        return LETTER_TO_SR[size]
    if size in PE_AGE:
        return PE_AGE[size]
    return size


def map_print_sizes_key(size: str) -> str:
    s = clean(size)
    if not s:
        return ""
    lower = s.lower()
    for src, dest in AGE_TO_PRINT.items():
        if src.lower() == lower:
            return dest
    for src, dest in LETTER_TO_MEN_PRINT.items():
        if src.lower() == lower:
            return dest
    if s in PE_AGE:
        age_sr = PE_AGE[s]
        return AGE_TO_PRINT.get(age_sr, AGE_TO_PRINT.get(age_sr + " Years", ""))
    return ""


def is_shirt_row(gender_apparel: str, custom_label: str, size: str = "") -> bool:
    """All shirt kinds (tee/polo/hoodie/sweat/tank) or a mappable Size band."""
    ga = clean(gender_apparel)
    if RE_NOT_SHIRT_GA.search(ga):
        return False
    if map_print_sizes_key(size):
        return True
    if RE_SHIRT_GA.search(ga):
        return True
    return bool(RE_SHIRT_SKU.search(clean(custom_label)))


def has_exact_mock_uid(custom_label: str, size_index) -> bool:
    m = re.match(r"^(M\d+)-(\d+)$", clean(custom_label).upper())
    if not m:
        return False
    key = f"{m.group(1)} ({m.group(2)})"
    return key in size_index.by_exact_sku


def classify(name: str) -> str:
    """Classify a position name. Kebab-case front/back/pocket still classifies."""
    n = name.lower().strip()
    if not n:
        return "empty"
    if "sleeve" in n or "corner" in n or n == "inside":
        return "other"
    if "pocket" in n or "chest" in n:
        return "pocket"
    if "back" in n:
        return "back"
    if "front" in n:
        return "front"
    return "other"


def infer_printing_position(pos_list: list[str]) -> str:
    kinds = [classify(p) for p in pos_list]
    has_p = "pocket" in kinds
    has_f = "front" in kinds
    has_b = "back" in kinds
    if has_p and has_b:
        return "Left Chest & Back Print"
    if has_f and has_b:
        return "Front & Back Print"
    if has_p:
        return "Left Chest"
    if has_b and not has_f:
        return "Back Print"
    if has_f:
        return "Front Print"
    return ""


def paper_from_printing_size(val: str) -> str:
    s = (val or "").upper()
    if "A3" in s:
        return "A3"
    if "A4" in s:
        return "A4"
    return "A4"


def suffix_name(suffix: str, printing_position: str) -> str:
    suf = (suffix or "").upper()
    if suf in SUFFIX_TO_NAME:
        return SUFFIX_TO_NAME[suf]
    pp = (printing_position or "").strip()
    if pp == "Left Chest":
        return "Front Left Pocket"
    if pp == "Front Print":
        return "Front Center"
    if pp == "Back Print":
        return "Back Center"
    return ""


def kinds_in(names: list[str]) -> set[str]:
    return {classify(n) for n in names if n}


def normalize_gender_apparel_for_sr_sku(gender_apparel: str) -> list[str]:
    s = clean(gender_apparel).upper()
    if not s:
        return []
    cands: list[str] = []
    if s.endswith("-BS") and len(s) > 3:
        base = s[: -len("-BS")]
        if base and base != s:
            cands.append(base)
    if s.startswith("BG-") and len(s) > len("BG-"):
        cands.append(s.replace("BG-", "", 1))
        remainder = s.replace("BG-", "", 1)
        if "CHINA" in remainder and "BAG" in remainder:
            cands.append("BG-" + remainder.replace("-", ""))
    out: list[str] = []
    seen: set[str] = set()
    for x in cands:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
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


def load_pe_sizes(pe_path: Path) -> dict[str, str]:
    pe = _read_pe_table(pe_path, usecols=["UID", "Size"])
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    out: dict[str, str] = {}
    for uid, size in zip(pe["UID"].map(clean), pe["Size"].map(clean)):
        if uid and uid not in out:
            out[uid] = size
    return out


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


def _block_from_rows(rows: list[dict]) -> dict:
    n_designs = 1
    for r in rows:
        nd = r.get("n_designs")
        if nd:
            n_designs = int(nd)
            break
    return {
        "n_designs": n_designs,
        "printing_position": rows[0].get("printing_position", "") if rows else "",
        "printing_size": next((r["printing_size"] for r in rows if r.get("printing_size")), ""),
        "mock": rows[0].get("mock", "") if rows else "",
        "sku_value": rows[0].get("sku_value", "") if rows else "",
        "rows": rows,
        "source": "",
    }


def load_size_ref(config_path: Path) -> tuple[dict, dict, dict, dict]:
    if config_path.suffix.lower() == ".csv":
        sr = pd.read_csv(config_path, dtype=str)
    else:
        sr = pd.read_excel(config_path, sheet_name="Size References")
    mock_index: dict[tuple[str, str, str], list[dict]] = {}
    mock_inside_index: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    sku_index: dict[str, list[dict]] = defaultdict(list)
    pc_blocks: dict[tuple[str, str, str], dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for _, rec in sr.iterrows():
        sku_val = clean(rec.get("SKU Value"))
        suffix = clean(rec.get("Suffix"))
        gender = clean(rec.get("Gender"))
        size = clean(rec.get("Size"))
        ppos = clean(rec.get("Printing Position"))
        psize = clean(rec.get("Printing Size"))
        pcode = clean(rec.get("Product Code"))
        w = to_num(rec.get("Size Width"))
        h = to_num(rec.get("Size Height"))
        nd = to_num(rec.get("Number of Designs")) or 1
        mock_m = re.match(r"^(M\d+)", sku_val, re.I)
        mock = mock_m.group(1).upper() if mock_m else ""

        mock_paren_m = re.match(r"^(M\d+)\s*\(([^)]+)\)", sku_val, re.I)
        mock_paren = mock_paren_m.group(1).upper() if mock_paren_m else ""
        inside_paren = clean(mock_paren_m.group(2)) if mock_paren_m else ""

        row = {
            "sku_value": sku_val,
            "suffix": suffix.upper(),
            "gender": gender,
            "size": size,
            "printing_position": ppos,
            "printing_size": psize,
            "w": int(w) if w is not None else None,
            "h": int(h) if h is not None else None,
            "n_designs": int(nd),
            "mock": mock,
        }
        if sku_val:
            sku_index[sku_val.upper()].append(row)
        if mock and size:
            key = (mock, gender, size)
            existing = mock_index.get(key)
            if existing is None:
                mock_index[key] = [row]
            else:
                sufs = {r["suffix"] for r in existing}
                if row["suffix"] not in sufs:
                    existing.append(row)
        if mock_paren and inside_paren and size:
            mock_inside_index[(mock_paren, inside_paren, gender, size)].append(row)
        if pcode and gender and size:
            for code in pcode.split("-"):
                code = code.strip()
                if code:
                    pc_blocks[(code, gender, size)][sku_val].append(row)

    pc_index: dict[tuple[str, str, str], list[dict]] = {}
    for key, by_sku in pc_blocks.items():
        blocks = [_block_from_rows(rows) for rows in by_sku.values() if rows]
        seen: set = set()
        uniq = []
        for b in blocks:
            sig = (
                b["mock"],
                b["printing_position"],
                paper_from_printing_size(b["printing_size"]),
                tuple((r["suffix"], r["w"], r["h"]) for r in b["rows"]),
            )
            if sig in seen:
                continue
            seen.add(sig)
            uniq.append(b)
        pc_index[key] = uniq

    mock_blocks = {k: _block_from_rows(v) for k, v in mock_index.items()}
    mock_inside_blocks = {k: _block_from_rows(v) for k, v in mock_inside_index.items()}
    for b in mock_blocks.values():
        b["source"] = "mock_only"
    for b in mock_inside_blocks.values():
        b["source"] = "mock_inside"
    return mock_blocks, mock_inside_blocks, sku_index, pc_index


def score_block(block: dict, wanted_pos: str) -> int:
    got = block.get("printing_position") or ""
    if not wanted_pos:
        return 1
    if got == wanted_pos:
        return 100
    if wanted_pos in got or got in wanted_pos:
        return 50
    if "Chest" in wanted_pos and "Chest" in got:
        return 40
    if "Front" in wanted_pos and "Front" in got:
        return 30
    if "Back" in wanted_pos and "Back" in got:
        return 20
    return 0


def pick_pc_block(blocks: list[dict], pos_list: list[str], mock: str) -> dict | None:
    if not blocks:
        return None
    if mock:
        mocked = [b for b in blocks if b.get("mock") == mock]
        if mocked:
            blocks = mocked
    wanted = infer_printing_position(pos_list)
    ranked = sorted(blocks, key=lambda b: score_block(b, wanted), reverse=True)
    return ranked[0] if ranked else None


def lookup_sr(
    mock: str,
    spc: str,
    custom_label: str,
    gender: str,
    sr_size: str,
    pos_list: list[str],
    mock_blocks: dict,
    mock_inside_blocks: dict,
    sku_index: dict,
    pc_index: dict,
    gender_apparel: str,
) -> dict | None:
    genders_try = [gender]
    if gender == "Women":
        genders_try.append("Men")
    if gender != "Kids" and is_age_size(sr_size):
        genders_try.append("Kids")
    if "" not in genders_try:
        genders_try.append("")

    ga_keys = normalize_gender_apparel_for_sr_sku(gender_apparel)

    inside = ""
    m_inside = re.search(r"-(?:P\d+-)?(\d+)$", clean(custom_label).upper())
    if m_inside:
        inside = m_inside.group(1)

    mock_eff = mock
    if not mock_eff:
        m_mock = re.match(r"^(M\d+)", clean(custom_label).upper(), flags=re.I)
        mock_eff = m_mock.group(1).upper() if m_mock else ""

    if mock_eff and sr_size and inside:
        for g in genders_try:
            b = mock_inside_blocks.get((mock_eff, inside, g, sr_size))
            if b:
                return b

    if mock and sr_size:
        for g in genders_try:
            b = mock_blocks.get((mock, g, sr_size))
            if b:
                return b

    for key in (spc.upper(), custom_label.upper(), *ga_keys):
        if key and key in sku_index:
            return _block_from_rows(sku_index[key])

    if spc and sr_size:
        for g in genders_try:
            blocks = pc_index.get((spc, g, sr_size))
            picked = pick_pc_block(blocks or [], pos_list, mock)
            if picked:
                return picked
    return None


# ---------------------------------------------------------------------------
# Fill steps
# ---------------------------------------------------------------------------
def step_customise(df: pd.DataFrame, counts: dict) -> None:
    """Customise from Custom Label: -P{digit}- => Yes; otherwise not Yes."""
    if "Customise" not in df.columns:
        df["Customise"] = ""
    for idx in df.index:
        label = clean(df.at[idx, "Custom Label"])
        if not label:
            continue
        expected = customise_for_label(label)
        current = clean(df.at[idx, "Customise"])
        if expected:
            if current != "Yes":
                df.at[idx, "Customise"] = "Yes"
                counts["customise_set_yes"] += 1
        elif current.lower() == "yes":
            df.at[idx, "Customise"] = ""
            counts["customise_cleared_yes"] += 1


def step_supplier_sku(df: pd.DataFrame, counts: dict) -> None:
    """Fill blank Supplier SKU from Custom Label UID suffix."""
    if "Supplier SKU" not in df.columns:
        df["Supplier SKU"] = ""
    uids = df["Custom Label"].map(uid_from_custom_label)
    cur = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    mask = cur.eq("") & uids.ne("")
    df.loc[mask, "Supplier SKU"] = uids[mask]
    counts["sku_filled"] = int(mask.sum())


def _pe_column(pe_index: pd.DataFrame, *names: str) -> str:
    """Resolve a PE header, ignoring hyphen/space/case."""
    def norm(s: str) -> str:
        return re.sub(r"[\s_\-]+", "", s).lower()

    by_norm = {norm(c): c for c in pe_index.columns}
    for name in names:
        if name in pe_index.columns:
            return name
        hit = by_norm.get(norm(name))
        if hit:
            return hit
    return ""


# DB column <- PE column. Title-case matches the existing Category fill.
PE_TAXONOMY = (
    ("Category", "Department", True),
    ("Sub-Category", "Sub Department", True),
    ("Department", "Department", True),
    ("Sub-Department", "Sub Department", True),
    ("Brand", "Brand", False),
)
# These four track PE Department / Sub Department. When PE is corrected, overwrite them.
PE_TAXONOMY_REFRESH = frozenset(
    {"Category", "Sub-Category", "Department", "Sub-Department"}
)


def step_pe_enrich(
    df: pd.DataFrame,
    pe_index: pd.DataFrame,
    counts: dict,
    overwrite_taxonomy: bool = False,
) -> None:
    """Fill Supplier Name / SPC / Brand (blank only) and PE taxonomy."""
    for col in (
        "Supplier Name",
        "Supplier Product Code",
        "Category",
        "Sub-Category",
        "Department",
        "Sub-Department",
        "Brand",
    ):
        if col not in df.columns:
            df[col] = ""

    sku = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    suffix = df["Custom Label"].map(uid_from_custom_label)

    pe_uids = []
    via_sku = 0
    via_suffix = 0
    for s, suf in zip(sku, suffix):
        if s and s in pe_index.index:
            pe_uids.append(s)
            via_sku += 1
        elif (not s) and suf and suf in pe_index.index:
            pe_uids.append(suf)
            via_suffix += 1
        else:
            pe_uids.append("")
    pe_uids_s = pd.Series(pe_uids, index=df.index)
    matched = pe_uids_s.ne("")
    counts["pe_matched"] = int(matched.sum())
    counts["pe_via_sku"] = via_sku
    counts["pe_via_suffix"] = via_suffix

    def pe_col(uid: str, col: str) -> str:
        if not uid or not col or col not in pe_index.columns:
            return ""
        val = pe_index.at[uid, col]
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return clean(val)

    pe_spc = pe_uids_s.map(lambda u: pe_col(u, "SPC"))

    mask = matched & df["Supplier Name"].eq("")
    df.loc[mask, "Supplier Name"] = BTC_SUPPLIER
    counts["supplier_name_filled"] = int(mask.sum())

    mask = matched & df["Supplier Product Code"].eq("") & pe_spc.ne("")
    df.loc[mask, "Supplier Product Code"] = pe_spc[mask]
    counts["spc_filled"] = int(mask.sum())

    pe_dept_col = _pe_column(pe_index, "Department")
    pe_sub_col = _pe_column(pe_index, "Sub Department", "Sub-Department")
    pe_brand_col = _pe_column(pe_index, "Brand")
    pe_src = {
        "Department": pe_dept_col,
        "Sub Department": pe_sub_col,
        "Brand": pe_brand_col,
    }

    for db_col, pe_name, title_case in PE_TAXONOMY:
        src = pe_src.get(pe_name, "")
        incoming = pe_uids_s.map(
            lambda u, c=src, tc=title_case: (
                g1_format(pe_col(u, c)) if tc else pe_col(u, c)
            )
            if c
            else ""
        )
        already = matched & df[db_col].ne("") & incoming.ne("")
        differ = already & (df[db_col] != incoming)
        counts[f"{db_col}_already_differs"] = int(differ.sum())
        blank_mask = matched & df[db_col].eq("") & incoming.ne("")
        if overwrite_taxonomy and db_col in PE_TAXONOMY_REFRESH:
            over_mask = differ
            df.loc[over_mask, db_col] = incoming[over_mask]
            df.loc[blank_mask, db_col] = incoming[blank_mask]
            counts[f"{db_col}_overwritten"] = int(over_mask.sum())
            counts[f"{db_col}_filled"] = int(blank_mask.sum())
        else:
            df.loc[blank_mask, db_col] = incoming[blank_mask]
            counts[f"{db_col}_filled"] = int(blank_mask.sum())
            counts[f"{db_col}_overwritten"] = 0
        counts[f"{db_col}_still_blank"] = int((df[db_col].map(clean) == "").sum())


def step_dedicated_suppliers(df: pd.DataFrame, counts: dict) -> None:
    """Copy generic supplier fields into BTC/Ralawise/Absolute columns by name."""
    needed = ["Supplier Name", "Supplier SKU", "Supplier Product Code", "Supplier Stock"]
    for col in needed:
        if col not in df.columns:
            df[col] = ""
    for _, sku_c, pc_c, stock_c in DEDICATED_SUPPLIERS:
        for c in (sku_c, pc_c, stock_c):
            if c not in df.columns:
                df[c] = ""

    name = df["Supplier Name"].fillna("").astype(str).str.strip()
    name_l = name.str.lower()
    sku = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    pc = df["Supplier Product Code"].fillna("").astype(str).str.strip()
    stock = df["Supplier Stock"].fillna("").astype(str).str.strip()

    for key, sku_c, pc_c, stock_c in DEDICATED_SUPPLIERS:
        match = name_l.str.contains(key, na=False)
        counts[f"suppliers_{key}_rows"] = int(match.sum())

        m = match & df[sku_c].eq("") & sku.ne("")
        df.loc[m, sku_c] = sku[m]
        counts[f"filled_{sku_c}"] = int(m.sum())

        m = match & df[pc_c].eq("") & pc.ne("")
        df.loc[m, pc_c] = pc[m]
        counts[f"filled_{pc_c}"] = int(m.sum())

        m = match & df[stock_c].eq("") & stock.ne("")
        df.loc[m, stock_c] = stock[m]
        counts[f"filled_{stock_c}"] = int(m.sum())


def step_apparel_image(df: pd.DataFrame, counts: dict) -> None:
    if "Apparel Image" not in df.columns:
        df["Apparel Image"] = ""
    has_both = df["Gender Apparel"].ne("") & df["Colour"].ne("")
    slugs = pd.Series(
        [
            apparel_image_slug(g, c)
            for g, c in zip(df["Gender Apparel"], df["Colour"])
        ],
        index=df.index,
    )
    mask = has_both & df["Apparel Image"].eq("") & slugs.ne("")
    df.loc[mask, "Apparel Image"] = slugs[mask]
    counts["apparel_image_filled"] = int(mask.sum())


def step_print_sizes(
    df: pd.DataFrame,
    size_index,
    overrides,
    ps_table: dict,
    counts: dict,
    only_missing_wh: bool,
    pe_sizes: dict | None = None,
    shirts_only: bool = False,
    w1_blank: bool = False,
) -> None:
    """
    Fill blank print sizes.
    Shirts (t-shirt / polo / M-T W-T K-T): Shirts Print Sizes A4 by size band
    (DB Size, else Product Export Size), unless Size References has an exact
    mock+UID row. Everything else: Size References size-code pipeline.
    Positions from Print Positions (CSV). Number of Designs drives slot count.
    """
    pos_cols = [f"Position {i} Name" for i in range(1, 5)]
    w_cols = [f"Width {i} (mm)" for i in range(1, 5)]
    h_cols = [f"Height {i} (mm)" for i in range(1, 5)]
    for c in pos_cols + w_cols + h_cols:
        if c not in df.columns:
            df[c] = ""
    if "Print Positions" not in df.columns:
        df["Print Positions"] = ""

    rows_n = len(df)
    cl = df["Custom Label"].tolist()
    pp_col = df["Print Positions"].tolist()
    size_col = (
        df["Size"].tolist() if "Size" in df.columns else [""] * rows_n
    )
    ga_col = (
        df["Gender Apparel"].tolist()
        if "Gender Apparel" in df.columns
        else [""] * rows_n
    )
    sku_col = (
        df["Supplier SKU"].tolist() if "Supplier SKU" in df.columns else [""] * rows_n
    )
    pe_sizes = pe_sizes or {}
    w1_list = df["Width 1 (mm)"].tolist() if "Width 1 (mm)" in df.columns else [""] * rows_n

    new_pos = {c: [""] * rows_n for c in pos_cols}
    new_w = {c: [""] * rows_n for c in w_cols}
    new_h = {c: [""] * rows_n for c in h_cols}

    # Process rows that still have any blank width slot (multi-design needs this)
    process_mask = [True] * rows_n
    if only_missing_wh:
        w_lists = [df[c].tolist() for c in w_cols]
        for i in range(rows_n):
            process_mask[i] = any(clean(w_lists[s][i]) == "" for s in range(4))
    for i in range(rows_n):
        if not process_mask[i]:
            continue
        if w1_blank and clean(w1_list[i]) != "":
            process_mask[i] = False
            continue
        if shirts_only and not is_shirt_row(ga_col[i], cl[i], size_col[i]):
            process_mask[i] = False

    for i in range(rows_n):
        if not process_mask[i]:
            counts["print_skipped_already_has_wh"] += 1
            continue
        if i and i % 20000 == 0:
            print(f"  print: {i:,}/{rows_n:,}", flush=True)

        label = cl[i]
        pp = clean(pp_col[i])
        result = resolve_print_dims(label, pp, size_index, overrides, max_slots=MAX_SLOTS)

        code = result["size_code"]
        if code:
            counts["size_code_extracted"] += 1
        else:
            counts["size_code_missing"] += 1
        if result["override"]:
            counts["override_contain_hit"] += 1
        if result["matched_rows"]:
            counts["size_ref_rows_matched"] += 1
        else:
            counts["size_ref_rows_unmatched"] += 1

        names = result["position_names"]
        whs = list(result["whs"])
        n_slots = result["n_slots"]

        if is_shirt_row(ga_col[i], label, size_col[i]):
            size_used = size_col[i]
            ps_key = map_print_sizes_key(size_used)
            if not ps_key and pe_sizes:
                uid = re.sub(r"\.0$", "", clean(sku_col[i]))
                if not uid:
                    uid = uid_from_custom_label(label)
                pe_size = pe_sizes.get(uid, "")
                if pe_size:
                    ps_key = map_print_sizes_key(pe_size)
                    if ps_key:
                        counts["used_pe_size"] += 1
            shirt_wh = None
            if ps_key and ps_key in ps_table:
                shirt_wh = ps_table[ps_key].get("A4")
            if shirt_wh:
                pos_for_kind = names if names else split_positions(pp)
                if not pos_for_kind:
                    pos_for_kind = ["Front Center"]
                while len(whs) < max(n_slots, len(pos_for_kind)):
                    whs.append((None, None))
                n_slots = max(n_slots, len(pos_for_kind))
                overlaid = False
                for slot, name in enumerate(pos_for_kind[:MAX_SLOTS]):
                    kind = classify(name)
                    if kind in ("front", "back"):
                        if slot >= len(whs):
                            whs.append(shirt_wh)
                        else:
                            whs[slot] = shirt_wh
                        overlaid = True
                if overlaid:
                    names = pos_for_kind
                    counts["wh_from_shirt_print_sizes"] += 1

        # Position names from Print Positions (blank fill only later)
        for slot, name in enumerate(names[:MAX_SLOTS]):
            new_pos[pos_cols[slot]][i] = name

        filled_any = False
        for slot in range(min(n_slots, MAX_SLOTS)):
            if slot >= len(whs):
                break
            w, h = whs[slot]
            if w is None or h is None:
                continue
            new_w[w_cols[slot]][i] = mm_str(w)
            new_h[h_cols[slot]][i] = mm_str(h)
            counts[f"wh_slot_{slot + 1}"] += 1
            filled_any = True

        if filled_any:
            counts["rows_with_wh"] += 1
        else:
            counts["rows_no_wh"] += 1

        counts["n_designs_slots_total"] += n_slots

    proc = pd.Series(process_mask, index=df.index)

    # Position names: blank only
    for c in pos_cols:
        incoming = pd.Series(new_pos[c], index=df.index)
        mask = proc & df[c].eq("") & incoming.ne("")
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())

    # Width/Height: blank only
    for c in w_cols + h_cols:
        incoming = pd.Series(
            new_w[c] if c in w_cols else new_h[c], index=df.index
        )
        mask = proc & df[c].eq("") & incoming.ne("")
        df.loc[mask, c] = incoming[mask]
        counts[f"filled_{c}"] = int(mask.sum())
        counts[f"blank_filled_{c}"] = int(mask.sum())

    counts["width1_now_filled"] = int((df["Width 1 (mm)"].map(clean) != "").sum())
    counts["pos1_now_filled"] = int((df["Position 1 Name"].map(clean) != "").sum())
    counts["width1_still_blank"] = int((df["Width 1 (mm)"].map(clean) == "").sum())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
    p.add_argument("--pe", type=Path, default=DEFAULT_PE, help="ProductExport CSV/XLSX")
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
        help="Comma list: sku,pe,suppliers,image,print,customise (default: all)",
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
    args = parse_args(argv)
    steps = tuple(s.strip().lower() for s in args.steps.split(",") if s.strip())
    unknown = [s for s in steps if s not in ALL_STEPS]
    if unknown:
        print(f"Unknown steps: {unknown}. Allowed: {ALL_STEPS}", file=sys.stderr)
        return 2

    db_path: Path = args.file.resolve()
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1
    for label, path in (
        ("ProductExport", args.pe),
        ("Size References", args.config),
        ("Shirts Print Sizes", args.print_sizes),
    ):
        if "pe" in steps and label == "ProductExport" and not path.exists():
            print(f"Missing {label}: {path}", file=sys.stderr)
            return 1
        if "print" in steps and label != "ProductExport" and not path.exists():
            print(f"Missing {label}: {path}", file=sys.stderr)
            return 1
        if (
            "print" in steps
            and label == "ProductExport"
            and args.shirts_only
            and not path.exists()
        ):
            print(f"Missing {label}: {path}", file=sys.stderr)
            return 1

    print(f"Loading DB: {db_path}", flush=True)
    if db_path.suffix.lower() == ".csv":
        df = pd.read_csv(db_path, dtype=str, low_memory=False)
    else:
        df = pd.read_excel(db_path, sheet_name=args.sheet, dtype=str)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()
    print(f"  rows={len(df):,} cols={len(df.columns)}", flush=True)

    work = df
    if args.iloc_from is not None:
        if args.iloc_from < 0 or args.iloc_from >= len(df):
            print(
                f"--iloc-from {args.iloc_from} out of range for {len(df)} rows",
                file=sys.stderr,
            )
            return 1
        work = df.iloc[args.iloc_from :].copy()
        print(f"  scoped to iloc[{args.iloc_from}:] -> {len(work)} rows", flush=True)

    counts: dict = defaultdict(int)

    if "sku" in steps:
        print("Step: supplier SKU from Custom Label UID...", flush=True)
        step_supplier_sku(work, counts)

    pe_index = None
    if "pe" in steps:
        print(f"Loading ProductExport: {args.pe}", flush=True)
        pe_index = load_pe_index(args.pe)
        print(f"  PE UIDs={len(pe_index):,}", flush=True)
        print("Step: ProductExport enrich...", flush=True)
        if args.overwrite_pe_taxonomy:
            print(
                "  overwrite Category / Sub-Category / Department / Sub-Department from PE",
                flush=True,
            )
        step_pe_enrich(
            work,
            pe_index,
            counts,
            overwrite_taxonomy=args.overwrite_pe_taxonomy,
        )

    if "suppliers" in steps:
        print("Step: dedicated supplier columns...", flush=True)
        step_dedicated_suppliers(work, counts)

    if "image" in steps:
        print("Step: Apparel Image slug...", flush=True)
        step_apparel_image(work, counts)

    if "print" in steps:
        print("Step: print sizes (shirts -> Print Sizes, else Size References)...", flush=True)
        print(f"  loading Size References + Override: {args.config}", flush=True)
        size_index = load_size_ref_index(args.config)
        overrides = load_overrides(args.config)
        print(f"  loading Shirts Print Sizes: {args.print_sizes}", flush=True)
        ps_table = load_print_sizes(args.print_sizes)
        pe_sizes: dict = {}
        if args.pe.exists():
            print(f"  loading PE sizes: {args.pe}", flush=True)
            pe_sizes = load_pe_sizes(args.pe)
            print(f"  PE size UIDs={len(pe_sizes):,}", flush=True)
        print(
            f"  SR bases={len(size_index.bases_longest_first)} "
            f"overrides={len(overrides)} shirt bands={len(ps_table)}",
            flush=True,
        )
        if args.shirts_only:
            print("  scoped to shirts only", flush=True)
        if args.w1_blank:
            print("  scoped to blank Width 1", flush=True)
        step_print_sizes(
            work,
            size_index,
            overrides,
            ps_table,
            counts,
            only_missing_wh=args.only_missing_wh,
            pe_sizes=pe_sizes,
            shirts_only=args.shirts_only,
            w1_blank=args.w1_blank,
        )

    if "customise" in steps:
        print("Step: Customise from Custom Label (-P{digit}- => Yes)...", flush=True)
        step_customise(work, counts)

    if args.iloc_from is not None:
        for c in work.columns:
            df.loc[work.index, c] = work[c]

    print("\n=== Counts ===", flush=True)
    for k in sorted(counts):
        print(f"  {k}: {counts[k]:,}", flush=True)

    if args.dry_run:
        print("\nDry run — no files written.", flush=True)
        return 0

    if not args.no_backup:
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
            df.to_excel(db_path, sheet_name=args.sheet, index=False)
        print("Done.", flush=True)
    except PermissionError:
        fallback = db_path.with_name(db_path.stem + "_write_fallback" + db_path.suffix)
        print(
            f"  live file locked, writing fallback -> {fallback}",
            flush=True,
        )
        if db_path.suffix.lower() == ".csv":
            df.to_csv(fallback, index=False)
        else:
            df.to_excel(fallback, sheet_name=args.sheet, index=False)
        print(
            "Done (fallback). Close the live CSV in Excel/Cursor and I can replace it.",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
