"""Set every sleeve print slot on the Areeb CSV to 100x100 mm.

A slot counts when its Position Name contains "sleeve" (Sleeve, Right Sleeve).
Blank slots are filled too. Other positions are not touched.
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.paths.catalog import cl_areeb_csv_path, cl_backups_dir

W, H = "100", "100"


def rewrite(path: Path, *, dry_run: bool) -> dict[str, int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    counts = {"slots": 0, "rows": 0, "was_blank": 0}
    for row in rows:
        touched = False
        for i in range(1, 5):
            name = (row.get(f"Position {i} Name") or "").lower()
            if "sleeve" not in name:
                continue
            if not (row.get(f"Width {i} (mm)") or "").strip():
                counts["was_blank"] += 1
            if row.get(f"Width {i} (mm)") == W and row.get(f"Height {i} (mm)") == H:
                continue
            row[f"Width {i} (mm)"] = W
            row[f"Height {i} (mm)"] = H
            counts["slots"] += 1
            touched = True
        counts["rows"] += touched
    if dry_run or not counts["slots"]:
        return counts
    bak = cl_backups_dir()
    bak.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, bak / f"{path.stem}_preSleeve100_{stamp}{path.suffix}")
    tmp = path.with_suffix(".tmp.csv")
    with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)
    return counts


def main() -> None:
    dry = "--run" not in sys.argv
    counts = rewrite(cl_areeb_csv_path(), dry_run=dry)
    print(("dry-run " if dry else "wrote ") + str(counts))


if __name__ == "__main__":
    main()
