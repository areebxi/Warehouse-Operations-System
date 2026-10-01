"""
Fast Custom Label add: seed -> same fill_from_seeds steps -> append-only write.

Integrity: existing CL rows are never rewritten (append only). Fill rules are
the same blank-only / PE / print / Customise steps as fill_from_seeds.py.
Backup before write (unless --no-backup).

Default = **named labels only** (fast). Use --all-spc to also seed every PE
UID for that BTC SPC (slower; catalog completeness).

  python scripts/add_labels.py M260-P3-3265 W101-SkyBe-O/S-Yes
  python scripts/add_labels.py --skus 10428ALG-M260-P3-3265 128967LG-W101-SkyBe-O/S-Yes
  python scripts/add_labels.py --all-spc --skus 10428ALG-M260-P3-3265
  python scripts/add_labels.py --dry-run --skus ...
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
_WAREHOUSE = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(_WAREHOUSE))

from shared import paths as wh  # noqa: E402
from fill_from_seeds import DEFAULT_PE, load_pe_index  # noqa: E402
from add_labels_exports import *  # noqa: F401,F403,E402
from add_labels_exports import (  # noqa: E402
    SEED_COLS,
    _collect_peers_for_labels,
    _expand_all_spc,
    _scan_existing,
    build_seed_rows,
    fill_rows,
    label_from_input,
)
from add_labels_selfcheck import run_selfchecks  # noqa: E402


def append_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        for row in rows:
            w.writerow({c: row.get(c, "") for c in fieldnames})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("labels", nargs="*", help="Custom Labels and/or packing SKUs")
    ap.add_argument(
        "--skus",
        nargs="+",
        default=[],
        help="Packing Item SKUs (Custom Label = after first dash)",
    )
    ap.add_argument(
        "--all-spc",
        action="store_true",
        help="Also seed every PE UID for the named mock's BTC SPC (slower)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    raw_items: list[tuple[str, bool]] = [(x, False) for x in args.labels]
    raw_items.extend((x, True) for x in args.skus)
    if not raw_items:
        print("No labels/SKUs given.", file=sys.stderr)
        return 2

    labels = []
    for raw, from_sku in raw_items:
        lab = label_from_input(raw, from_sku=from_sku)
        if lab:
            labels.append(lab)
    seen_in: set[str] = set()
    uniq: list[str] = []
    for lab in labels:
        k = lab.casefold()
        if k in seen_in:
            continue
        seen_in.add(k)
        uniq.append(lab)
    labels = uniq

    cl_path = wh.cl_csv_path()
    print(f"Scanning labels in {cl_path} ...", flush=True)
    fieldnames, existing = _scan_existing(cl_path)
    print(f"  existing labels={len(existing):,}", flush=True)

    print(f"Loading BTC Product Data: {DEFAULT_PE}", flush=True)
    pe_index = load_pe_index(DEFAULT_PE)
    print(f"  PE UIDs={len(pe_index):,}", flush=True)

    sku_uids: dict[str, str] = {}
    for raw, from_sku in raw_items:
        if not from_sku:
            continue
        lab = label_from_input(raw, from_sku=True)
        prefix = raw.split("-", 1)[0].strip()
        if lab and prefix.isdigit() and prefix in pe_index.index:
            sku_uids[lab.casefold()] = prefix

    print("Loading peer rows for named labels...", flush=True)
    peers = _collect_peers_for_labels(cl_path, fieldnames, labels)

    if args.all_spc:
        expanded: list[str] = []
        for lab in labels:
            expanded.extend(_expand_all_spc(lab, peers, pe_index))
        labels = list(dict.fromkeys(expanded))
        print(f"  --all-spc expanded to {len(labels)} labels", flush=True)
        peers = _collect_peers_for_labels(cl_path, fieldnames, labels)

    new_rows, skipped = build_seed_rows(
        labels,
        fieldnames=fieldnames,
        existing=existing,
        peers=peers,
        pe_index=pe_index,
        all_spc=False,  # expansion already done when --all-spc
        sku_uids=sku_uids,
    )
    print(
        f"Named inputs={len(labels)}  new rows={len(new_rows)}  "
        f"skipped={len(skipped)}  all_spc={args.all_spc}",
        flush=True,
    )
    for r in new_rows[:12]:
        print("  seed", {k: r.get(k) for k in SEED_COLS}, flush=True)
    if len(new_rows) > 12:
        print(f"  ... +{len(new_rows) - 12} more", flush=True)
    if not new_rows:
        print("Nothing to add.", flush=True)
        return 0

    run_selfchecks()
    df = pd.DataFrame(new_rows)
    for c in fieldnames:
        if c not in df.columns:
            df[c] = ""
    df = df[fieldnames]
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)

    counts: dict = defaultdict(int)
    print("Filling (same steps as fill_from_seeds)...", flush=True)
    assert pe_index is not None
    fill_rows(df, pe_index, counts)

    print("=== Counts ===", flush=True)
    for k in sorted(counts):
        if counts[k]:
            print(f"  {k}: {counts[k]:,}", flush=True)

    if args.dry_run:
        print("Dry-run: no write.", flush=True)
        return 0

    if not args.no_backup:
        backups = wh.cl_backups_dir()
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backups / f"{cl_path.stem}_preAdd_{stamp}{cl_path.suffix}"
        shutil.copy2(cl_path, backup)
        print(f"Backup: {backup}", flush=True)

    out_rows = df.to_dict(orient="records")
    try:
        append_rows(cl_path, fieldnames, out_rows)
    except PermissionError:
        fallback = cl_path.with_name(cl_path.stem + "_write_fallback" + cl_path.suffix)
        shutil.copy2(cl_path, fallback)
        append_rows(fallback, fieldnames, out_rows)
        print(f"Live CSV locked. Wrote fallback: {fallback}", flush=True)
        return 0

    print(f"Appended {len(out_rows)} rows -> {cl_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
