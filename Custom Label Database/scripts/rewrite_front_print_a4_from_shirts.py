"""Rewrite Front Print A4 Size References (+ matching CL) to Shirts Print Sizes mm.

Scope (supervisor 2026-09-22):
  - Size References: mock+UID rows, Printing Position = Front Print, Printing Size = A4
    (blank paper treated as A4), no pocket/sleeve Suffix.
  - Custom Label: same M##-UID labels — Width 1 / Height 1 only when Position 1 is front
    (or blank name with Front Center / Front Print style Print Positions).

Does not touch pocket 80x100, A3 paper rows, multi-position non-front slots.

  python scripts/rewrite_front_print_a4_from_shirts.py --dry-run
  python scripts/rewrite_front_print_a4_from_shirts.py
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent
_APP = _SCRIPT.parent
_ROOT = _APP.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_SCRIPT))

from fill_from_seeds import (  # noqa: E402
    DEFAULT_PRINT_SIZES,
    clean,
    load_print_sizes,
    map_print_sizes_key,
    to_num,
)
from shared import paths as wh  # noqa: E402

RE_SR_KEY = re.compile(r"^(M\d+)\s*\((\d+)\)\s*$", re.I)
RE_CL_KEY = re.compile(r"^(M\d+)-(\d+)$", re.I)
POCKET_SUFFIX = frozenset({"P", "S", "S1", "S2"})


def map_size(size: str, ps: dict) -> str:
    key = map_print_sizes_key(size)
    if key and key in ps:
        return key
    s = clean(size)
    aliases = {
        "xs": "Small",
        "extra small": "Small",
        "s": "Small",
        "m": "Medium",
        "l": "Large",
        "small": "Small",
        "medium": "Medium",
        "large": "Large",
        "xl": "XL",
        "2xl": "2XL",
        "xxl": "2XL",
        "3xl": "3XL",
        "4xl": "4XL",
        "5xl": "5XL",
        "14-15y": "Small",
        "14-15 years": "Small",
        "12-14 years": "Small",
        "12-14y": "Small",
    }
    a = aliases.get(s.casefold(), "")
    if a in ps:
        return a
    m = re.match(r"^(\d+)-(\d+)Y$", s, re.I)
    if m:
        age = f"{m.group(1)}-{m.group(2)} Years"
        k2 = map_print_sizes_key(age)
        if k2 in ps:
            return k2
        for pk in ps:
            if age.casefold() in pk.casefold():
                return pk
    return ""


def expected_a4(size: str, ps: dict) -> tuple[int, int] | None:
    key = map_size(size, ps)
    if not key or "A4" not in ps[key]:
        return None
    w, h = ps[key]["A4"]
    return int(w), int(h)


def _is_front_pos_name(name: str) -> bool:
    n = clean(name).casefold()
    if not n:
        return True
    if "pocket" in n or "chest" in n or "sleeve" in n:
        return False
    if "back" in n and "front" not in n:
        return False
    return "front" in n or n in ("front center", "front print", "front centre")


def _cl_is_front_slot1(row: dict) -> bool:
    pos1 = clean(row.get("Position 1 Name"))
    if pos1:
        return _is_front_pos_name(pos1)
    pp = clean(row.get("Print Positions")).casefold()
    if not pp:
        return True
    if "pocket" in pp or "chest" in pp:
        return False
    if "back" in pp and "front" not in pp:
        return False
    return "front" in pp


def rewrite_sr(path: Path, ps: dict, *, dry_run: bool) -> tuple[int, int, list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    changed = 0
    unchanged = 0
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
        bak_dir = path.parent / "backups"
        bak_dir.mkdir(exist_ok=True)
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

    changed = 0
    unchanged = 0
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
        bak_dir = path.parent / "backups"
        bak_dir.mkdir(exist_ok=True)
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--print-sizes", type=Path, default=DEFAULT_PRINT_SIZES)
    args = ap.parse_args(argv)

    ps = load_print_sizes(args.print_sizes)
    sr_path = wh.custom_label_support_dir() / "Size References.csv"
    if not sr_path.is_file():
        sr_path = Path(r"database/custom-label-database/support/Size References.csv")
    cl_path = wh.cl_csv_path()

    mode = "DRY-RUN" if args.dry_run else "WRITE"
    print(f"=== Rewrite Front Print A4 from Shirts Print Sizes ({mode}) ===", flush=True)
    print(f"  SR: {sr_path}", flush=True)
    print(f"  CL: {cl_path}", flush=True)
    print(f"  Print sizes: {args.print_sizes}", flush=True)

    sr_c, sr_ok, sr_s = rewrite_sr(sr_path, ps, dry_run=args.dry_run)
    cl_c, cl_ok, cl_s = rewrite_cl(cl_path, ps, dry_run=args.dry_run)
    print(f"SR changed={sr_c:,} already_ok={sr_ok:,}", flush=True)
    for s in sr_s:
        print(f"  SR {s}", flush=True)
    print(f"CL changed={cl_c:,} already_ok={cl_ok:,}", flush=True)
    for s in cl_s:
        print(f"  CL {s}", flush=True)
    if args.dry_run:
        print("Dry-run: no write.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
