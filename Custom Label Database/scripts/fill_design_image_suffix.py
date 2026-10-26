"""Fill Design Image Suffix 1-4 on the Areeb catalog.

One named position stays blank. Two or more get a letter (no hyphen).
The queue looks for {design code}-{suffix}.png.
"""

from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

ROOT = Path(__file__).resolve().parents[2]
SRC_NAME = "Custom_Label_Database (Areeb) - With Suffix Columns.csv"
PRIMARY_NAME = "Custom_Label_Database (Areeb).csv"
FALLBACK_NAME = "Custom_Label_Database_write_fallback.csv"
ONE_BACK = "B/B-M-T-BLK-XL-YES"


def suffix_letter(name: str, names: list[str]) -> str:
    n = name.strip().casefold()
    if "inside" in n:
        return "I"
    if "right sleeve" in n:
        return "SR"
    if "left sleeve" in n:
        return "SL"
    if n == "sleeve":
        return "S"
    if "bottom right" in n:
        return "FBRC"
    if "bottom left" in n:
        return "FBLC"
    if "right pocket" in n:
        return "PR"
    if "left pocket" in n or n == "pocket":
        has_right = any("right pocket" in other.casefold() for other in names)
        return "PL" if has_right else "P"
    if n.startswith("back"):
        return "B"
    if n.startswith("front"):
        return "F"
    return ""


def slot_name(row: dict, n: int) -> str:
    return (row.get(f"Position {n} Name") or "").strip()


def clear_slot(row: dict, n: int) -> None:
    row[f"Position {n} Name"] = ""
    row[f"Print Size {n}"] = ""
    row[f"Width {n} (mm)"] = ""
    row[f"Height {n} (mm)"] = ""
    row[f"Design Image Suffix {n}"] = ""


def fill_row(row: dict) -> str:
    names = [slot_name(row, n) for n in range(1, 5)]
    named = [name for name in names if name]
    label = (row.get("Custom Label") or "").strip()
    if label == ONE_BACK and names[0].casefold() == "back center" and names[1].casefold() == "back center":
        clear_slot(row, 2)
        named = [names[0]]
    for n in range(1, 5):
        row[f"Design Image Suffix {n}"] = suffix_letter(names[n - 1], named) if len(named) > 1 else ""
    return label


def catalog_dir() -> Path:
    return ROOT / "database" / "shared" / "custom_label"


def backup(path: Path, stamp: str) -> Path:
    dest = ROOT / "backups" / "custom-label" / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def main() -> None:
    folder = catalog_dir()
    src = folder / SRC_NAME
    if not src.is_file():
        src = folder / PRIMARY_NAME
    stamp = "preSuffix_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    print("backup", backup(src, stamp))
    primary = folder / PRIMARY_NAME
    fallback = folder / FALLBACK_NAME
    if primary.is_file() and primary.resolve() != src.resolve():
        print("backup", backup(primary, "preReplace_" + stamp.split("_", 1)[1]))
    if fallback.is_file():
        print("backup", backup(fallback, "preDelete_" + stamp.split("_", 1)[1]))

    with src.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    for row in rows:
        fill_row(row)
    out = folder / (PRIMARY_NAME + ".tmp")
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    if primary.is_file() and primary.resolve() != src.resolve():
        primary.unlink()
    if src.resolve() != primary.resolve() and src.is_file():
        src.unlink()
    out.replace(primary)
    if fallback.is_file():
        fallback.unlink()
    print("primary", primary)
    print("rows", len(rows))


if __name__ == "__main__":
    main()
