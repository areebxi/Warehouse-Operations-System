"""
Fill Size References.csv from live Custom_Label_Database.csv.

Live paths:
  database/shared/custom_label/Custom_Label_Database.csv
  database/custom-label-database/support/Size References.csv
  database/custom-label-database/support/Mocks Databse.csv

Scope: mock+UID labels only (Custom Label M123-45678 → SKU Value `M123 (45678)`).
  - Append missing exact mock+UID keys (and extra design rows when CL has more slots).
  - Blank-only on existing cells. Size Width/Height never overwritten.
  - Number of Designs is updated on a group only when extra design rows are added.
  - Non-mock Size References rows (A4, BG125, 10AILG-M-T, …) are untouched.
  - Iron-on / hybrid labels (M260-P5-…, M66-M-T-…) are skipped.

Run from Custom Label Database app root:

  python scripts/fill_size_references_from_cl.py --dry-run
  python scripts/fill_size_references_from_cl.py
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

_SCRIPT_DIR = Path(__file__).resolve().parent
_APP_ROOT = _SCRIPT_DIR.parent
_WAREHOUSE_ROOT = _APP_ROOT.parent
sys.path.insert(0, str(_WAREHOUSE_ROOT))
sys.path.insert(0, str(_SCRIPT_DIR))

from shared.paths import (  # noqa: E402
    cl_csv_path,
    custom_label_support_dir,
    warehouse_root_from,
)

from fill_from_seeds import (  # noqa: E402
    classify,
    clean,
    infer_printing_position,
    map_sr_size,
    mm_str,
    split_positions,
    sr_gender,
    to_num,
)
from generate_from_mocks import load_mocks  # noqa: E402

_ROOT = warehouse_root_from(_SCRIPT_DIR)
_SUPPORT = custom_label_support_dir(_ROOT)
_LEGACY_SUPPORT = _APP_ROOT / "support"

DEFAULT_DB = cl_csv_path(_ROOT)
DEFAULT_SR = _SUPPORT / "Size References.csv"
if not DEFAULT_SR.is_file():
    DEFAULT_SR = _LEGACY_SUPPORT / "Size References.csv"
DEFAULT_MOCKS = _SUPPORT / "Mocks Databse.csv"
if not DEFAULT_MOCKS.is_file():
    DEFAULT_MOCKS = _LEGACY_SUPPORT / "Mocks Databse.csv"
BACKUPS = _SUPPORT / "backups"

SR_COLS = [
    "SKU Value",
    "SKU Value 2",
    "SKU Value 3",
    "Number of Designs",
    "Size Width",
    "Size Height",
    "Suffix",
    "Gender",
    "Size",
    "Printing Position",
    "Product Code",
    "Printing Size",
]

RE_MOCK_UID = re.compile(r"^(M\d+)-(\d+)$", re.I)
RE_SR_KEY = re.compile(r"^(M\d+)\s*\((\d+)\)\s*$", re.I)

BLANK_FILL_COLS = (
    "Suffix",
    "Gender",
    "Size",
    "Printing Position",
    "Product Code",
    "Printing Size",
    "Size Width",
    "Size Height",
)


def sr_key(mock: str, uid: str) -> str:
    return f"{mock.upper()} ({uid})"


def parse_cl_mock_uid(label: str) -> tuple[str, str] | None:
    m = RE_MOCK_UID.match(clean(label))
    if not m:
        return None
    return m.group(1).upper(), m.group(2)


def parse_sr_key(sku_value: str) -> str:
    m = RE_SR_KEY.match(clean(sku_value))
    if not m:
        return ""
    return sr_key(m.group(1), m.group(2))


def mm_cell(val) -> str:
    n = to_num(val)
    if n is None:
        return ""
    return mm_str(n)


def suffix_for_slots(pos_names: list[str], n_slots: int) -> list[str]:
    """Multi-design: F/B/P/S. Single-design: blank suffix (matches existing SR)."""
    if n_slots <= 1:
        return [""] * n_slots
    used: dict[str, int] = defaultdict(int)
    out: list[str] = []
    for i in range(n_slots):
        kind = classify(pos_names[i]) if i < len(pos_names) else "empty"
        if kind == "pocket":
            token = "P"
        elif kind == "back":
            token = "B"
        elif kind == "front":
            token = "F"
        elif kind == "other":
            token = "S"
        else:
            token = "F"
        n = used[token]
        used[token] = n + 1
        out.append(token if n == 0 else f"{token}-1")
    return out


def load_mock_meta(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    mocks = load_mocks(path)
    out: dict[str, dict[str, str]] = {}
    for _, rec in mocks.iterrows():
        mid = clean(rec.get("Pasting Mocks ID")).upper()
        if not mid or mid in out:
            continue
        out[mid] = {
            "product_code": clean(rec.get("Product Code")),
            "printing_size": clean(rec.get("Printing Size")),
            "printing_position": clean(rec.get("Printing Position")),
        }
    return out


RE_LETTER_SIZE = re.compile(r"^(?:[2-5])?XL$|^XXL$|^XS$|^S$|^M$|^L$", re.I)


def _map_sr_size(size: str) -> str:
    s = clean(size)
    if not s:
        return ""
    mapped = map_sr_size(s)
    if mapped != s:
        return mapped
    if RE_LETTER_SIZE.match(s):
        return map_sr_size(s.upper().replace("XXL", "2XL")) or s.upper()
    return s


def slot_payload(cl_row: dict) -> dict:
    label = clean(cl_row.get("Custom Label"))
    parsed = parse_cl_mock_uid(label)
    assert parsed is not None
    mock, uid = parsed
    pos_named = []
    widths: list[str] = []
    heights: list[str] = []
    print_sizes: list[str] = []
    for n in range(1, 5):
        pos_named.append(clean(cl_row.get(f"Position {n} Name")))
        widths.append(mm_cell(cl_row.get(f"Width {n} (mm)")))
        heights.append(mm_cell(cl_row.get(f"Height {n} (mm)")))
        print_sizes.append(clean(cl_row.get(f"Print Size {n}")))

    from_pp = split_positions(clean(cl_row.get("Print Positions")))
    names: list[str] = []
    for i in range(4):
        name = pos_named[i] or (from_pp[i] if i < len(from_pp) else "")
        names.append(name)

    n_wh = 0
    for i in range(4):
        if widths[i] and heights[i]:
            n_wh = i + 1
    n_pos = 0
    for i in range(4):
        if names[i]:
            n_pos = i + 1
    n_slots = max(n_wh, n_pos, 1)

    names = names[:n_slots]
    while len(names) < n_slots:
        names.append("")

    return {
        "key": sr_key(mock, uid),
        "mock": mock,
        "uid": uid,
        "n_slots": n_slots,
        "names": names,
        "widths": widths[:n_slots] + [""] * max(0, n_slots - 4),
        "heights": heights[:n_slots] + [""] * max(0, n_slots - 4),
        "print_sizes": print_sizes[:n_slots] + [""] * max(0, n_slots - 4),
        "gender": sr_gender(clean(cl_row.get("Gender Apparel")), clean(cl_row.get("Size"))),
        "size": _map_sr_size(clean(cl_row.get("Size"))),
        "product_code_cl": clean(cl_row.get("BTC Product Code"))
        or clean(cl_row.get("Supplier Product Code")),
        "wh_score": n_wh,
        "ga_len": len(clean(cl_row.get("Gender Apparel"))),
    }


def desired_sr_rows(payload: dict, mock_meta: dict[str, dict[str, str]]) -> list[dict]:
    meta = mock_meta.get(payload["mock"], {})
    names = payload["names"]
    n = payload["n_slots"]
    suffixes = suffix_for_slots(names, n)
    printing_pos = infer_printing_position([n_ for n_ in names if n_]) or meta.get(
        "printing_position", ""
    )
    product_code = meta.get("product_code") or payload["product_code_cl"]
    guide_psize = meta.get("printing_size", "")
    nd = str(n)
    rows: list[dict] = []
    for i in range(n):
        psize = payload["print_sizes"][i] if i < len(payload["print_sizes"]) else ""
        if not psize:
            psize = guide_psize
        w = payload["widths"][i] if i < len(payload["widths"]) else ""
        h = payload["heights"][i] if i < len(payload["heights"]) else ""
        rows.append(
            {
                "SKU Value": payload["key"],
                "SKU Value 2": "",
                "SKU Value 3": "",
                "Number of Designs": nd,
                "Size Width": w,
                "Size Height": h,
                "Suffix": suffixes[i],
                "Gender": payload["gender"],
                "Size": payload["size"],
                "Printing Position": printing_pos,
                "Product Code": product_code,
                "Printing Size": psize,
            }
        )
    return rows


def blank(val) -> bool:
    return clean(val) == ""


def fill_cell(existing: dict, col: str, incoming: str, counts: dict, prefixed: str) -> None:
    if not incoming:
        return
    if not blank(existing.get(col)):
        counts[f"skip_already_{prefixed}_{col}"] += 1
        return
    existing[col] = incoming
    counts[f"filled_{prefixed}_{col}"] += 1


def empty_sr_row() -> dict:
    return {c: "" for c in SR_COLS}


def pick_cl_payloads(cl: pd.DataFrame) -> tuple[dict[str, dict], dict]:
    stats: dict[str, int] = defaultdict(int)
    best: dict[str, dict] = {}
    records = cl.to_dict("records")
    stats["cl_label_rows"] = len(records)
    for rec in records:
        parsed = parse_cl_mock_uid(rec.get("Custom Label", ""))
        if parsed is None:
            stats["cl_skipped_not_mock_uid"] += 1
            continue
        stats["cl_mock_uid_rows"] += 1
        payload = slot_payload(rec)
        key = payload["key"]
        prev = best.get(key)
        if prev is None:
            best[key] = payload
        elif payload["wh_score"] > prev["wh_score"] or (
            payload["wh_score"] == prev["wh_score"]
            and payload["ga_len"] > prev["ga_len"]
        ):
            stats["cl_duplicate_keys_replaced"] += 1
            best[key] = payload
        else:
            stats["cl_duplicate_keys_kept_first"] += 1
    stats["cl_unique_mock_uid_keys"] = len(best)
    return best, stats


def apply_fill(
    sr_rows: list[dict],
    payloads: dict[str, dict],
    mock_meta: dict[str, dict[str, str]],
) -> tuple[list[dict], dict]:
    counts: dict[str, int] = defaultdict(int)
    by_key: dict[str, list[int]] = defaultdict(list)
    for i, rec in enumerate(sr_rows):
        key = parse_sr_key(rec.get("SKU Value", ""))
        if key:
            by_key[key].append(i)
            counts["sr_existing_mock_uid_rows"] += 1
        else:
            counts["sr_non_mock_or_other_rows"] += 1

    counts["sr_existing_mock_uid_keys"] = len(by_key)
    appends: list[dict] = []
    samples_new: list[str] = []
    samples_extra: list[str] = []
    samples_filled: list[str] = []

    for key, payload in payloads.items():
        desired = desired_sr_rows(payload, mock_meta)
        idxs = by_key.get(key, [])
        if not idxs:
            appends.extend(desired)
            counts["keys_appended"] += 1
            counts["rows_appended_new_key"] += len(desired)
            if payload["n_slots"] > 1:
                counts["new_keys_multi_design"] += 1
            if len(samples_new) < 8:
                samples_new.append(f"{key} n={payload['n_slots']}")
            continue

        counts["keys_already_present"] += 1
        extra = len(desired) - len(idxs)
        if extra > 0:
            counts["keys_extra_design_rows"] += 1
            counts["rows_appended_extra_design"] += extra
            nd = str(len(desired))
            for i in idxs:
                sr_rows[i]["Number of Designs"] = nd
            for rec in desired[len(idxs) :]:
                rec["Number of Designs"] = nd
                appends.append(rec)
            if len(samples_extra) < 6:
                samples_extra.append(f"{key} {len(idxs)}->{len(desired)}")

        n_overlap = min(len(idxs), len(desired))
        expand = extra > 0
        before_fills = sum(counts.get(f"filled_existing_{c}", 0) for c in BLANK_FILL_COLS)
        for j in range(n_overlap):
            existing = sr_rows[idxs[j]]
            incoming = desired[j]
            for col in BLANK_FILL_COLS:
                if (
                    col == "Suffix"
                    and not expand
                    and len(desired) == 1
                    and blank(existing.get("Suffix"))
                ):
                    counts["skip_single_blank_suffix"] += 1
                    continue
                fill_cell(existing, col, incoming.get(col, ""), counts, "existing")
        after_fills = sum(counts.get(f"filled_existing_{c}", 0) for c in BLANK_FILL_COLS)
        if after_fills > before_fills and len(samples_filled) < 6:
            samples_filled.append(key)

    sr_rows.extend(appends)
    counts["rows_appended_total"] = len(appends)
    counts["sample_new"] = samples_new  # type: ignore[assignment]
    counts["sample_extra"] = samples_extra  # type: ignore[assignment]
    counts["sample_filled"] = samples_filled  # type: ignore[assignment]
    return sr_rows, counts


def dataframe_from_rows(rows: list[dict]) -> pd.DataFrame:
    out = pd.DataFrame(rows, columns=SR_COLS)
    for c in SR_COLS:
        out[c] = out[c].map(lambda v: "" if v is None else str(v))
    return out


def backup_sr(path: Path) -> Path:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS / f"Size_References_preFill_{stamp}.csv"
    shutil.copy2(path, dest)
    return dest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fill Size References from CL mock+UID rows.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--sr", type=Path, default=DEFAULT_SR)
    p.add_argument("--mocks", type=Path, default=DEFAULT_MOCKS)
    return p.parse_args(argv)


def print_report(stats: dict, counts: dict, backup: Path | None, dry: bool) -> None:
    print("=== Size References <- CL mock+UID ===", flush=True)
    print(f"  mode: {'DRY-RUN' if dry else 'WRITE'}", flush=True)
    print(f"  CL rows: {stats.get('cl_label_rows', 0):,}", flush=True)
    print(f"  CL mock+UID rows: {stats.get('cl_mock_uid_rows', 0):,}", flush=True)
    print(f"  CL skipped (not M##-UID): {stats.get('cl_skipped_not_mock_uid', 0):,}", flush=True)
    print(f"  CL unique mock+UID keys: {stats.get('cl_unique_mock_uid_keys', 0):,}", flush=True)
    print(f"  SR existing mock+UID rows: {counts.get('sr_existing_mock_uid_rows', 0):,}", flush=True)
    print(f"  SR existing mock+UID keys: {counts.get('sr_existing_mock_uid_keys', 0):,}", flush=True)
    print(f"  SR other rows (untouched keys): {counts.get('sr_non_mock_or_other_rows', 0):,}", flush=True)
    print(f"  keys already in SR: {counts.get('keys_already_present', 0):,}", flush=True)
    print(f"  keys appended (new): {counts.get('keys_appended', 0):,}", flush=True)
    print(f"  new keys with 2+ designs: {counts.get('new_keys_multi_design', 0):,}", flush=True)
    print(f"  existing keys extra design rows: {counts.get('keys_extra_design_rows', 0):,}", flush=True)
    print(f"  rows appended (new keys): {counts.get('rows_appended_new_key', 0):,}", flush=True)
    print(f"  rows appended (extra designs): {counts.get('rows_appended_extra_design', 0):,}", flush=True)
    print(f"  rows appended total: {counts.get('rows_appended_total', 0):,}", flush=True)
    print("  blank-fills on existing mock rows:", flush=True)
    for col in BLANK_FILL_COLS:
        n = counts.get(f"filled_existing_{col}", 0)
        if n:
            print(f"    {col}: {n:,}", flush=True)
    if not any(counts.get(f"filled_existing_{c}", 0) for c in BLANK_FILL_COLS):
        print("    (none)", flush=True)
    if counts.get("sample_new"):
        print("  sample new keys:", "; ".join(counts["sample_new"]), flush=True)
    if counts.get("sample_extra"):
        print("  sample extra-design:", "; ".join(counts["sample_extra"]), flush=True)
    if backup:
        print(f"  backup: {backup}", flush=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.db.is_file():
        print(f"Missing CL CSV: {args.db}", file=sys.stderr)
        return 1
    if not args.sr.is_file():
        print(f"Missing Size References: {args.sr}", file=sys.stderr)
        return 1

    print(f"CL:  {args.db}", flush=True)
    print(f"SR:  {args.sr}", flush=True)
    print(f"Mocks: {args.mocks}", flush=True)
    print(f"Loading CL: {args.db}", flush=True)
    cl = pd.read_csv(args.db, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    print(f"Loading SR: {args.sr}", flush=True)
    sr = pd.read_csv(args.sr, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    for c in SR_COLS:
        if c not in sr.columns:
            sr[c] = ""
    print(f"Loading mocks guide: {args.mocks}", flush=True)
    mock_meta = load_mock_meta(args.mocks)
    print(f"  mock IDs with meta: {len(mock_meta):,}", flush=True)

    payloads, stats = pick_cl_payloads(cl)
    sr_rows = [{c: clean(rec.get(c, "")) for c in SR_COLS} for rec in sr.to_dict("records")]
    before_n = len(sr_rows)
    sr_rows, counts = apply_fill(sr_rows, payloads, mock_meta)
    after_n = len(sr_rows)

    print_report(stats, counts, None, args.dry_run)
    print(f"  SR rows before->after: {before_n:,} -> {after_n:,}", flush=True)

    if args.dry_run:
        print("Dry-run: no file written.", flush=True)
        return 0

    backup = None
    if not args.no_backup:
        backup = backup_sr(args.sr)
        print(f"Backup: {backup}", flush=True)

    out = dataframe_from_rows(sr_rows)
    fallback = args.sr.with_name("Size_References_write_fallback.csv")
    try:
        out.to_csv(args.sr, index=False, encoding="utf-8")
        dest = args.sr
    except PermissionError:
        out.to_csv(fallback, index=False, encoding="utf-8")
        print(
            f"PermissionError on {args.sr.name}. Wrote {fallback.name}. "
            "Close the live file and swap.",
            file=sys.stderr,
        )
        dest = fallback
    print(f"Wrote {dest} ({after_n:,} rows).", flush=True)
    print_report(stats, counts, backup, False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
