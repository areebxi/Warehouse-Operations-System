"""Rewrite SR / CL rows for front-print A4 mm."""
from __future__ import annotations

import csv
import shutil
from datetime import datetime
from pathlib import Path

from fill_from_seeds import clean, to_num
from shared.paths import cl_backups_dir, size_references_backups_dir
from rewrite_front_a4_map import (
    POCKET_SUFFIX,
    RE_CL_KEY,
    RE_SR_KEY,
    _cl_is_front_slot1,
    expected_a4,
)


def rewrite_sr(path: Path, ps: dict, *, dry_run: bool) -> tuple[int, int, list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    changed = unchanged = 0
    samples: list[str] = []
    for row in rows:
        sku = clean(row.get("SKU Value"))
        if not RE_SR_KEY.match(sku):
            continue
        if clean(row.get("Printing Position")).casefold() != "front print":
            continue
        if clean(row.get("Suffix")).upper() in POCKET_SUFFIX:
            continue
        psize = clean(row.get("Printing Size")).upper() or "A4"
        if psize != "A4":
            continue
        exp = expected_a4(clean(row.get("Size")), ps)
        if exp is None:
            continue
        exp_w, exp_h = exp
        w = to_num(row.get("Size Width"))
        h = to_num(row.get("Size Height"))
        if w is not None and h is not None and int(w) == exp_w and int(h) == exp_h:
            unchanged += 1
            continue
        old = f"{'' if w is None else int(w)}x{'' if h is None else int(h)}"
        row["Size Width"] = str(exp_w)
        row["Size Height"] = str(exp_h)
        changed += 1
        if len(samples) < 12:
            samples.append(f"{sku} {clean(row.get('Size'))} {old} -> {exp_w}x{exp_h}")

    if not dry_run and changed:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_dir = size_references_backups_dir()
        bak_dir.mkdir(parents=True, exist_ok=True)
        bak = bak_dir / f"Size_References_preRewriteFrontA4_{stamp}.csv"
        shutil.copy2(path, bak)
        print(f"SR backup: {bak}", flush=True)
        tmp = path.with_suffix(".tmp.csv")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({c: row.get(c, "") for c in fields})
        tmp.replace(path)
    return changed, unchanged, samples


def rewrite_cl(path: Path, ps: dict, *, dry_run: bool) -> tuple[int, int, list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    changed = unchanged = 0
    samples: list[str] = []
    for row in rows:
        lab = clean(row.get("Custom Label"))
        if not RE_CL_KEY.match(lab):
            continue
        if not _cl_is_front_slot1(row):
            continue
        exp = expected_a4(clean(row.get("Size")), ps)
        if exp is None:
            continue
        exp_w, exp_h = exp
        w = to_num(row.get("Width 1 (mm)"))
        h = to_num(row.get("Height 1 (mm)"))
        if w is not None and h is not None and int(w) == exp_w and int(h) == exp_h:
            unchanged += 1
            continue
        old = f"{'' if w is None else int(w)}x{'' if h is None else int(h)}"
        row["Width 1 (mm)"] = str(exp_w)
        row["Height 1 (mm)"] = str(exp_h)
        changed += 1
        if len(samples) < 12:
            samples.append(f"{lab} {clean(row.get('Size'))} {old} -> {exp_w}x{exp_h}")

    if not dry_run and changed:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_dir = cl_backups_dir()
        bak_dir.mkdir(parents=True, exist_ok=True)
        bak = bak_dir / f"Custom_Label_Database_preRewriteFrontA4_{stamp}.csv"
        shutil.copy2(path, bak)
        print(f"CL backup: {bak}", flush=True)
        tmp = path.with_suffix(".tmp.csv")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({c: row.get(c, "") for c in fields})
        tmp.replace(path)
    return changed, unchanged, samples
