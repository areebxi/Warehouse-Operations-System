"""Write the closed taxonomy pick-lists (Hashim #038).

  python scripts/build_taxonomy_picklists.py --dry-run
  python scripts/build_taxonomy_picklists.py

Curated warehouse lists in shared/taxonomy_catalog.py.
Do not re-harvest catalogs to discover ad hoc inventions.
To allow a new value, add it there (and a maps_to alias if an old spelling must snap).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import paths as wh
from shared.taxonomy_catalog import csv_rows
from shared.taxonomy_picklist import DIMENSIONS, HEADER, load


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rows = csv_rows()
    counts = {d: 0 for d in DIMENSIONS}
    aliases = {d: 0 for d in DIMENSIONS}
    for dim, _value, maps_to, _src in rows:
        if maps_to:
            aliases[dim] += 1
        else:
            counts[dim] += 1
    dest = wh.sorter_taxonomy_picklists_path()
    print(f"canonical + aliases -> {dest}")
    for dim in DIMENSIONS:
        print(f"  {dim}: {counts[dim]} canonical, {aliases[dim]} aliases")
    if args.dry_run:
        print("dry-run — not written")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    load.cache_clear()
    print(f"wrote {len(rows)} rows")


if __name__ == "__main__":
    main()
