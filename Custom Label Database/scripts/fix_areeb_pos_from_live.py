"""Fix Areeb CL print positions: live FC restore, A3-B-M-T back, named FC.

Areeb only. Live NocoDB untouched. See plan Fix Areeb positions.
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DIR = Path(__file__).resolve().parent
for p in (_ROOT, _DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fix_areeb_pos_lib import (
    AREEB_CL,
    LIVE_CL,
    copy_print_from_live,
    live_get,
    mm_ok,
    peer_front_mm,
    sole_center,
)
from shared.paths.catalog import cl_areeb_csv_path, cl_backups_dir, cl_csv_path

FORCE_FC = frozenset(
    {
        "1-K-T-WHI-YL",
        "1-K-T-WHI-YXL",
        "1-K-T-WHI-YM",
        "LG-W-T-WHI-XL",
        "LG-W-T-WHI-2XL",
        "LG-W-T-BLK-S",
        "I-CRD-WHT-A5-Yes",
        "BG747-201257-Yes",
    }
)


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def live_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        cl = live_get(r, LIVE_CL, AREEB_CL)
        if cl and cl not in out:
            out[cl] = r
    return out


def load_fc_restore(path: Path) -> frozenset[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return frozenset(x.strip() for x in lines if x.strip())


def pick_mm(row: dict[str, str], areeb_rows: list[dict[str, str]]) -> tuple[str, str]:
    w = (row.get("Width 1 (mm)") or "").strip()
    h = (row.get("Height 1 (mm)") or "").strip()
    if mm_ok(w, h):
        return w, h
    # try other filled slots
    for n in range(1, 5):
        w = (row.get(f"Width {n} (mm)") or "").strip()
        h = (row.get(f"Height {n} (mm)") or "").strip()
        if mm_ok(w, h):
            return w, h
    peer = peer_front_mm(
        areeb_rows,
        (row.get("Size") or "").strip(),
        (row.get("Gender Apparel") or "").strip(),
    )
    if peer:
        return peer
    # keep slot-1 even if pocket-sized (e.g. keyring) rather than blank
    w1 = (row.get("Width 1 (mm)") or "").strip()
    h1 = (row.get("Height 1 (mm)") or "").strip()
    if w1 and h1:
        return w1, h1
    return w or "", h or ""


def process(*, dry_run: bool, fc_list: Path) -> dict:
    areeb_path = cl_areeb_csv_path()
    fields, areeb = load_csv(areeb_path)
    live_by = live_index(load_csv(cl_csv_path())[1])
    fc_restore = load_fc_restore(fc_list)

    stats = {
        "restored_from_live": 0,
        "a3b_back": 0,
        "force_fc": 0,
        "missing_live": 0,
    }
    missing: list[str] = []

    for row in areeb:
        cl = (row.get(AREEB_CL) or "").strip()
        if not cl:
            continue

        if cl.upper().startswith("A3-B-M-T-"):
            w, h = pick_mm(row, areeb)
            sole_center(row, back=True, width=w, height=h)
            stats["a3b_back"] += 1
            continue

        if cl in FORCE_FC:
            w, h = pick_mm(row, areeb)
            sole_center(row, back=False, width=w, height=h)
            stats["force_fc"] += 1
            continue

        if cl in fc_restore:
            src = live_by.get(cl)
            if not src:
                stats["missing_live"] += 1
                missing.append(cl)
                continue
            copy_print_from_live(row, src)
            # Design Image Suffix is Areeb-only; sole Front from live → blank suffixes
            for n in range(1, 5):
                col = f"Design Image Suffix {n}"
                if col in row:
                    row[col] = ""
            stats["restored_from_live"] += 1

    stats["missing_samples"] = missing[:10]
    if dry_run:
        return stats

    bak = cl_backups_dir()
    bak.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(
        areeb_path, bak / f"{areeb_path.stem}_prePosFix_{stamp}{areeb_path.suffix}"
    )
    tmp = areeb_path.with_suffix(".tmp.csv")
    with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(areeb)
    tmp.replace(areeb_path)
    stats["backup"] = f"{areeb_path.stem}_prePosFix_{stamp}{areeb_path.suffix}"
    return stats


def main() -> None:
    dry = "--run" not in sys.argv
    fc_list = Path(__file__).resolve().parent / "data" / "areeb_fc_restore_labels.txt"
    if not fc_list.exists():
        # fallback: agent-tools list from scan
        fc_list = Path(
            r"C:/Users/admin/.cursor/projects/d-Areeb-Work-Warehouse-Operations-System"
            r"/agent-tools/fc_restore_list.txt"
        )
    stats = process(dry_run=dry, fc_list=fc_list)
    print(("dry-run " if dry else "wrote ") + str(stats))


if __name__ == "__main__":
    main()
