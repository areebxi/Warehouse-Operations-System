"""Fill blank Gender Apparel from Plain Database, then Packs.

Printed rows already filled from Custom Label are left alone.
Plain key = till last dash, else whole SKU. Packs key = whole SKU.
"""

from __future__ import annotations

import csv
import threading
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from shared.cl_sku_match import key_till_last_dash

_LOCK = threading.Lock()
_CACHE: tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]] | None = None


def _cell(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() in ("nan", "none") else text


def _blank(value: object) -> bool:
    return _cell(value) == ""


def gender_text(row: dict[str, str]) -> str:
    """Garment line for the packing-list Gender Apparel box."""
    dept = _cell(row.get("Department (Areeb)"))
    ptype = _cell(row.get("Product Type (Areeb)"))
    if dept and len(dept) <= 24 and ptype and dept.casefold() not in ptype.casefold():
        return f"{dept} {ptype}".strip()
    return ptype or dept or _cell(row.get("Description")) or _cell(row.get("Pack Name"))


def _read_rows(path: Path) -> list[dict[str, str]]:
    last: Exception | None = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open(encoding=enc, newline="") as handle:
                return [{k: _cell(v) for k, v in row.items() if k} for row in csv.DictReader(handle)]
        except UnicodeDecodeError as exc:
            last = exc
    raise last or RuntimeError(f"Could not decode {path}")


def index_by(rows: list[dict[str, str]], key_col: str) -> dict[str, dict[str, str]]:
    idx: dict[str, dict[str, str]] = {}
    for row in rows:
        key = _cell(row.get(key_col)).casefold()
        if key and key not in idx:
            idx[key] = row
    return idx


def load_plain_index(path: Path | None = None) -> dict[str, dict[str, str]]:
    from shared import paths as wh

    src = path or wh.plain_database_path()
    if not src.is_file():
        return {}
    return index_by(_read_rows(src), "SKU")


def load_packs_index(path: Path | None = None) -> dict[str, dict[str, str]]:
    from shared import paths as wh

    src = path or wh.packs_database_path()
    if not src.is_file():
        return {}
    return index_by(_read_rows(src), "Channel Child SKU")


def cached_indexes() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    global _CACHE
    with _LOCK:
        if _CACHE is None:
            _CACHE = (load_plain_index(), load_packs_index())
        return _CACHE


def _plain_hit(sku: object, plain: dict[str, dict[str, str]]) -> dict[str, str] | None:
    till = _cell(key_till_last_dash(sku)).casefold()
    if till and till in plain:
        return plain[till]
    whole = _cell(sku).casefold()
    if whole and whole in plain:
        return plain[whole]
    return None


def _apply_row(df: pd.DataFrame, idx, row: dict[str, str], *, size_col: str, colour_col: str) -> None:
    gender = gender_text(row)
    if not gender:
        return
    df.at[idx, "Gender Apparel"] = gender
    size = _cell(row.get(size_col))
    colour = _cell(row.get(colour_col))
    image = _cell(row.get("Product_Image_URL"))
    if size:
        df.at[idx, "Size"] = size
    if colour:
        df.at[idx, "Colour"] = colour
    if image:
        df.at[idx, "Picture Name"] = image
        df.at[idx, "Apparel Image"] = image


def apply_plain_packs(
    df: pd.DataFrame,
    plain: dict[str, dict[str, str]] | None = None,
    packs: dict[str, dict[str, str]] | None = None,
    log: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """Fill rows whose Gender Apparel is still blank. CL hits are kept."""
    if plain is None or packs is None:
        loaded_plain, loaded_packs = cached_indexes()
        plain = loaded_plain if plain is None else plain
        packs = loaded_packs if packs is None else packs
    plain_hits = pack_hits = 0
    for idx, row in df.iterrows():
        if not _blank(row.get("Gender Apparel")):
            continue
        sku = row.get("Item SKU", "")
        hit = _plain_hit(sku, plain)
        if hit is not None:
            before = _cell(df.at[idx, "Gender Apparel"])
            _apply_row(df, idx, hit, size_col="Size", colour_col="Colour")
            if _cell(df.at[idx, "Gender Apparel"]) and not before:
                plain_hits += 1
            continue
        pack = packs.get(_cell(sku).casefold())
        if pack is None:
            continue
        before = _cell(df.at[idx, "Gender Apparel"])
        _apply_row(df, idx, pack, size_col="Pack Size", colour_col="")
        if _cell(df.at[idx, "Gender Apparel"]) and not before:
            pack_hits += 1
    if log:
        log(f"  Step 2 plain/packs: plain={plain_hits}, packs={pack_hits}.")
    return df
