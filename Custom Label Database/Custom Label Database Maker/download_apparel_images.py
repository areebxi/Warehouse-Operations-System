"""
Download apparel images for Custom Label Database mock rows.

Uses ProductExport `colour image 01` as the URL.
Saves each file as the exact `Apparel Image` name (+ extension from URL).

Default scope: mock rows (Custom Label ^M\\d+) that were added by
generate_from_mocks (not present in the preGenerate backup). Use --all-mocks
for every M## row.

Example (from repo root or Maker folder):

  python "Custom Label Database Maker/download_apparel_images.py"
  python "Custom Label Database Maker/download_apparel_images.py" --all-mocks
  python "Custom Label Database Maker/download_apparel_images.py" --dry-run
"""
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

MAKER_DIR = Path(__file__).resolve().parent
REPO = MAKER_DIR.parent

DEFAULT_DB = REPO / "Custom_Label_Database.csv"
DEFAULT_PE_XLSX = REPO / "support" / "ProductExport.xlsx"
DEFAULT_PE_CSV = MAKER_DIR / "ProductExport.csv"
DEFAULT_OUT = MAKER_DIR / "Apparel Images"
DEFAULT_PRE_GENERATE = (
    REPO / "backups" / "Custom Label Database_preGenerate_20260820_171255.xlsx"
)

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
        pe = pd.read_csv(path, dtype=str, low_memory=False)
    else:
        pe = pd.read_excel(path, sheet_name="staff", dtype=str)
        if len(pe) and str(pe.iloc[0].get("UID", "")).startswith("["):
            pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = clean(pe[c])
    if "UID" not in pe.columns:
        raise SystemExit(f"ProductExport missing UID: {path}")
    if COLOUR_IMAGE_COL not in pe.columns:
        raise SystemExit(f"ProductExport missing '{COLOUR_IMAGE_COL}': {path}")
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


def download_one(url: str, out_path: Path, timeout: int = 120) -> tuple[str, str]:
    """Returns (status, detail) status in ok|skip|fail."""
    if out_path.exists() and out_path.stat().st_size > 0:
        return "skip", str(out_path.name)
    tmp = out_path.with_suffix(out_path.suffix + ".part")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CustomLabelDatabaseMaker/1.0"},
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


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Download mock Apparel Images from ProductExport colour image 01."
    )
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="Custom_Label_Database.csv")
    ap.add_argument(
        "--product",
        type=Path,
        default=None,
        help="ProductExport.xlsx or .csv (default: support/ProductExport.xlsx)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output folder (default: Maker/Apparel Images)",
    )
    ap.add_argument(
        "--all-mocks",
        action="store_true",
        help="Download for all M## rows (not only generate_from_mocks additions)",
    )
    ap.add_argument(
        "--pre-generate",
        type=Path,
        default=DEFAULT_PRE_GENERATE,
        help="Backup used to detect newly added mocks",
    )
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Max unique images (0=all)")
    args = ap.parse_args()

    pe_path = args.product
    if pe_path is None:
        pe_path = DEFAULT_PE_XLSX if DEFAULT_PE_XLSX.exists() else DEFAULT_PE_CSV
    if not args.db.exists():
        raise SystemExit(f"DB not found: {args.db}")
    if not pe_path.exists():
        raise SystemExit(f"ProductExport not found: {pe_path}")

    print(f"DB: {args.db}", flush=True)
    print(f"PE: {pe_path}", flush=True)
    print(f"Out: {args.out}", flush=True)

    db = pd.read_csv(
        args.db,
        dtype=str,
        low_memory=False,
        usecols=lambda c: c
        in ("Custom Label", "Apparel Image", "Supplier SKU", "Gender Apparel", "Colour"),
    )
    for c in db.columns:
        db[c] = clean(db[c])

    is_mock = db["Custom Label"].str.match(RE_MOCK, na=False)
    if args.all_mocks:
        scope = db.loc[is_mock].copy()
        print(f"Scope: all M## rows ({len(scope):,})", flush=True)
    else:
        old = load_existing_labels(args.pre_generate)
        if not old:
            print(
                "WARNING: pre-generate backup missing — falling back to all M## rows.",
                flush=True,
            )
            scope = db.loc[is_mock].copy()
        else:
            scope = db.loc[is_mock & ~db["Custom Label"].isin(old)].copy()
            print(
                f"Scope: newly added M## vs preGenerate ({len(scope):,} rows)",
                flush=True,
            )

    pe = load_pe(pe_path)
    plan = build_download_plan(scope, pe)
    if args.limit > 0:
        plan = plan.head(args.limit)

    no_url = (
        scope["Apparel Image"].ne("")
        & scope["Custom Label"].map(extract_uid).map(pe[COLOUR_IMAGE_COL]).fillna("").eq("")
    )
    print(f"Unique Apparel Image files to fetch: {len(plan):,}", flush=True)
    print(f"Scope rows missing PE colour image 01: {int(no_url.sum()):,}", flush=True)

    if args.dry_run:
        print("\nDry-run samples:", flush=True)
        for _, r in plan.head(8).iterrows():
            print(f"  {r['Apparel Image']}  <-  {r['url'][:70]}", flush=True)
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    ok = skip = fail = 0
    t0 = time.time()

    def job(row: pd.Series) -> tuple[str, str]:
        name = row["Apparel Image"]
        url = row["url"]
        ext = url_extension(url)
        # Exact Apparel Image name; do not re-sanitize
        out_path = args.out / f"{name}{ext}"
        return download_one(url, out_path)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {ex.submit(job, row): row["Apparel Image"] for _, row in plan.iterrows()}
        done = 0
        total = len(futures)
        for fut in as_completed(futures):
            done += 1
            status, detail = fut.result()
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                fail += 1
                failures.append(detail)
            if done % 25 == 0 or done == total:
                print(
                    f"  [{done}/{total}] ok={ok} skip={skip} fail={fail}",
                    flush=True,
                )

    elapsed = time.time() - t0
    print(
        f"\nDone in {elapsed:.1f}s — downloaded={ok} skipped={skip} failed={fail}",
        flush=True,
    )
    print(f"Images folder: {args.out}", flush=True)
    if failures:
        fail_path = args.out / "download-failures-colour-image-01.txt"
        fail_path.write_text("\n".join(failures) + "\n", encoding="utf-8")
        print(f"Failures logged: {fail_path}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
