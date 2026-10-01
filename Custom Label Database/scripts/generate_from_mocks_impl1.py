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
            skip_reasons[mock_id] = f"no BTC Product Data SPC hits for {codes}"
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
def save_db(df: pd.DataFrame, db_path: Path) -> None:
    if db_path.suffix.lower() == ".csv":
        df.to_csv(db_path, index=False)
    else:
        df.to_excel(db_path, sheet_name=SHEET, index=False)
