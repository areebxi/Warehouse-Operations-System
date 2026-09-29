"""Load fixed-batch table (B80 / B100 / …).

Live file: database/order-grouping-sorter/fixed_batches.csv
(path: shared.paths.sorter_fixed_batches_path).

Criteria columns (Graph order). Cell `any` / `x` / blank = do not care.
`product-type` tokens `ss_fotl` / `iron_on` / `gildan_tee` / `mug` / `babysuit` / `packs`
use the line predicates in grouping.py; a literal type may list values with `;`.
Contains / not-contains cells are `;` lists (any needle hits). SKU needle `=M61` = whole
dash-separated SKU part; otherwise case-insensitive substring.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import shared.paths as wh

# Blank / any / x = ignore this criterion when matching.
DONT_CARE = frozenset({"", "any", "x", "*"})


@dataclass(frozen=True)
class FixedBatchRow:
    batch_code: str
    name: str
    order_status: str
    ship_by_date: str  # today | future | any
    product_finish: str  # plain | printed
    order_source: str
    design_grouping: str
    shipping_service: str  # prime | non-prime | any
    printing_method: str
    customised: str
    customisation_type: str
    print_size: str
    print_position: str
    supply_method: str
    supplier: str
    package_type: str
    category: str
    product_type: str  # ss_fotl | iron_on | gildan_tee | mug | babysuit | packs | any | literal
    product_style: str
    department: str
    brand: str
    size: str
    color: str
    destination: str  # international (ship-to country not GB) | any
    item_name_contains: str  # ; list, any line
    sku_contains: str  # ; list, any line
    item_name_not_contains: str  # ; list, no line
    sku_not_contains: str  # ; list, no line
    notes: str


def _cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _fold(s: str) -> str:
    return s.casefold().strip()


def cares(val: str) -> bool:
    return _fold(val) not in DONT_CARE


def load_fixed_batches(path: Path | None = None) -> list[FixedBatchRow]:
    p = path or wh.sorter_fixed_batches_path()
    rows: list[FixedBatchRow] = []
    with p.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            code = _cell(raw, "batch_code")
            if not code:
                continue
            rows.append(
                FixedBatchRow(
                    batch_code=code,
                    name=_cell(raw, "name"),
                    order_status=_fold(_cell(raw, "order-status")),
                    ship_by_date=_fold(_cell(raw, "ship-by-date")),
                    product_finish=_fold(_cell(raw, "product-finish")),
                    order_source=_fold(_cell(raw, "order-source")),
                    design_grouping=_fold(_cell(raw, "design-grouping")),
                    shipping_service=_fold(_cell(raw, "shipping-service")),
                    printing_method=_fold(_cell(raw, "printing-method")),
                    customised=_fold(_cell(raw, "customised")),
                    customisation_type=_fold(_cell(raw, "customisation-type")),
                    print_size=_fold(_cell(raw, "print-size")),
                    print_position=_fold(_cell(raw, "print-position")),
                    supply_method=_cell(raw, "supply-method"),
                    supplier=_fold(_cell(raw, "supplier")),
                    package_type=_fold(_cell(raw, "package-type")),
                    category=_cell(raw, "category"),
                    product_type=_fold(_cell(raw, "product-type")),
                    product_style=_fold(_cell(raw, "product-style")),
                    department=_fold(_cell(raw, "department")),
                    brand=_fold(_cell(raw, "brand")),
                    size=_fold(_cell(raw, "size")),
                    color=_fold(_cell(raw, "color")),
                    destination=_fold(_cell(raw, "destination")),
                    item_name_contains=_cell(raw, "item-name-contains"),
                    sku_contains=_cell(raw, "sku-contains"),
                    item_name_not_contains=_cell(raw, "item-name-not-contains"),
                    sku_not_contains=_cell(raw, "sku-not-contains"),
                    notes=_cell(raw, "notes"),
                )
            )
    return rows


@lru_cache(maxsize=1)
def fixed_batch_table() -> tuple[FixedBatchRow, ...]:
    return tuple(load_fixed_batches())


def fixed_batch_codes() -> frozenset[str]:
    """B80 / B100 / … reserved codes."""
    return frozenset(r.batch_code for r in fixed_batch_table() if r.batch_code)


def reserved_batch_nums() -> frozenset[int]:
    nums: set[int] = set()
    for r in fixed_batch_table():
        digits = "".join(c for c in r.batch_code if c.isdigit())
        if digits:
            nums.add(int(digits))
    return frozenset(nums)


def clear_fixed_batch_cache() -> None:
    fixed_batch_table.cache_clear()
