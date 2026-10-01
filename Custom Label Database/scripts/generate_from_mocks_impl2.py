from __future__ import annotations
import argparse
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
import pandas as pd
from shared import paths as wh  # noqa: E402

def split_product_codes(raw: str) -> list[str]:
    """Split '61082-61430-61036' or '18000 / 18000B' into SPC tokens."""
    s = clean(raw)
    if not s or s.upper() in ("N/A", "NA"):
        return []
    # replace slash separators with hyphen-like splits
    s = s.replace("/", "-")
    parts = []
    for tok in re.split(r"[\s\-]+", s):
        tok = tok.strip()
        if tok and tok.upper() not in ("N/A", "NA"):
            parts.append(tok)
    return parts
def strip_special(text: str) -> str:
    """Remove special chars (™, &, apostrophe, etc.); keep dash/comma/basic punctuation."""
    s = clean(text)
    if not s:
        return ""
    s = s.replace("&", " and ")
    s = s.replace("*", " x ")
    s = RE_SPECIAL.sub("", s)
    s = re.sub(r" {2,}", " ", s).strip()
    s = re.sub(r"-{2,}", "-", s)
    return s.strip(" -")
def normalize_description(description: str) -> str:
    """Normalize PE Description for Gender Apparel (match existing FOTL-style names)."""
    desc = clean(description)
    if not desc:
        return ""
    desc = desc.replace("Men's", "Mens")
    desc = desc.replace("Kid's", "Kids")
    desc = desc.replace("Ladies'", "Ladies")
    desc = desc.replace("Women's", "Womens")
    return strip_special(desc)
def load_mocks(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str)
    # skip metadata rows: keep only Pasting Mocks ID like M01
    raw["Pasting Mocks ID"] = raw["Pasting Mocks ID"].map(clean)
    mocks = raw[raw["Pasting Mocks ID"].str.match(r"^M\d+$", na=False)].copy()
    # Prefer first occurrence of each mock ID (guide has some duplicate IDs later)
    mocks = mocks.drop_duplicates(subset=["Pasting Mocks ID"], keep="first")
    return mocks
def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return RE_CRLF.sub(" ", s).strip()
def apparel_image_slug(*parts: str) -> str:
    combined = " ".join(p for p in (strip_special(x) for x in parts) if p)
    if not combined:
        return ""
    slug = re.sub(r"\s+", "-", combined)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
def gender_apparel_from_pe(brand_code: str, description: str) -> str:
    """Gender Apparel = '{Brand Code} {Description}'."""
    code = strip_special(brand_code)
    desc = normalize_description(description)
    if not code or not desc:
        return ""
    return f"{code} {desc}".strip()
def normalize_colour(colour: str) -> str:
    c = strip_special(colour)
    if not c:
        return ""
    c = COLOUR_TYPOS.get(c, c)
    c = COLOUR_ABBREV.get(c, c)
    return c
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
def load_db(db_path: Path) -> pd.DataFrame:
    if db_path.suffix.lower() == ".csv":
        return pd.read_csv(db_path, dtype=str, low_memory=False)
    return pd.read_excel(db_path, sheet_name=SHEET, dtype=str)
