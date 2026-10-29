"""Repair Areeb mock Print Positions from Mocks Database (prefer live when match).

Default dry-run. --run writes Areeb only after backup. Live NocoDB untouched.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DIR = Path(__file__).resolve().parent
for p in (_ROOT, _DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fix_areeb_mock_pos_lib import (  # noqa: E402
    expected_pp,
    leading_mock_id,
    norm_pp,
    prefer_live_or_mocks,
)
from fix_areeb_pos_lib import AREEB_CL, LIVE_CL, live_get  # noqa: E402
from generate_mocks_util import clean  # noqa: E402
from shared.paths import mocks_database_csv_path  # noqa: E402
from shared.paths.catalog import cl_areeb_csv_path, cl_backups_dir, cl_csv_path  # noqa: E402


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def load_mocks_raw() -> dict[str, str]:
    out: dict[str, str] = {}
    with mocks_database_csv_path().open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            mid = clean(row.get("Pasting Mocks ID")).upper()
            if re.fullmatch(r"M\d+", mid) and mid not in out:
                out[mid] = clean(row.get("Printing Position"))
    return out


def live_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        cl = live_get(r, LIVE_CL, AREEB_CL)
        if cl and cl not in out:
            out[cl] = r
    return out


def process(*, dry_run: bool) -> dict:
    fields, areeb = load_csv(cl_areeb_csv_path())
    live_by = live_index(load_csv(cl_csv_path())[1])
    mocks_raw = load_mocks_raw()
    by_mock: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    samples: list[str] = []
    changed = 0

    for row in areeb:
        lab = clean(row.get(AREEB_CL))
        mid = leading_mock_id(lab)
        if not mid:
            continue
        mapped = expected_pp(mocks_raw, mid)
        if not mapped:
            continue
        cur = clean(row.get("Print Positions"))
        if norm_pp(cur) == norm_pp(mapped):
            continue
        src = prefer_live_or_mocks(row, live_by.get(lab), mapped, "Print_Positions")
        changed += 1
        by_mock[mid] += 1
        sources[src] += 1
        if len(samples) < 12:
            samples.append(f"{lab}: {cur!r} -> {row.get('Print Positions')!r} ({src})")

    if not dry_run and changed:
        bak = cl_backups_dir() / (
            f"Custom_Label_Database (Areeb)_preMockPos_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cl_areeb_csv_path(), bak)
        tmp = cl_areeb_csv_path().with_suffix(".tmp.csv")
        with tmp.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(areeb)
        tmp.replace(cl_areeb_csv_path())
        print(f"backup: {bak}", flush=True)

    return {
        "changed": changed,
        "by_mock": by_mock,
        "sources": sources,
        "samples": samples,
        "dry_run": dry_run,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true", help="Write Areeb CSV (default dry-run)")
    args = ap.parse_args()
    stats = process(dry_run=not args.run)
    mode = "DRY-RUN" if stats["dry_run"] else "WROTE"
    print(f"{mode}: changed={stats['changed']:,} sources={dict(stats['sources'])}", flush=True)
    for mid, n in stats["by_mock"].most_common(15):
        print(f"  {mid}: {n}", flush=True)
    for s in stats["samples"]:
        print(f"  sample {s}", flush=True)


if __name__ == "__main__":
    main()
