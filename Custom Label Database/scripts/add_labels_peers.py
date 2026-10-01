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
            if (
                key not in exact
                and not any(key.startswith(p) for p in prefixes)
                and not any(key.endswith(s) for s in suffixes)
            ):
                continue
            prev = peers.get(key)
            slim = _slim_peer(r, fieldnames)
            if prev is None:
                peers[key] = slim
            elif slim.get("Gender Apparel", "").startswith("FOTL") and not prev.get(
                "Gender Apparel", ""
            ).startswith("FOTL"):
                peers[key] = slim
    return peers
