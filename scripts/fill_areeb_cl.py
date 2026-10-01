"""Fill Areeb columns on Custom Label CSV."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from fill_areeb_util import backup_file, count_write, print_stats
from shared import paths as wh
from shared.areeb_taxonomy import AREEB_COLS, AreebValues, apply_areeb, cell, classify_cl


def cl_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = [{k: cell(v) for k, v in row.items()} for row in reader]
    return headers, rows


def fill_cl(*, dry_run: bool) -> tuple[dict[str, int], list[dict[str, str]]]:
    path = wh.cl_csv_path()
    headers, rows = cl_rows(path)
    for col in AREEB_COLS:
        if col not in headers:
            raise SystemExit(f"CL missing column {col!r}")
    stats: dict[str, int] = defaultdict(int)
    samples: list[str] = []
    classified: list[tuple[dict[str, str], AreebValues]] = []
    cleared_style: Counter[str] = Counter()
    for row in rows:
        values = classify_cl(row)
        patch = apply_areeb(row, values)
        stats["rows"] += 1
        classified.append((row, values))
        if not patch:
            if not any(cell(row.get(c)) for c in AREEB_COLS) and not values.any_filled():
                stats["blank_miss"] += 1
            else:
                stats["already_or_empty_incoming"] += 1
            continue
        count_write(stats, values.source, len(patch))
        for col, val in patch.items():
            if not val:
                stats[f"cleared_{col}"] += 1
                if col == "Product Style (Areeb)":
                    old = cell(row.get(col)) or "(blank)"
                    ga = cell(row.get("Gender Apparel")) or "(blank GA)"
                    cleared_style[f"{old} | {ga}"] += 1
        if len(samples) < 8:
            samples.append(f"label={row.get('Custom Label')} src={values.source} {patch}")
        if not dry_run:
            row.update(patch)
    print("Custom Label:", path)
    print_stats(stats, samples)
    if cleared_style:
        print("  Product Style cleared (top 12 old | Gender Apparel):")
        for k, n in cleared_style.most_common(12):
            print(f"    {n:6,}  {k}")
    leftover_rows = [row for row, val in classified if not val.category]
    if dry_run:
        return dict(stats), leftover_rows
    bak = backup_file(path, wh.cl_backups_dir())
    print(f"  backup {bak}")
    try:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print("  wrote", path)
        fallback = path.with_name(path.stem + "_write_fallback" + path.suffix)
        if fallback.is_file():
            fallback.unlink()
    except PermissionError:
        fallback = path.with_name(path.stem + "_write_fallback" + path.suffix)
        with fallback.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        print("  live locked, wrote", fallback)
    return dict(stats), leftover_rows
