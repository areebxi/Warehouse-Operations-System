"""Build download plan and fetch one apparel image."""
from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from download_apparel_load import COLOUR_IMAGE_COL, extract_uid


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
    return (
        db.loc[usable, ["Apparel Image", "url", "Custom Label", "UID"]]
        .drop_duplicates("Apparel Image", keep="first")
        .reset_index(drop=True)
    )


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
