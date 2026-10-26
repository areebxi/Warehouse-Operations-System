"""Rewrite hoodie front/back mm on the Areeb CSV from the locked chart.

Kids and men/women bands: .cursor/rules/custom-label-database/print-sizes.mdc.
Pocket, sleeve, and corner slots stay. 6XL has no band and is left.
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

KIDS = {
    "xs": (170, 170), "extra small": (170, 170), "yxs": (170, 170),
    "3-4 years": (170, 170), "3-4y": (170, 170),
    "s": (190, 190), "small": (190, 190), "ys": (190, 190), "5-6 years": (190, 190),
    "m": (210, 210), "medium": (210, 210), "ym": (210, 210), "7-8 years": (210, 210),
    "l": (230, 230), "large": (230, 230), "9-11 years": (230, 230),
    "xl": (250, 250), "extra large": (250, 250), "y2xl": (250, 250),
    "12-13 years": (250, 250), "12-14 years": (250, 250), "14-15 years": (250, 250),
}
ADULT = {
    "xs": (250, 250), "extra small": (250, 250), "s": (250, 250), "small": (250, 250),
    "m": (270, 270), "medium": (270, 270),
    "l": (290, 290), "large": (290, 290),
    "xl": (310, 310), "extra large": (310, 310),
    "2xl": (330, 330), "xxl": (330, 330),
    "3xl": (350, 350),
    "4xl": (370, 370),
    "5xl": (390, 390),
}
# ponytail: "front"/"back" in the name is enough; pocket is excluded first.
SKIP_WORDS = ("pocket", "sleeve", "corner", "inside", "chest")


def band(size: str, kids: bool) -> tuple[int, int] | None:
    key = size.strip().split(" (", 1)[0].strip().lower()
    return (KIDS if kids else ADULT).get(key)


def is_kids(gender_apparel: str, size: str) -> bool:
    ga = gender_apparel.lower()
    if "kid" in ga or "youth" in ga:
        return True
    # Age bands are kids even when Gender Apparel is a style code (SF500B).
    return band(size, True) is not None and band(size, False) is None


def is_body(name: str) -> bool:
    n = name.strip().lower()
    if not n or any(w in n for w in SKIP_WORDS):
        return False
    return "front" in n or "back" in n


def rewrite(path: Path, *, dry_run: bool) -> dict[str, int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    counts = {"hoodies": 0, "slots": 0, "rows": 0, "unmapped": 0, "over_300": 0, "xl4_5": 0}
    for row in rows:
        if "hoodie" not in (row.get("Gender Apparel") or "").lower():
            continue
        counts["hoodies"] += 1
        kids = is_kids(row.get("Gender Apparel") or "", row.get("Size") or "")
        wh = band(row.get("Size") or "", kids)
        if wh is None:
            counts["unmapped"] += 1
            continue
        if wh[0] > 300 or wh[1] > 500:
            counts["over_300"] += 1
        if wh[0] >= 370:
            counts["xl4_5"] += 1
        touched = False
        for i in range(1, 5):
            if not is_body(row.get(f"Position {i} Name") or ""):
                continue
            w, h = str(wh[0]), str(wh[1])
            if row.get(f"Width {i} (mm)") == w and row.get(f"Height {i} (mm)") == h:
                continue
            row[f"Width {i} (mm)"] = w
            row[f"Height {i} (mm)"] = h
            counts["slots"] += 1
            touched = True
        counts["rows"] += touched
    if dry_run or not counts["slots"]:
        return counts
    bak = cl_backups_dir()
    bak.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, bak / f"{path.stem}_preHoodieSizes_{stamp}{path.suffix}")
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
