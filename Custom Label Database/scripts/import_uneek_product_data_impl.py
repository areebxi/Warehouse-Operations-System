from __future__ import annotations
import argparse
import csv
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import openpyxl
import requests
from shared import paths as wh

def uneek_to_cl_fields(u: dict[str, str]) -> dict[str, str]:
    short = u["Short Code"]
    product = u.get("Product Name") or ""
    ga = f"Uneek {product}".strip() if product else "Uneek"
    url = u.get(_IMAGE_COL) or ""
    stem = _stem_from_url(url)
    fields = {
        "Custom Label": short,
        "Gender Apparel": ga,
        "Apparel Image": stem,
        "Brand": "Uneek",
        "Supplier Name": u.get("Company") or "Uneek Clothing",
        "Supplier Product Code": u.get("Product Code") or "",
        "Supplier SKU": short,
        "Department": u.get("Category") or "",
        "Print Positions": "",
        "Customise": "",
    }
    for src, dst in _DIRECT.items():
        if u.get(src):
            fields[dst] = u[src]
    return fields
def download_one(url: str, dest: Path, timeout: float = 60.0) -> tuple[str, bool, str]:
    """Return (stem, ok, detail)."""
    stem = dest.stem
    if dest.exists() and dest.stat().st_size > 0:
        return stem, True, "exists"
    try:
        resp = requests.get(
            _request_url(url),
            timeout=timeout,
            headers={"User-Agent": "WarehouseOperationsSystem/1.0"},
        )
        if not resp.ok:
            return stem, False, f"HTTP {resp.status_code}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(resp.content)
        tmp.replace(dest)
        return stem, True, f"saved {len(resp.content)} bytes"
    except Exception as exc:
        return stem, False, repr(exc)
def load_uneek_rows(path: Path) -> list[dict[str, str]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    header = [(_cell(h) if h is not None else "") for h in next(it)]
    out: list[dict[str, str]] = []
    for raw in it:
        row = {header[i]: _cell(raw[i]) if i < len(raw) else "" for i in range(len(header))}
        if not row.get("Short Code"):
            continue
        out.append(row)
    wb.close()
    return out
def _stem_from_url(url: str) -> str:
    if not url:
        return ""
    path = unquote(urlparse(url).path)
    name = Path(path).name
    if not name:
        return ""
    return Path(name).stem
def _request_url(url: str) -> str:
    """Quote path spaces so CDN fetch succeeds; keep scheme/netloc intact."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    path = quote(unquote(parsed.path), safe="/")
    return parsed._replace(path=path).geturl()
def _cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()
def _ext_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    suf = Path(path).suffix.lower()
    return suf if suf in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".jpg"
