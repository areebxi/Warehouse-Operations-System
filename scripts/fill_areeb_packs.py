"""Fill Areeb columns on Packs Database (blank-only)."""

from __future__ import annotations

import csv
from collections import defaultdict

from fill_areeb_util import backup_file, count_write, print_stats
from shared import paths as wh
from shared.areeb_taxonomy import AREEB_COLS, AreebCatalogs, apply_areeb, cell


def _read_csv(path):
    last: Exception | None = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open(encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return enc, list(reader.fieldnames or []), list(reader)
        except UnicodeDecodeError as exc:
            last = exc
    raise last or RuntimeError(f"Could not decode {path}")


def fill_packs(cat: AreebCatalogs, *, dry_run: bool) -> dict[str, int]:
    path = wh.packs_database_path()
    enc, headers, rows = _read_csv(path)
    for col in AREEB_COLS:
        if col not in headers:
            raise SystemExit(f"Packs Database missing column {col!r}")
    stats: dict[str, int] = defaultdict(int)
    samples: list[str] = []
    changed = False
    for row in rows:
        item1 = cell(row.get("Item 1 SKU"))
        pcode = cell(row.get("Product Code"))
        child = cell(row.get("Channel Child SKU"))
        current = {col: cell(row.get(col)) for col in AREEB_COLS}
        values = cat.classify_packs(item1_sku=item1, product_code=pcode, channel_child_sku=child)
        patch = apply_areeb(current, values)
        stats["rows"] += 1
        if not patch:
            if not any(current.values()) and not values.any_filled():
                stats["blank_miss"] += 1
            else:
                stats["already_or_empty_incoming"] += 1
            continue
        count_write(stats, values.source, len(patch))
        changed = True
        if len(samples) < 8:
            samples.append(f"child={child} item1={item1} src={values.source} {patch}")
        if not dry_run:
            row.update(patch)
    print("Packs Database:", path)
    print_stats(stats, samples)
    if dry_run or not changed:
        return dict(stats)
    bak = backup_file(path, wh.packs_database_archive_dir())
    print(f"  backup {bak}")
    with path.open("w", encoding=enc, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, lineterminator="\r\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("  wrote", path)
    return dict(stats)
