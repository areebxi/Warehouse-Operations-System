"""Printing Type for grouping (Custom Label only).

Supervisor lock 2026-09-09:
 DTF = default (garments, bags, iron-on, stickers, ...)
 Sublimation = mugs / drinkware
 UV = safety helmet (wins over mock and DTF; locked 2026-10-20)

Lookup: helmet (Product Type Safety Helmet, or Gender Apparel contains
helmet) -> UV. Else Custom Label leading M## -> Mocks Database.csv
Printing-Type when that cell is DTF or Sublimation. Else mug (Category Mugs
or Gender Apparel starts with Mug) -> Sublimation. Else DTF.

Do not fill Design Type. Plain / Packs have no Printing Type split (flag x).
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from typing import Any, Mapping

from shared import cl_columns as clc
from shared.areeb_taxonomy import cell
from shared.paths import mocks_database_csv_path

COL = clc.PRINTING_TYPE

DTF = "DTF"
SUBLIMATION = "Sublimation"
UV = "UV"

_MOCK_ID_RE = re.compile(r"^(M\d+)\b", re.I)
_KNOWN = {DTF.casefold(): DTF, SUBLIMATION.casefold(): SUBLIMATION, UV.casefold(): UV}


def mock_id_from_label(label: object) -> str:
    match = _MOCK_ID_RE.match(cell(label))
    return match.group(1) if match else ""


def is_safety_helmet(*, gender_apparel: object = "", product_type: object = "") -> bool:
    blob = f"{cell(product_type)} {cell(gender_apparel)}".casefold()
    return "helmet" in blob


def is_mug(*, category_areeb: object = "", gender_apparel: object = "") -> bool:
    if cell(category_areeb).casefold() == "mugs":
        return True
    return cell(gender_apparel).casefold().startswith("mug")


def normalize_printing_type(raw: object) -> str:
    return _KNOWN.get(cell(raw).casefold(), "")


@lru_cache(maxsize=1)
def load_mock_printing_types() -> dict[str, str]:
    path = mocks_database_csv_path()
    out: dict[str, str] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            mid = cell(row.get("Pasting Mocks ID"))
            value = normalize_printing_type(row.get("Printing-Type"))
            if mid and value:
                out[mid.casefold()] = value
    return out


def classify_printing_type(
    *,
    custom_label: object = "",
    gender_apparel: object = "",
    category_areeb: object = "",
    product_type: object = "",
    mock_types: Mapping[str, str] | None = None,
) -> str:
    if is_safety_helmet(gender_apparel=gender_apparel, product_type=product_type):
        return UV
    types = mock_types if mock_types is not None else load_mock_printing_types()
    mid = mock_id_from_label(custom_label)
    if mid:
        hit = normalize_printing_type(types.get(mid.casefold(), ""))
        if hit:
            return hit
    if is_mug(category_areeb=category_areeb, gender_apparel=gender_apparel):
        return SUBLIMATION
    return DTF


def classify_cl_row(
    row: dict[str, Any],
    *,
    mock_types: Mapping[str, str] | None = None,
) -> str:
    return classify_printing_type(
        custom_label=row.get(clc.CUSTOM_LABEL),
        gender_apparel=row.get(clc.GENDER_APPAREL) or row.get("Gender Apparel"),
        category_areeb=row.get(clc.CATEGORY_AREEB),
        product_type=row.get(clc.PRODUCT_TYPE_AREEB),
        mock_types=mock_types,
    )
