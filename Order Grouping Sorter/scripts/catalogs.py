"""Load the three grouping catalogs (read-only).

CL key = after first dash → Custom Label; if the SKU has no dash, whole SKU
(not universal resolve_label).
Plain key = till last dash or whole SKU → SKU.
Packs key = whole SKU → Channel Child SKU.
Plain / Packs use disk cache (see catalog_cache.py).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import Mapping, Optional

from shared import cl_columns as clc
from shared import paths as wh
from shared.areeb_taxonomy import cell
from shared.cl_sku_match import key_after_first_dash, key_till_last_dash

from catalog_cache import load_xlsx_index

PLAIN_SHEET = "Sheet1"
PACKS_SHEET = "01-Database"

SRC_CL = "cl"
SRC_PLAIN = "plain"
SRC_PACKS = "packs"


def _fold(value: object) -> str:
    return cell(value).casefold()


def _index_rows(rows: list[dict[str, str]], key_col: str) -> dict[str, dict[str, str]]:
    idx: dict[str, dict[str, str]] = {}
    for row in rows:
        key = _fold(row.get(key_col))
        if key and key not in idx:
            idx[key] = row
    return idx


def load_cl_index(path=None) -> dict[str, dict[str, str]]:
    csv_path = path or wh.cl_csv_path()
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rename = clc.rename_legacy_headers(
            [name for name in (reader.fieldnames or []) if name]
        )
        rows = [
            clc.normalize_cl_record(
                {k: cell(v) for k, v in row.items() if k}, rename
            )
            for row in reader
        ]
    return _index_rows(rows, clc.CUSTOM_LABEL)


@dataclass
class Catalogs:
    cl: dict[str, dict[str, str]] = field(default_factory=dict)
    plain: dict[str, dict[str, str]] = field(default_factory=dict)
    packs: dict[str, dict[str, str]] = field(default_factory=dict)

    def lookup_cl(self, sku: object) -> Optional[dict[str, str]]:
        after = _fold(key_after_first_dash(sku))
        if after:
            return self.cl.get(after)
        # Supervisor 2026-09-22: no-dash SKUs (A515, …) match Custom Label whole.
        whole = _fold(sku)
        if whole:
            return self.cl.get(whole)
        return None

    def lookup_plain(self, sku: object) -> Optional[dict[str, str]]:
        till = _fold(key_till_last_dash(sku))
        if till and till in self.plain:
            return self.plain[till]
        whole = _fold(sku)
        if whole:
            return self.plain.get(whole)
        return None

    def lookup_packs(self, sku: object) -> Optional[dict[str, str]]:
        whole = _fold(sku)
        if whole:
            return self.packs.get(whole)
        return None

    def attribute_row(self, sku: object) -> tuple[Optional[str], Optional[Mapping[str, str]]]:
        """Packs whole → else CL after-first → else Plain. Separate from finish gate."""
        packs = self.lookup_packs(sku)
        if packs is not None:
            return SRC_PACKS, packs
        cl = self.lookup_cl(sku)
        if cl is not None:
            return SRC_CL, cl
        plain = self.lookup_plain(sku)
        if plain is not None:
            return SRC_PLAIN, plain
        return None, None


def load_catalogs() -> Catalogs:
    return Catalogs(
        cl=load_cl_index(),
        plain=load_xlsx_index(
            wh.plain_database_path(), PLAIN_SHEET, "SKU", cache_stem="plain"
        ),
        packs=load_xlsx_index(
            wh.packs_database_path(),
            PACKS_SHEET,
            "Channel Child SKU",
            cache_stem="packs",
        ),
    )
