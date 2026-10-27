"""Set ISO paper print mm on Areeb CL rows that are A3/A4/A5/A6.

Detect paper from Size (exact or token), then a dash token on Custom Label
(leading A3/A4/… only if iron-on/sticker/acrylic/photo/transfer or Size/GA
already confirms paper — skips design prefixes like A3-F/B-…), then Gender
Apparel. Front/Back Center → paper mm; pocket → 80×100; sleeve → 100×100.
"""
from __future__ import annotations

import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.paths.catalog import cl_areeb_csv_path, cl_backups_dir

PAPER = {"A3": ("297", "420"), "A4": ("210", "297"), "A5": ("148", "210"), "A6": ("105", "148")}
TOKEN = re.compile(r"(?<![A-Za-z0-9])(A[3456])(?![A-Za-z0-9])", re.I)
PAPERISH = re.compile(
    r"iron\s*-?\s*on|ironon|sticker|stckr|acrylic|photo|transfer", re.I
)


def paper_of(row: dict[str, str]) -> str | None:
    size = (row.get("Size") or "").strip()
    if size.upper() in PAPER:
        return size.upper()
    m = TOKEN.search(size)
    if m:
        return m.group(1).upper()
    cl = row.get("Custom Label") or ""
    ga = row.get("Gender Apparel") or ""
    confirmed = bool(
        PAPERISH.search(cl) or PAPERISH.search(ga) or TOKEN.search(ga) or TOKEN.search(size)
    )
    for i, tok in enumerate(p for p in cl.split("-") if p.strip()):
        t = tok.strip().upper()
        if t in PAPER and (i > 0 or confirmed):
            return t
    m = TOKEN.search(ga)
    return m.group(1).upper() if m else None


def slot_kind(name: str) -> str | None:
    n = name.strip().lower()
    if not n:
        return None
    if "pocket" in n:
        return "pocket"
    if "sleeve" in n:
        return "sleeve"
    if any(
        s in n
        for s in ("front center", "front centre", "back center", "back centre")
    ):
        return "body"
    return None


def target_mm(paper: str, kind: str) -> tuple[str, str]:
    if kind == "pocket":
        return "80", "100"
    if kind == "sleeve":
        return "100", "100"
    return PAPER[paper]


def rewrite(path: Path, *, dry_run: bool) -> dict[str, int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    counts = {
        "matched": 0, "rows": 0, "slots": 0,
        "body": 0, "pocket": 0, "sleeve": 0, "was_blank": 0,
    }
    for row in rows:
        paper = paper_of(row)
        if not paper:
            continue
        counts["matched"] += 1
        touched = False
        for i in range(1, 5):
            kind = slot_kind(row.get(f"Position {i} Name") or "")
            if not kind:
                continue
            w, h = target_mm(paper, kind)
            if not (row.get(f"Width {i} (mm)") or "").strip():
                counts["was_blank"] += 1
            if row.get(f"Width {i} (mm)") == w and row.get(f"Height {i} (mm)") == h:
                continue
            row[f"Width {i} (mm)"] = w
            row[f"Height {i} (mm)"] = h
            counts["slots"] += 1
            counts[kind] += 1
            touched = True
        counts["rows"] += touched
    if dry_run or not counts["slots"]:
        return counts
    bak = cl_backups_dir()
    bak.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, bak / f"{path.stem}_prePaperSizes_{stamp}{path.suffix}")
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
