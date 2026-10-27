"""Dedupe Areeb CL by Custom Label; fix K-T youth Mens + lone Back Center.

Keep rule: token match to Custom Label first; then long supplier GA over short
canonical; then most filled key fields; then first row. See dedupe_areeb_cl_lib.
"""
from __future__ import annotations

import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DIR = Path(__file__).resolve().parent
for p in (_ROOT, _DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from dedupe_areeb_cl_lib import fix_kt_mens_youth, fix_lone_back, pick_winner
from shared.paths.catalog import cl_areeb_csv_path, cl_backups_dir


def process(path: Path, *, dry_run: bool) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    by_cl: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    blanks: list[dict] = []
    for i, r in enumerate(rows):
        cl = (r.get("Custom Label") or "").strip()
        if not cl:
            blanks.append(r)
            continue
        by_cl[cl].append((i, r))

    win_map: dict[str, dict] = {}
    dropped = 0
    dup_groups = 0
    for cl, indexed in by_cl.items():
        if len(indexed) == 1:
            win_map[cl] = indexed[0][1]
            continue
        dup_groups += 1
        _, win = pick_winner(cl, indexed)
        win_map[cl] = win
        dropped += len(indexed) - 1

    order: list[str] = []
    seen: set[str] = set()
    for r in rows:
        cl = (r.get("Custom Label") or "").strip()
        if cl and cl not in seen:
            seen.add(cl)
            order.append(cl)
    out = [win_map[cl] for cl in order] + blanks

    kt_log = fix_kt_mens_youth(out)
    back_log = fix_lone_back(out)
    stats = {
        "in_rows": len(rows),
        "out_rows": len(out),
        "dup_groups": dup_groups,
        "dropped": dropped,
        "kt_mens_fixed": len(kt_log),
        "back_to_front": len(back_log),
        "kt_samples": kt_log[:12],
        "back_samples": back_log[:12],
    }
    if dry_run:
        return stats

    bak = cl_backups_dir()
    bak.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, bak / f"{path.stem}_preDedupe_{stamp}{path.suffix}")
    tmp = path.with_suffix(".tmp.csv")
    with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(out)
    tmp.replace(path)
    stats["backup"] = f"{path.stem}_preDedupe_{stamp}{path.suffix}"
    return stats


def main() -> None:
    dry = "--run" not in sys.argv
    stats = process(cl_areeb_csv_path(), dry_run=dry)
    summary = {
        k: v for k, v in stats.items() if k not in ("kt_samples", "back_samples")
    }
    print(("dry-run " if dry else "wrote ") + str(summary))
    if stats.get("kt_samples"):
        print("kt_mens_fixed samples:")
        for row in stats["kt_samples"]:
            print(" ", row)
    if stats.get("back_samples"):
        print("back_to_front samples:")
        for row in stats["back_samples"]:
            print(" ", row)


if __name__ == "__main__":
    main()
