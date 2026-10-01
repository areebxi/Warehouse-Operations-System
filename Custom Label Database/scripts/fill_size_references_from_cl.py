"""
Fill Size References.csv from live Custom_Label_Database.csv.

Live paths:
  database/shared/custom_label/Custom_Label_Database.csv
  database/custom-label-database/support/Size References.csv
  database/custom-label-database/support/Mocks Database.csv

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
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Paths module inserts script/warehouse roots onto sys.path.
from fill_sr_from_cl_paths import (  # noqa: E402
    BACKUPS,
    BLANK_FILL_COLS,
    DEFAULT_DB,
    DEFAULT_MOCKS,
    DEFAULT_SR,
    SR_COLS,
)
from fill_from_seeds import clean  # noqa: E402
from fill_sr_from_cl_apply import apply_fill, pick_cl_payloads  # noqa: E402
from fill_sr_from_cl_parse import (  # noqa: E402
    load_mock_meta,
    parse_cl_mock_uid,
    sr_key,
    suffix_for_slots,
)


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


def _selfcheck() -> None:
    assert sr_key("m123", "45678") == "M123 (45678)"
    assert parse_cl_mock_uid("M123-45678") == ("M123", "45678")
    assert parse_cl_mock_uid("M260-P5-102722") is None
    assert suffix_for_slots(["Front Center"], 1) == [""]
    assert suffix_for_slots(["Front Center", "Back Center"], 2) == ["F", "B"]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        print("fill_size_references_from_cl selfcheck OK")
        raise SystemExit(0)
    raise SystemExit(main())
