"""Fill Printing Type on Custom Label.

  python scripts/fill_printing_type.py --dry-run
  python scripts/fill_printing_type.py
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import paths as wh
from shared.areeb_taxonomy import cell
from shared.printing_type import COL, classify_cl_row, load_mock_printing_types


def backup_file(path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{path.stem}.bak_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    path = wh.cl_csv_path()
    mock_types = load_mock_printing_types()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = [{k: cell(v) for k, v in row.items()} for row in reader]
    if COL not in headers:
        raise SystemExit(f"CL missing column {COL!r}")
    stats: dict[str, int] = defaultdict(int)
    samples: list[str] = []
    for row in rows:
        value = classify_cl_row(row, mock_types=mock_types)
        prev = cell(row.get(COL))
        stats["rows"] += 1
        stats[value] += 1
        if prev != value:
            stats["would_write" if args.dry_run else "wrote"] += 1
        row[COL] = value
        if len(samples) < 6:
            samples.append(f"{row.get('Custom Label')} ga={row.get('Gender Apparel')!r} -> {value}")
    print(f"Custom Label: {path}")
    print(f"  rows={stats['rows']:,}")
    for key in sorted(k for k in stats if k != "rows"):
        print(f"  {key}: {stats[key]:,}")
    for line in samples:
        print(f"  e.g. {line}")
    if args.dry_run:
        print("Dry run - no files written.")
        return 0
    bak = backup_file(path, wh.cl_backups_dir())
    print(f"  backup {bak}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("  wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
