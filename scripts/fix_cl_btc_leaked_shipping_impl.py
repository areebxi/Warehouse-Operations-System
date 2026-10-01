from __future__ import annotations
import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from shared import paths as wh

def run(*, dry_run: bool) -> dict[str, int]:
    path = wh.cl_csv_path()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = list(reader)

    stats: dict[str, int] = defaultdict(int)
    stats["rows"] = len(rows)
    samples: list[str] = []

    for row in rows:
        patch = plan_row(row)
        if not patch:
            continue
        stats["rows_touched"] += 1
        for col, value in patch.items():
            key = f"wrote_{col}" if not dry_run else f"would_{col}"
            stats[key] += 1
            if value == "":
                stats[f"cleared_{col}"] += 1
            elif cell(row.get(col)) == "":
                stats[f"restored_or_refilled_{col}"] += 1
            else:
                stats[f"replaced_{col}"] += 1
            row[col] = value
        if len(samples) < 6:
            samples.append(
                f"{cell(row.get('Custom Label'))} "
                f"SKU={cell(row.get(COL_SKU))!r} PC={cell(row.get(COL_PC))!r} "
                f"Stock={cell(row.get(COL_STOCK))!r} pkg={cell(row.get(COL_PKG))!r} "
                f"wt={cell(row.get(COL_WEIGHT))!r} svc={cell(row.get(COL_SERVICE))!r}"
            )

    print(f"Custom Label: {path}")
    for key in (
        "rows",
        "rows_touched",
        "cleared_BTC SKU",
        "cleared_BTC Product Code",
        "cleared_BTC Supplier Stock",
        "replaced_BTC SKU",
        "replaced_BTC Product Code",
        "replaced_BTC Supplier Stock",
        "restored_or_refilled_Package Type",
        "restored_or_refilled_Weight",
        "restored_or_refilled_Service",
        "would_BTC SKU",
        "would_BTC Product Code",
        "would_BTC Supplier Stock",
        "would_Package Type",
        "would_Weight",
        "would_Service",
    ):
        if key in stats:
            print(f"  {key}: {stats[key]:,}")
    for line in samples:
        print(f"  e.g. {line}")

    if dry_run:
        print("  dry-run — no write")
        return dict(stats)

    bak = backup_file(path)
    print(f"  backup {bak}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("  wrote", path)
    return dict(stats)
def backup_file(path: Path) -> Path:
    dest_dir = wh.cl_backups_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{path.stem}.bak_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest
