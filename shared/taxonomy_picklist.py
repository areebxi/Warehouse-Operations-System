"""Closed pick-lists for the four Areeb columns plus PE subcategory.

Hashim #038: when a product arrives, pick only from these values.
Do not invent a new cell. Add a row to the CSV to allow a new value.

CL fill snaps Category / Product Type / Product Style / Department.
Plain leftover does not snap — Plain / Packs copy supplier product data.
Grouping does not unmatched an already-filled catalog cell that is off-list.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from shared.paths import sorter_taxonomy_picklists_path

DIM_CATEGORY = "category"
DIM_SUBCATEGORY = "subcategory"
DIM_PRODUCT_TYPE = "product_type"
DIM_PRODUCT_STYLE = "product_style"
DIM_DEPARTMENT = "department"

DIMENSIONS = (
    DIM_CATEGORY,
    DIM_SUBCATEGORY,
    DIM_PRODUCT_TYPE,
    DIM_PRODUCT_STYLE,
    DIM_DEPARTMENT,
)

HEADER = ("dimension", "value", "maps_to", "source")


def cell(value: object) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.casefold() in {"nan", "none"}:
        return ""
    return s


def _fold(value: object) -> str:
    return cell(value).casefold()


@lru_cache(maxsize=1)
def load(path: Path | None = None) -> dict[str, dict[str, str]]:
    """dimension → casefold → canonical spelling."""
    src = path or sorter_taxonomy_picklists_path()
    if not src.is_file():
        raise FileNotFoundError(f"taxonomy pick-list missing: {src}")
    out: dict[str, dict[str, str]] = {d: {} for d in DIMENSIONS}
    with src.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dim = _fold(row.get("dimension"))
            value = cell(row.get("value"))
            if dim not in out or not value:
                continue
            canonical = cell(row.get("maps_to")) or value
            folded = value.casefold()
            if folded not in out[dim]:
                out[dim][folded] = canonical
            canon_fold = canonical.casefold()
            if canon_fold not in out[dim]:
                out[dim][canon_fold] = canonical
    return out


def pick(dimension: str, value: object, *, path: Path | None = None) -> str:
    """Canonical list value, or blank if not on the list."""
    raw = cell(value)
    if not raw:
        return ""
    dim = _fold(dimension)
    table = load(path).get(dim) or {}
    return table.get(raw.casefold(), "")


def allowed(dimension: str, *, path: Path | None = None) -> frozenset[str]:
    return frozenset(load(path).get(_fold(dimension), {}).values())


def snap_warehouse(
    *,
    category: object = "",
    product_type: object = "",
    product_style: object = "",
    department: object = "",
    path: Path | None = None,
) -> tuple[str, str, str, str]:
    """Snap Areeb warehouse cells. Unknown → blank (do not invent)."""
    return (
        pick(DIM_CATEGORY, category, path=path),
        pick(DIM_PRODUCT_TYPE, product_type, path=path),
        pick(DIM_PRODUCT_STYLE, product_style, path=path),
        pick(DIM_DEPARTMENT, department, path=path),
    )
