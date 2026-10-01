"""Shared helpers for fill_areeb_taxonomy."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from shared.areeb_taxonomy import cell

PLAIN_SHEET = "Sheet1"
PACKS_SHEET = "01-Database"
SS_STATUSES = ("shipped", "awaiting_shipment")


def backup_file(path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{path.stem}.bak_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def header_index(headers: list[str]) -> dict[str, int]:
    return {h: i for i, h in enumerate(headers) if h}


def row_dict(headers: list[str], values: tuple) -> dict[str, object]:
    out: dict[str, object] = {}
    for i, h in enumerate(headers):
        if not h:
            continue
        out[h] = values[i] if i < len(values) else ""
    return out


def count_write(stats: dict[str, int], source: str, n_cells: int) -> None:
    stats["rows_touched"] += 1
    stats[f"src_{source or 'none'}"] += 1
    stats["cells_filled"] += n_cells


def print_stats(stats: dict[str, int], samples: list[str]) -> None:
    for k in sorted(stats):
        print(f"  {k}: {stats[k]:,}")
    for s in samples:
        print("  sample:", s[:220])
