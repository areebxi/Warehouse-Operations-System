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
from scripts.rewrite_front_print_a4_from_shirts_impl import rewrite_sr, rewrite_cl, map_size, _cl_is_front_slot1, _is_front_pos_name, expected_a4

RE_SR_KEY = re.compile(r"^(M\d+)\s*\((\d+)\)\s*$", re.I)
RE_CL_KEY = re.compile(r"^(M\d+)-(\d+)$", re.I)
POCKET_SUFFIX = frozenset({"P", "S", "S1", "S2"})


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
