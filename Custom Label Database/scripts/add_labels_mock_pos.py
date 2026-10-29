"""Mock Custom Label Print Positions from Mocks Database (never Front Center default)."""
from __future__ import annotations

import csv
import re
from functools import lru_cache

from generate_mocks_util import clean, map_print_positions
from shared.paths import mocks_database_csv_path

RE_LEADING_MOCK = re.compile(r"^(M\d+)\b", re.I)
RE_MOCK_SUFFIX = re.compile(r"\s*\(M\d+\)\s*$", re.I)


@lru_cache(maxsize=1)
def mock_print_positions_map() -> dict[str, str]:
    path = mocks_database_csv_path()
    out: dict[str, str] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            mid = clean(row.get("Pasting Mocks ID")).upper()
            if not re.fullmatch(r"M\d+", mid):
                continue
            mapped = map_print_positions(row.get("Printing Position", ""), mid)
            if mapped:
                out[mid] = mapped
    return out


def leading_mock_id(label: str) -> str | None:
    m = RE_LEADING_MOCK.match(clean(label))
    return m.group(1).upper() if m else None


def first_position_name(mapped: str) -> str:
    head = mapped.split(",", 1)[0].strip()
    return RE_MOCK_SUFFIX.sub("", head).strip()


def apply_mock_print_positions(label: str, row: dict[str, str]) -> None:
    """Overwrite Print Positions from Mocks when label is M##… and mocks mapped."""
    mid = leading_mock_id(label)
    if not mid:
        return
    mapped = mock_print_positions_map().get(mid)
    if not mapped:
        # blank/unmapped mocks → do not invent Front Center
        return
    row["Print Positions"] = mapped
    if "Position 1 Name" in row:
        row["Position 1 Name"] = first_position_name(mapped)
