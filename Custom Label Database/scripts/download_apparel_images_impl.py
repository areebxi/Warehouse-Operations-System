from __future__ import annotations
import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
from shared import paths as wh  # noqa: E402

def download_one(url: str, out_path: Path, timeout: int = 120) -> tuple[str, str]:
    """Returns (status, detail) status in ok|skip|fail."""
    if out_path.exists() and out_path.stat().st_size > 0:
        return "skip", str(out_path.name)
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CustomLabelDatabase/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        tmp.replace(out_path)
        return "ok", str(out_path.name)
    except Exception as e:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return "fail", f"{out_path.name} :: {url} :: {e}"
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
def build_download_plan(db: pd.DataFrame, pe: pd.DataFrame) -> pd.DataFrame:
    """One row per Apparel Image name (first URL wins)."""
    db = db.copy()
    db["UID"] = db["Custom Label"].map(extract_uid)
    db["url"] = db["UID"].map(pe[COLOUR_IMAGE_COL]).fillna("")
    usable = (
        db["Apparel Image"].ne("")
        & db["url"].ne("")
        & db["url"].str.startswith(("http://", "https://"))
    )
    plan = (
        db.loc[usable, ["Apparel Image", "url", "Custom Label", "UID"]]
        .drop_duplicates("Apparel Image", keep="first")
        .reset_index(drop=True)
    )
    return plan
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
def url_extension(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path
        ext = Path(path).suffix
        if ext and len(ext) <= 5:
            return ext.lower()
    except Exception:
        pass
    return ".jpg"
def extract_uid(custom_label: str) -> str:
    m = RE_UID.search(custom_label or "")
    return m.group(1) if m else ""
def clean(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip()
