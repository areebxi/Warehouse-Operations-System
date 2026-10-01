"""BTC Stock ID CSV I/O and SPC+colour+size lookup fill."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from fill_btc_stock_id_maps import cl_size_to_pe, colours_to_try, norm


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
            return fieldnames, rows, encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode file: {path}")


def lookup_uid(
    lookup: dict[tuple[str, str, str], str],
    spc: str,
    colour_name: str,
    pe_size: str,
) -> tuple[str | None, bool]:
    """Return (uid, used_alias)."""
    ns = norm(spc)
    for i, colour_key in enumerate(colours_to_try(colour_name)):
        uid = lookup.get((ns, colour_key, pe_size))
        if uid:
            return uid, i > 0
    return None, False


def build_lookup(
    product_rows: list[dict[str, str]],
) -> tuple[dict[tuple[str, str, str], str], list[tuple[tuple[str, str, str], str, str]]]:
    lookup: dict[tuple[str, str, str], str] = {}
    duplicates: list[tuple[tuple[str, str, str], str, str]] = []

    for row in product_rows:
        spc = (row.get("SPC") or "").strip()
        colour = norm(row.get("Colour Name") or "")
        size = (row.get("Size") or "").strip()
        uid = (row.get("UID") or "").strip()
        if not spc or not uid:
            continue

        key = (norm(spc), colour, size)
        if key in lookup and lookup[key] != uid:
            duplicates.append((key, lookup[key], uid))
        lookup[key] = uid

    return lookup, duplicates


def fill_stock_ids(
    custom_rows: list[dict[str, str]],
    lookup: dict[tuple[str, str, str], str],
) -> tuple[int, int, int, int, int, Counter[str]]:
    filled = 0
    filled_via_alias = 0
    filled_via_kids_size = 0
    unchanged_no_match = 0
    unchanged_no_spc = 0
    skip_reasons: Counter[str] = Counter()

    for row in custom_rows:
        spc = (row.get("BTC Product Code") or "").strip()
        if not spc:
            unchanged_no_spc += 1
            skip_reasons["empty_btc_product_code"] += 1
            continue

        pe_size, used_kids_size = cl_size_to_pe(row.get("Size") or "", spc)
        uid, used_alias = lookup_uid(lookup, spc, row.get("Colour Name") or "", pe_size)

        if not uid:
            unchanged_no_match += 1
            skip_reasons["no_match_in_btc_product_data"] += 1
            continue

        row["BTC Stock ID"] = uid
        filled += 1
        if used_alias:
            filled_via_alias += 1
        if used_kids_size:
            filled_via_kids_size += 1

    return (
        filled,
        filled_via_alias,
        filled_via_kids_size,
        unchanged_no_match,
        unchanged_no_spc,
        skip_reasons,
    )


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    encoding: str,
) -> None:
    with open(path, "w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
