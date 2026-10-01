"""Sanitize / IO helpers for fill_cl_database."""
from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, Optional

TOKEN_RE = re.compile(r"\{([^{}]+)\}")
_SANITIZE_PRODUCT_VALUE = re.compile(r"[^a-zA-Z0-9-]+")
_PARENS_SEGMENT = re.compile(r"\([^()]*\)")
_BRACKETS_SEGMENT = re.compile(r"\[[^\[\]]*\]")
_POSSESSIVE_APOSTROPHE_S = re.compile(r"'s\b", re.IGNORECASE)


def _normalize_apostrophes(value: str) -> str:
    value = _POSSESSIVE_APOSTROPHE_S.sub("s", value)
    return value.replace("'", "")


def _strip_bracketed_segments(value: str) -> str:
    s = value
    prev = None
    while prev != s:
        prev = s
        s = _BRACKETS_SEGMENT.sub("", s)
        s = _PARENS_SEGMENT.sub("", s)
    return s


def sanitize_product_field(value: str) -> str:
    if not value:
        return ""
    value = _strip_bracketed_segments(value)
    value = _normalize_apostrophes(value)
    return _SANITIZE_PRODUCT_VALUE.sub(" ", value).strip()


def _read_csv_text(path: str, encoding: Optional[str]) -> tuple[str, str]:
    with open(path, "rb") as f:
        raw = f.read()
    if encoding is not None:
        return raw.decode(encoding), encoding
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1"), "latin-1"


def load_btc_product_data(path: str, encoding: Optional[str]) -> tuple[List[str], List[Dict[str, str]]]:
    text, _used_enc = _read_csv_text(path, encoding)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("BTC Product Data has no header/fieldnames.")
    rows: List[Dict[str, str]] = []
    for row in reader:
        rows.append({k: sanitize_product_field("" if v is None else v) for k, v in row.items()})
    return reader.fieldnames, rows


def cell_has_placeholders(cell: str) -> bool:
    return bool(TOKEN_RE.search(cell))


def replace_placeholders_in_cell(
    cell: str, product_row: Dict[str, str], source_name: str, row_num: int
) -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key not in product_row:
            raise KeyError(
                f"Missing token column {key!r} referenced from CL {source_name} row {row_num}. "
                f"Available BTC Product Data columns do not include it."
            )
        return product_row[key]

    filled = TOKEN_RE.sub(repl, cell)
    return re.sub(r"\s+", " ", filled).strip()
