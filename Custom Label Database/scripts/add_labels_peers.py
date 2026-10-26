"""Scan CL CSV and collect slim peer rows for named labels."""
from __future__ import annotations

import csv
from pathlib import Path

from fill_from_seeds import clean

from add_labels_peer_keys import _peer_keys_for_label

_PEER_KEEP = (
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
    "Customise",
    "Supplier Product Code",
    "Supplier SKU",
    "Brand",
    "Category",
    "Department",
    "Sub-Category",
    "Sub-Department",
    "Width 1 (mm)",
    "Height 1 (mm)",
    "Position 1 Name",
)


def _slim_peer(r: dict[str, str], fieldnames: list[str]) -> dict[str, str]:
    keep = [c for c in _PEER_KEEP if c in fieldnames]
    return {c: clean(r.get(c)) for c in keep}


def _peer_filters(
    labels: list[str],
) -> tuple[set[str], list[str], list[str]]:
    exact: set[str] = set()
    prefixes: list[str] = []
    suffixes: list[str] = []
    for lab in labels:
        for item in _peer_keys_for_label(lab):
            if item.startswith("__prefix__:"):
                prefixes.append(item.split(":", 1)[1])
            elif item.startswith("__suffix__:"):
                suffixes.append(item.split(":", 1)[1].casefold())
            else:
                exact.add(item)
    return exact, prefixes, suffixes


def _peer_hit(
    key: str, exact: set[str], prefixes: list[str], suffixes: list[str]
) -> bool:
    return (
        key in exact
        or any(key.startswith(p) for p in prefixes)
        or any(key.endswith(s) for s in suffixes)
    )


def _take_peer(
    peers: dict[str, dict[str, str]], key: str, slim: dict[str, str]
) -> None:
    prev = peers.get(key)
    if prev is None:
        peers[key] = slim
    elif slim.get("Gender Apparel", "").startswith("FOTL") and not prev.get(
        "Gender Apparel", ""
    ).startswith("FOTL"):
        peers[key] = slim


def _scan_existing(path: Path) -> tuple[list[str], set[str]]:
    """Fast pass: fieldnames + existing Custom Label set only."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        fieldnames = next(reader)
        try:
            lab_i = fieldnames.index("Custom Label")
        except ValueError as exc:
            raise ValueError("CL CSV missing Custom Label column") from exc
        existing: set[str] = set()
        for row in reader:
            if lab_i >= len(row):
                continue
            lab = row[lab_i].strip()
            if lab:
                existing.add(lab.casefold())
    return fieldnames, existing


def _collect_peers_for_labels(
    path: Path, fieldnames: list[str], labels: list[str]
) -> dict[str, dict[str, str]]:
    exact, prefixes, suffixes = _peer_filters(labels)
    if not exact and not prefixes and not suffixes:
        return {}
    peers: dict[str, dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lab = clean(r.get("Custom Label"))
            if not lab:
                continue
            key = lab.casefold()
            if not _peer_hit(key, exact, prefixes, suffixes):
                continue
            _take_peer(peers, key, _slim_peer(r, fieldnames))
    return peers


def _scan_existing_and_peers(
    path: Path, labels: list[str]
) -> tuple[list[str], set[str], dict[str, dict[str, str]]]:
    """One DictReader pass: existing labels + peer rows (same picks as two-pass)."""
    exact, prefixes, suffixes = _peer_filters(labels)
    want_peers = bool(exact or prefixes or suffixes)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "Custom Label" not in fieldnames:
            raise ValueError("CL CSV missing Custom Label column")
        existing: set[str] = set()
        peers: dict[str, dict[str, str]] = {}
        for r in reader:
            lab = clean(r.get("Custom Label"))
            if not lab:
                continue
            key = lab.casefold()
            existing.add(key)
            if want_peers and _peer_hit(key, exact, prefixes, suffixes):
                _take_peer(peers, key, _slim_peer(r, fieldnames))
    return fieldnames, existing, peers
