from __future__ import annotations
import re
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

def g1_format(text: str) -> str:
    """Title-case PE department strings, preserving hyphenated parts."""
    if not text:
        return text
    words = text.split()
    out: list[str] = []
    for word in words:
        if "-" in word:
            out.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)
def apparel_image_slug(gender_apparel: str, colour: str) -> str:
    """Gender Apparel + Colour with spaces as dashes, no double dashes."""
    combined = f"{gender_apparel} {colour}".strip()
    if not combined:
        return ""
    slug = re.sub(r"\s+", "-", combined)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
def resolve_pe_uid(row: pd.Series) -> str:
    sku = row.get("sku", "")
    if sku and sku in pe_index.index:
        return sku
    suffix = row.get("suffix", "")
    if not row.get("sku", "") and suffix and suffix in pe_index.index:
        return suffix
    return ""
def load_pe() -> pd.DataFrame:
    pe = pd.read_excel(PE_PATH, sheet_name="staff", dtype=str)
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = pe[c].fillna("").astype(str).str.strip()
    return pe.drop_duplicates("UID").set_index("UID", drop=False)
