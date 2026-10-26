"""Set print positions from F/P-F8 and B4 tokens on the Areeb CSV.

F/P-F8 (both tokens) is Front Left Pocket, 80x100, not Front Center.
B4 is Back Center. The back millimetres are copied from a front slot on the
same row. A row with no front size gets the position and a blank size.
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = Path(__file__).resolve().parent
for p in (_ROOT, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fill_design_image_suffix import fill_row
from shared.paths.catalog import cl_areeb_csv_path, cl_backups_dir

POCKET = ("Front Left Pocket", "80", "100")


def tokens(label: str) -> set[str]:
    return {part.strip().upper() for part in label.replace(" ", "-").split("-")}


def back_mm(row: dict) -> tuple[str, str]:
    for i in range(1, 5):
        name = (row.get(f"Position {i} Name") or "").lower()
        if "front" in name and "pocket" not in name:
            w, h = row.get(f"Width {i} (mm)"), row.get(f"Height {i} (mm)")
            if (w or "").strip() and (h or "").strip():
                return w, h
    return "", ""


def set_slot(row: dict, i: int, name: str, w: str, h: str) -> None:
    row[f"Position {i} Name"] = name
    row[f"Width {i} (mm)"] = w
    row[f"Height {i} (mm)"] = h


def named(row: dict) -> list[int]:
    return [i for i in range(1, 5) if (row.get(f"Position {i} Name") or "").strip()]


def rewrite(path: Path, *, dry_run: bool) -> dict[str, int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    counts = {"fp_f8": 0, "b4": 0, "rows": 0, "no_mm": 0}
    for row in rows:
        tok = tokens(row.get("Custom Label") or "")
        touched = False
        if {"F/P", "F8"} <= tok:
            for i in named(row):
                if (row.get(f"Position {i} Name") or "").strip().lower() == "front center":
                    set_slot(row, i, *POCKET)
                    counts["fp_f8"] += 1
                    touched = True
        if "B4" in tok and not any("back" in (row.get(f"Position {i} Name") or "").lower() for i in range(1, 5)):
            w, h = back_mm(row)
            if not w:
                counts["no_mm"] += 1
            slots = named(row)
            if len(slots) < 4:
                target = slots[-1] + 1 if slots else 1
                set_slot(row, target, "Back Center", w, h)
                counts["b4"] += 1
                touched = True
        if touched:
            positions = [row.get(f"Position {i} Name") or "" for i in range(1, 5)]
            row["Print Positions"] = ", ".join(p for p in positions if p.strip())
            fill_row(row)
            counts["rows"] += 1
    if dry_run or not counts["rows"]:
        return counts
    bak = cl_backups_dir()
    bak.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, bak / f"{path.stem}_prePositions_{stamp}{path.suffix}")
    tmp = path.with_suffix(".tmp.csv")
    with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)
    return counts


def main() -> None:
    dry = "--run" not in sys.argv
    print(("dry-run " if dry else "wrote ") + str(rewrite(cl_areeb_csv_path(), dry_run=dry)))


if __name__ == "__main__":
    main()
