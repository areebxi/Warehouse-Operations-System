"""AreebValues dataclass and cell/key helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from shared.areeb_taxonomy.consts import AREEB_COLS, SOURCE_CL_STANDARD, SOURCE_NONE

def cell(value: object) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in ("nan", "none", "none"):
        return ""
    if s.endswith(".0") and s[:-2].isdigit():
        return s[:-2]
    return s


def keyfold(value: object) -> str:
    return cell(value).casefold()


def _norm_ga(ga: object) -> str:
    s = cell(ga)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("TrouserLong", "Trouser Long")
    s = s.replace("Crew New", "Crewneck")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _fold_ga(ga: object) -> str:
    return _norm_ga(ga).casefold()


@dataclass(frozen=True)
class AreebValues:
    category: str = ""
    product_type: str = ""
    product_style: str = ""
    department: str = ""
    source: str = SOURCE_NONE

    def as_dict(self) -> dict[str, str]:
        return {
            "Category (Areeb)": self.category,
            "Product Type (Areeb)": self.product_type,
            "Product Style (Areeb)": self.product_style,
            "Department (Areeb)": self.department,
        }

    def any_filled(self) -> bool:
        return bool(self.category or self.product_type or self.product_style or self.department)

    def all_filled(self) -> bool:
        return bool(self.category and self.product_type and self.product_style and self.department)


def coalesce_areeb(base: AreebValues, extra: AreebValues) -> AreebValues:
    """Keep supplier cells; fill only the holes from leftover."""
    if not extra.any_filled() or base.all_filled():
        return base
    return AreebValues(
        category=base.category or extra.category,
        product_type=base.product_type or extra.product_type,
        product_style=base.product_style or extra.product_style,
        department=base.department or extra.department,
        source=base.source or extra.source,
    )


def from_src_row(row: Mapping[str, Any], src_map: dict[str, str], source: str) -> AreebValues:
    picked = {areeb: cell(row.get(src)) for areeb, src in src_map.items()}
    return AreebValues(
        category=picked["Category (Areeb)"],
        product_type=picked["Product Type (Areeb)"],
        product_style=picked["Product Style (Areeb)"],
        department=picked["Department (Areeb)"],
        source=source if any(picked.values()) else SOURCE_NONE,
    )


def _values_from_tuple(parts: tuple[str, str, str, str]) -> AreebValues:
    category, product_type, product_style, department = parts
    return AreebValues(
        category=category,
        product_type=product_type,
        product_style=product_style,
        department=department,
        source=SOURCE_CL_STANDARD if any(parts) else SOURCE_NONE,
    )
