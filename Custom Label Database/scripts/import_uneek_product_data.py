"""
Import Uneek Product Data.xlsx into Custom_Label_Database.csv.

Source: database/shared/uneek_product_data/Uneek_Product_Data.xlsx
- Custom Label / Supplier SKU ← Short Code
- Apparel Image ← stem of Large Colour Image URL (file downloaded into Apparel Images/)
- Other mapped columns filled from the Uneek sheet (upsert by Custom Label).

  python scripts/import_uneek_product_data.py
  python scripts/import_uneek_product_data.py --dry-run
  python scripts/import_uneek_product_data.py --no-download
"""
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

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from shared import paths as wh

UNEEK_XLSX = wh.uneek_product_data_path()
_IMAGE_COL = "Large Colour Image"

# Uneek column → CL column (direct copies)
_DIRECT = {
    "Colour": "Colour",
    "Size": "Size",
    "Category": "Category",
    "Length (cm)": "Length (cm)",
    "Width (cm)": "Width (cm)",
    "Height (cm)": "Height (cm)",
    "Weight (g)": "Weight (g)",
    "Outer Packaging": "Outer Packaging",
    "Inner Packaging": "Inner Packaging",
    "Package Type": "Package Type",
}


def _cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()


def _stem_from_url(url: str) -> str:
    if not url:
        return ""
    path = unquote(urlparse(url).path)
    name = Path(path).name
    if not name:
        return ""
    return Path(name).stem


def _ext_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    suf = Path(path).suffix.lower()
    return suf if suf in {".jpg", ".jpeg", ".png", ".webp", ".gif"} else ".jpg"


def _request_url(url: str) -> str:
    """Quote path spaces so CDN fetch succeeds; keep scheme/netloc intact."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    path = quote(unquote(parsed.path), safe="/")
    return parsed._replace(path=path).geturl()


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-download", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--xlsx", type=Path, default=UNEEK_XLSX)
    args = ap.parse_args()

    if not args.xlsx.exists():
        print(f"Missing Uneek file: {args.xlsx}", flush=True)
        return 1

    print(f"Loading {args.xlsx} ...", flush=True)
    uneek_rows = load_uneek_rows(args.xlsx)
    print(f"Uneek rows: {len(uneek_rows):,}", flush=True)

    cl_path = wh.cl_csv_path()
    with open(cl_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    by_label: dict[str, int] = {}
    for i, r in enumerate(rows):
        lab = (r.get("Custom Label") or "").strip().casefold()
        if lab and lab not in by_label:
            by_label[lab] = i

    added = 0
    updated = 0
    url_by_stem: dict[str, str] = {}

    for u in uneek_rows:
        fields = uneek_to_cl_fields(u)
        short = fields["Custom Label"]
        key = short.casefold()
        url = u.get(_IMAGE_COL) or ""
        stem = fields.get("Apparel Image") or ""
        if stem and url and stem not in url_by_stem:
            url_by_stem[stem] = url

        if key in by_label:
            row = rows[by_label[key]]
            changed = False
            for col, val in fields.items():
                if col not in fieldnames:
                    continue
                if col == "Custom Label":
                    continue
                if (row.get(col) or "") != val:
                    row[col] = val
                    changed = True
            if changed:
                updated += 1
        else:
            row = {c: "" for c in fieldnames}
            for col, val in fields.items():
                if col in row:
                    row[col] = val
            rows.append(row)
            by_label[key] = len(rows) - 1
            added += 1

    print(
        f"Would add={added:,} update={updated:,} unique {_IMAGE_COL} images={len(url_by_stem):,}",
        flush=True,
    )

    if args.dry_run:
        print("Dry-run: no write / download.", flush=True)
        return 0

    if not args.no_backup:
        backups = wh.cl_backups_dir()
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backups / f"{cl_path.stem}_preFill_{stamp}{cl_path.suffix}"
        shutil.copy2(cl_path, backup)
        print(f"Backup: {backup}", flush=True)

    with open(cl_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {cl_path} ({len(rows):,} rows)", flush=True)

    if args.no_download:
        print("Skipped image download.", flush=True)
        return 0

    apparel_dir = wh.images_apparel_dir()
    apparel_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[str, Path]] = []
    for stem, url in sorted(url_by_stem.items()):
        dest = apparel_dir / f"{stem}{_ext_from_url(url)}"
        jobs.append((url, dest))

    print(f"Downloading {len(jobs)} {_IMAGE_COL} file(s) -> {apparel_dir}", flush=True)
    ok = fail = skip = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(download_one, url, dest): dest.stem for url, dest in jobs}
        for fut in as_completed(futs):
            stem, success, detail = fut.result()
            if detail == "exists":
                skip += 1
            elif success:
                ok += 1
            else:
                fail += 1
                print(f"  FAIL {stem}: {detail}", flush=True)
    print(
        f"Images: saved={ok} existed={skip} failed={fail} in {time.time()-t0:.1f}s",
        flush=True,
    )
    print(f"Summary: added={added:,} updated={updated:,}", flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
