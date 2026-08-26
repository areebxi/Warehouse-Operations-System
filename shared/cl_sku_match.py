"""
Universal Custom Label match keys.

Against Custom Label (entire cell, casefold), try in order:
  1. whole Item SKU
  2. after first dash
  3. till last dash (everything before the last dash)

No short-token skip. First entire-cell hit wins.
"""

from __future__ import annotations

from typing import Hashable, Iterable, Mapping, MutableMapping, Optional, Sequence, TypeVar

T = TypeVar("T")


def _as_sku_str(item_sku: object) -> str:
    if item_sku is None:
        return ""
    s = str(item_sku).strip()
    if not s or s.lower() in ("nan", "none"):
        return ""
    return s


def key_after_first_dash(item_sku: object) -> str:
    s = _as_sku_str(item_sku)
    if not s:
        return ""
    dash = s.find("-")
    if dash == -1:
        return ""
    return s[dash + 1 :].strip()


def key_till_last_dash(item_sku: object) -> str:
    s = _as_sku_str(item_sku)
    if not s:
        return ""
    dash = s.rfind("-")
    if dash == -1:
        return ""
    return s[:dash].strip()


def match_keys(item_sku: object) -> list[str]:
    """Ordered unique candidate keys (original casing preserved for display)."""
    whole = _as_sku_str(item_sku)
    if not whole:
        return []
    keys: list[str] = []
    seen: set[str] = set()
    for candidate in (whole, key_after_first_dash(whole), key_till_last_dash(whole)):
        if not candidate:
            continue
        norm = candidate.casefold()
        if norm in seen:
            continue
        seen.add(norm)
        keys.append(candidate)
    return keys


def normalize_label(value: object) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return ""
    return s.casefold()


def build_label_index(
    labels: Iterable[object],
    *,
    ids: Optional[Iterable[Hashable]] = None,
) -> dict[str, Hashable]:
    """
    Map casefolded Custom Label -> first associated id (or 0-based index).

    Entire-cell match only; first row wins on duplicate labels.
    """
    index: dict[str, Hashable] = {}
    if ids is None:
        for i, label in enumerate(labels):
            key = normalize_label(label)
            if not key or key in index:
                continue
            index[key] = i
        return index

    for label, row_id in zip(labels, ids):
        key = normalize_label(label)
        if not key or key in index:
            continue
        index[key] = row_id
    return index


def resolve_label(
    item_sku: object,
    index: Mapping[str, T],
) -> Optional[str]:
    """
    Return the casefolded Custom Label key that matched, or None.

    Tries match_keys in order against the index (entire-cell).
    """
    for candidate in match_keys(item_sku):
        key = candidate.casefold()
        if key in index:
            return key
    return None


def resolve_from_map(
    item_sku: object,
    mapping: Mapping[str, T],
) -> Optional[T]:
    """Resolve Item SKU against a casefolded-key mapping; return mapped value."""
    key = resolve_label(item_sku, mapping)
    if key is None:
        return None
    return mapping[key]


def warehouse_root_from(path: object) -> "Path":
    """Delegate to shared.paths (data/runtime/config layout)."""
    from shared.paths import warehouse_root_from as _root

    return _root(path)


def default_cl_csv_path(from_path: object) -> "Path":
    from shared.paths import cl_csv_path

    return cl_csv_path(from_path)


def shared_inbox_dtf_des_root(from_path: object) -> "Path":
    from shared.paths import shared_inbox_dtf_des_root as _inbox

    return _inbox(from_path)
