"""Load PE / pre-generate labels for download_apparel_images."""
from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

import pandas as pd

RE_MOCK = re.compile(r"(?i)^M\d+")
RE_UID = re.compile(r"-(\d+)$")
COLOUR_IMAGE_COL = "colour image 01"


def clean(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip()


def extract_uid(custom_label: str) -> str:
    m = RE_UID.search(custom_label or "")
    return m.group(1) if m else ""


def url_extension(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path
        ext = Path(path).suffix
        if ext and len(ext) <= 5:
            return ext.lower()
    except Exception:
        pass
    return ".jpg"


def load_pe(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        # ponytail: PE is often Windows-1252; try utf-8 first then fall back
        last_err: Exception | None = None
        pe = None
        for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            try:
                pe = pd.read_csv(path, dtype=str, low_memory=False, encoding=enc)
                break
            except UnicodeDecodeError as e:
                last_err = e
        if pe is None:
            raise SystemExit(f"BTC Product Data decode failed: {path} ({last_err})")
    else:
        pe = pd.read_excel(path, sheet_name="staff", dtype=str)
        if len(pe) and str(pe.iloc[0].get("UID", "")).startswith("["):
            pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = clean(pe[c])
    if "UID" not in pe.columns:
        raise SystemExit(f"BTC Product Data missing UID: {path}")
    if COLOUR_IMAGE_COL not in pe.columns:
        raise SystemExit(f"BTC Product Data missing '{COLOUR_IMAGE_COL}': {path}")
    return pe.drop_duplicates("UID", keep="first").set_index("UID", drop=False)


def load_existing_labels(pre_generate: Path | None) -> set[str]:
    if pre_generate is None or not pre_generate.exists():
        return set()
    print(f"Loading pre-generate labels: {pre_generate}", flush=True)
    if pre_generate.suffix.lower() == ".csv":
        df = pd.read_csv(pre_generate, dtype=str, usecols=["Custom Label"], low_memory=False)
    else:
        try:
            df = pd.read_excel(
                pre_generate, sheet_name="Data", dtype=str, usecols=["Custom Label"]
            )
        except ValueError:
            df = pd.read_excel(pre_generate, dtype=str, usecols=["Custom Label"])
    return set(clean(df["Custom Label"]))
