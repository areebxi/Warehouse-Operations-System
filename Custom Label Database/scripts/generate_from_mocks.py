"""
Generate Custom Label Database seed rows from the Mocks Database Guide.

Creates rows with ONLY these seed columns filled:
  Custom Label, Gender Apparel, Colour, Size, Apparel Image, Print Positions

Rules:
  - Custom Label = {Pasting Mocks ID}-{UID}  (e.g. M01-120877)
  - UID comes from ProductExport rows whose SPC matches a Product Code on the mock
  - Gender Apparel = "{Brand Code} {Description}" (Men's->Mens, Kid's->Kids, Ladies'->Ladies)
  - Colour / Size from ProductExport (with Phase-2 style size/colour normalize)
  - Apparel Image = slug(Gender Apparel + Colour)
  - Print Positions mapped from mock Printing Position
  - Skip entire mock IDs already present in the Custom Label Database
  - Skip any mock / UID where any of the 6 seed columns cannot be filled

Examples:

  python scripts/generate_from_mocks.py --dry-run
  python scripts/generate_from_mocks.py --mock M01,M03
  python scripts/generate_from_mocks.py
  python scripts/generate_from_mocks.py --no-backup
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
SUPPORT = BASE / "support"
BACKUPS = BASE / "backups"

DEFAULT_DB = BASE / "Custom_Label_Database.csv"
DEFAULT_PE = SUPPORT / "ProductExport.xlsx"
DEFAULT_MOCKS = SUPPORT / "14-01-Mocks Database Guide(01-Mocks Databse).csv"
SHEET = "Data"

SEED_COLS = [
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
]

SIZE_TO_WORD = {
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "XL": "Extra Large",
    "XS": "Extra Small",
}

AGE_BANDS = {
    "1-2",
    "2-3",
    "3-4",
    "5-6",
    "7-8",
    "9-11",
    "12-13",
    "12-14",
    "14-15",
}

COLOUR_TYPOS = {
    "Fuschia": "Fuchsia",
    "Colbalt Blue": "Cobalt Blue",
    "Sport Grey": "Sports Grey",
    "Light-Pink": "Light Pink",
}
COLOUR_ABBREV = {
    "Dark Heather": "Dark Heather Grey",
    "Azure": "Azure Blue",
}

# Mock Printing Position -> Print Positions cell (without mock suffix)
PRINT_POS_MAP = {
    "Front Print": "Front Center",
    "Back Print": "Back Center",
    "Left Chest": "Front Left Pocket",
    "Front & Back Print": "Front Center, Back Center",
    "Left Chest & Back Print": "Front Left Pocket, Back Center",
    "Front  Print with Both Sleeves": "Front Center, Sleeve",
    "Front Print with Both Sleeves": "Front Center, Sleeve",
    "Front & Back with Both Sleeves": "Front Center, Back Center, Sleeve",
    "Front & Back with Right Sleeve": "Front Center, Back Center, Right Sleeve",
    "Front & Back with Left Sleeve": "Front Center, Back Center, Sleeve",
    "Left Chest & Left Sleeves": "Front Left Pocket, Sleeve",
    "Left Neck & Left Sleeve Bottom": "Front Left Pocket, Sleeve",
    "Front Print & Inside Print": "Front Center, Inside",
    "Front Print & Front Pocket": "Front Center, Front Left Pocket",
}

RE_CRLF = re.compile(r"[\r\n]+")
RE_MOCK_ID = re.compile(r"^M\d+$", re.I)
# Letters, digits, space, dash, comma, (), /, ., +, # — strip ™ & ' etc.
RE_SPECIAL = re.compile(r"[^A-Za-z0-9 ,\-/().+#]")


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return RE_CRLF.sub(" ", s).strip()


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


def apparel_image_slug(*parts: str) -> str:
    combined = " ".join(p for p in (strip_special(x) for x in parts) if p)
    if not combined:
        return ""
    slug = re.sub(r"\s+", "-", combined)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


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


def gender_apparel_from_pe(brand_code: str, description: str) -> str:
    """Gender Apparel = '{Brand Code} {Description}'."""
    code = strip_special(brand_code)
    desc = normalize_description(description)
    if not code or not desc:
        return ""
    return f"{code} {desc}".strip()


def normalize_size(size: str) -> str:
    s = strip_special(size)
    if not s:
        return ""
    if s in SIZE_TO_WORD:
        return SIZE_TO_WORD[s]
    # PE age bands like 3-4 / 14-15
    if s in AGE_BANDS:
        return f"{s} Years"
    if re.fullmatch(r"\d+-\d+", s):
        return f"{s} Years"
    # already "3-4 Years"
    if s.endswith(" Years"):
        return s
    return s


def normalize_colour(colour: str) -> str:
    c = strip_special(colour)
    if not c:
        return ""
    c = COLOUR_TYPOS.get(c, c)
    c = COLOUR_ABBREV.get(c, c)
    return c


def map_print_positions(printing_position: str, mock_id: str) -> str:
    pp = clean(printing_position)
    # collapse odd double spaces for lookup
    key = re.sub(r"\s+", " ", pp).strip()
    mapped = PRINT_POS_MAP.get(pp) or PRINT_POS_MAP.get(key)
    if not mapped:
        # try fuzzy: normalize double spaces in key map
        for k, v in PRINT_POS_MAP.items():
            if re.sub(r"\s+", " ", k).strip() == key:
                mapped = v
                break
    if not mapped:
        return ""
    # Append (M###) when multi-slot (matches existing DB style for multi-position)
    if "," in mapped:
        return f"{mapped} ({mock_id})"
    return mapped


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


def load_mocks(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, dtype=str)
    # skip metadata rows: keep only Pasting Mocks ID like M01
    raw["Pasting Mocks ID"] = raw["Pasting Mocks ID"].map(clean)
    mocks = raw[raw["Pasting Mocks ID"].str.match(r"^M\d+$", na=False)].copy()
    # Prefer first occurrence of each mock ID (guide has some duplicate IDs later)
    mocks = mocks.drop_duplicates(subset=["Pasting Mocks ID"], keep="first")
    return mocks


def generate_rows(
    mocks: pd.DataFrame,
    pe: pd.DataFrame,
    skip_mock_ids: set[str],
    only_mocks: set[str] | None,
) -> tuple[pd.DataFrame, dict]:
    pe_by_spc: dict[str, pd.DataFrame] = {
        spc: grp for spc, grp in pe.groupby("SPC", sort=False) if clean(spc)
    }

    stats: dict = Counter()
    skip_reasons: dict[str, str] = {}
    rows: list[dict] = []

    for _, mock in mocks.iterrows():
        mock_id = clean(mock["Pasting Mocks ID"]).upper()
        if only_mocks and mock_id not in only_mocks:
            continue

        if mock_id in skip_mock_ids:
            stats["skipped_mock_already_in_db"] += 1
            skip_reasons[mock_id] = "mock already in Custom Label Database"
            continue

        product_code = clean(mock.get("Product Code", ""))
        printing_pos = clean(mock.get("Printing Position", ""))
        codes = split_product_codes(product_code)

        if not codes:
            stats["skipped_mock_no_product_code"] += 1
            skip_reasons[mock_id] = "no Product Code"
            continue

        pp = map_print_positions(printing_pos, mock_id)
        if not pp:
            stats["skipped_mock_no_print_pos"] += 1
            skip_reasons[mock_id] = f"unmapped/blank Printing Position: {printing_pos!r}"
            continue

        # Collect PE variants for all codes
        variants: list[pd.Series] = []
        for code in codes:
            grp = pe_by_spc.get(code)
            if grp is None or grp.empty:
                stats["product_code_no_pe"] += 1
                continue
            variants.append(grp)

        if not variants:
            stats["skipped_mock_no_pe_hits"] += 1
            skip_reasons[mock_id] = f"no ProductExport SPC hits for {codes}"
            continue

        pe_hits = pd.concat(variants, ignore_index=True).drop_duplicates(subset=["UID"])
        mock_new = 0
        mock_skip_ga = 0
        mock_skip_fields = 0

        for _, pe_row in pe_hits.iterrows():
            uid = clean(pe_row["UID"])
            brand_code = clean(pe_row.get("Brand Code", ""))
            desc = clean(pe_row.get("Description", ""))
            colour = normalize_colour(pe_row.get("Colour Name", ""))
            size = normalize_size(pe_row.get("Size", ""))
            ga = gender_apparel_from_pe(brand_code, desc)

            if not ga:
                mock_skip_ga += 1
                stats["skipped_uid_no_gender_apparel"] += 1
                continue

            apparel_image = apparel_image_slug(ga, colour)
            custom_label = f"{mock_id}-{uid}"

            if not all([custom_label, ga, colour, size, apparel_image, pp]):
                mock_skip_fields += 1
                stats["skipped_uid_incomplete_seeds"] += 1
                continue

            rows.append(
                {
                    "Custom Label": custom_label,
                    "Gender Apparel": ga,
                    "Colour": colour,
                    "Size": size,
                    "Apparel Image": apparel_image,
                    "Print Positions": pp,
                }
            )
            mock_new += 1

        if mock_new == 0:
            stats["skipped_mock_zero_rows"] += 1
            skip_reasons[mock_id] = (
                f"0 rows after filters (PE={len(pe_hits)}, "
                f"no_GA={mock_skip_ga}, incomplete={mock_skip_fields})"
            )
        else:
            stats["mocks_generated"] += 1
            stats["rows_generated"] += mock_new
            stats[f"rows_{mock_id}"] = mock_new

    out = pd.DataFrame(rows, columns=SEED_COLS)
    return out, {"counts": dict(stats), "skip_reasons": skip_reasons}


def load_db(db_path: Path) -> pd.DataFrame:
    if db_path.suffix.lower() == ".csv":
        return pd.read_csv(db_path, dtype=str, low_memory=False)
    return pd.read_excel(db_path, sheet_name=SHEET, dtype=str)


def save_db(df: pd.DataFrame, db_path: Path) -> None:
    if db_path.suffix.lower() == ".csv":
        df.to_csv(db_path, index=False)
    else:
        df.to_excel(db_path, sheet_name=SHEET, index=False)


def append_to_db(db_path: Path, new_rows: pd.DataFrame, backup: bool) -> None:
    if backup:
        BACKUPS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = BACKUPS / f"{db_path.stem}_preGenerate_{stamp}{db_path.suffix}"
        print(f"Backup -> {bak}", flush=True)
        shutil.copy2(db_path, bak)

    print(f"Loading DB for append: {db_path}", flush=True)
    df = load_db(db_path)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)

    # Ensure seed columns exist
    for c in SEED_COLS:
        if c not in df.columns:
            df[c] = ""

    blank = {c: "" for c in df.columns}
    add = []
    for _, row in new_rows.iterrows():
        rec = dict(blank)
        for c in SEED_COLS:
            rec[c] = row[c]
        add.append(rec)

    out = pd.concat([df, pd.DataFrame(add)], ignore_index=True)
    print(f"Writing {db_path} ({len(df):,} -> {len(out):,} rows) ...", flush=True)
    save_db(out, db_path)
    print("Done.", flush=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Generate seed rows from Mocks Guide + ProductExport")
    p.add_argument("--file", type=Path, default=DEFAULT_DB, help="Custom_Label_Database.csv (or .xlsx)")
    p.add_argument("--pe", type=Path, default=DEFAULT_PE, help="ProductExport.xlsx")
    p.add_argument("--mocks", type=Path, default=DEFAULT_MOCKS, help="Mocks Database Guide CSV")
    p.add_argument("--mock", default="", help="Comma list of mock IDs to process (default: all eligible)")
    p.add_argument("--dry-run", action="store_true", help="Report only; do not write")
    p.add_argument("--no-backup", action="store_true", help="Skip backup before write")
    args = p.parse_args()

    only_mocks = None
    if clean(args.mock):
        only_mocks = {m.strip().upper() for m in args.mock.split(",") if m.strip()}

    print(f"Loading mocks: {args.mocks}", flush=True)
    mocks = load_mocks(args.mocks)
    print(f"  mock rows={len(mocks):,}", flush=True)

    print(f"Loading PE: {args.pe}", flush=True)
    pe = load_pe(args.pe)
    print(f"  PE rows={len(pe):,}", flush=True)

    print(f"Loading DB: {args.file}", flush=True)
    db = load_db(args.file)
    for c in db.columns:
        db[c] = db[c].fillna("").astype(str)
    print(f"  DB rows={len(db):,}", flush=True)

    skip_ids = existing_mock_ids(db)
    print(f"  Mock IDs already in DB (will skip): {len(skip_ids)}", flush=True)

    new_rows, meta = generate_rows(mocks, pe, skip_ids, only_mocks)
    counts = meta["counts"]
    skip_reasons = meta["skip_reasons"]

    print("\n=== Counts ===", flush=True)
    for k in sorted(counts):
        if k.startswith("rows_M"):
            continue
        print(f"  {k}: {counts[k]:,}", flush=True)

    print(f"\nNew seed rows ready: {len(new_rows):,}", flush=True)
    if len(new_rows):
        print("\nSample (first 5):", flush=True)
        print(new_rows.head(5).to_string(index=False), flush=True)
        print("\nPer-mock new rows:", flush=True)
        per = new_rows["Custom Label"].str.extract(r"^(M\d+)", expand=False).value_counts()
        for mid, n in per.items():
            print(f"  {mid}: {n:,}", flush=True)

    # Show skip summary (limit)
    interesting = {
        k: v
        for k, v in skip_reasons.items()
        if not v.startswith("mock already in")
    }
    if interesting:
        print(f"\nSkipped mocks (non-already-in-DB): {len(interesting)}", flush=True)
        for mid, reason in list(interesting.items())[:40]:
            print(f"  {mid}: {reason}", flush=True)
        if len(interesting) > 40:
            print(f"  ... and {len(interesting) - 40} more", flush=True)

    if args.dry_run:
        print("\nDry-run: no file written.", flush=True)
        return 0

    if new_rows.empty:
        print("Nothing to write.", flush=True)
        return 0

    append_to_db(args.file, new_rows, backup=not args.no_backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
