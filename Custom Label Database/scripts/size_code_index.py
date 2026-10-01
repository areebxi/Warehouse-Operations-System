"""Size References index + Override Print Size loaders."""
from __future__ import annotations

import pickle
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from size_code_util import clean, parse_sku_value, to_num


@dataclass
class SrRow:
    sku_value: str
    base: str
    brackets: list[str]
    w: int | None
    h: int | None
    n_designs: int
    suffix: str


@dataclass
class MergeBase:
    base: str
    brackets: dict[str, list[SrRow]] = field(default_factory=lambda: defaultdict(list))
    bare_rows: list[SrRow] = field(default_factory=list)

    @property
    def has_bare(self) -> bool:
        return bool(self.bare_rows)

    @property
    def only_brackets(self) -> bool:
        """True when every SR row for this base carries brackets (no bare row)."""
        return not self.has_bare and bool(self.brackets)


@dataclass
class SizeRefIndex:
    by_base: dict[str, MergeBase]
    bases_longest_first: list[str]
    # exact SKU Value → rows (for multi-design identical keys)
    by_exact_sku: dict[str, list[SrRow]]


@dataclass
class OverrideRule:
    contain: str
    w: int | None
    h: int | None


def _read_size_ref_table(config_path: Path) -> pd.DataFrame:
    path = Path(config_path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str)
    return pd.read_excel(path, sheet_name="Size References")


def load_size_ref_index(config_path: Path) -> SizeRefIndex:
    """Load Size References index; cache beside the CSV when mtime matches."""
    path = Path(config_path)
    cache = path.with_name(path.stem + ".index_cache.pkl")
    try:
        if cache.is_file() and cache.stat().st_mtime >= path.stat().st_mtime:
            with open(cache, "rb") as f:
                cached = pickle.load(f)
            if isinstance(cached, SizeRefIndex):
                return cached
    except Exception:
        pass

    sr = _read_size_ref_table(path)
    by_base: dict[str, MergeBase] = {}
    by_exact: dict[str, list[SrRow]] = defaultdict(list)

    for _, rec in sr.iterrows():
        sku_val = clean(rec.get("SKU Value"))
        if not sku_val:
            continue
        base, brackets = parse_sku_value(sku_val)
        if not base:
            continue
        w = to_num(rec.get("Size Width"))
        h = to_num(rec.get("Size Height"))
        nd = to_num(rec.get("Number of Designs")) or 1
        row = SrRow(
            sku_value=sku_val.upper(),
            base=base,
            brackets=brackets,
            w=int(w) if w is not None else None,
            h=int(h) if h is not None else None,
            n_designs=int(nd),
            suffix=clean(rec.get("Suffix")).upper(),
        )
        by_exact[row.sku_value].append(row)
        mb = by_base.get(base)
        if mb is None:
            mb = MergeBase(base=base)
            by_base[base] = mb
        if brackets:
            for br in brackets:
                mb.brackets[br].append(row)
        else:
            mb.bare_rows.append(row)

    bases = sorted(by_base.keys(), key=len, reverse=True)
    index = SizeRefIndex(by_base=by_base, bases_longest_first=bases, by_exact_sku=dict(by_exact))
    try:
        with open(cache, "wb") as f:
            pickle.dump(index, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception:
        pass
    return index


def load_overrides(config_path: Path) -> list[OverrideRule]:
    path = Path(config_path)
    if path.suffix.lower() == ".csv":
        return []
    try:
        ov = pd.read_excel(path, sheet_name="Override Print Size")
    except (ValueError, FileNotFoundError):
        return []
    rules: list[OverrideRule] = []
    for _, rec in ov.iterrows():
        contain = clean(rec.get("SKU Contain")).upper()
        if not contain:
            continue
        w = to_num(rec.get("Width"))
        h = to_num(rec.get("Height"))
        rules.append(
            OverrideRule(
                contain=contain,
                w=int(w) if w is not None else None,
                h=int(h) if h is not None else None,
            )
        )
    rules.sort(key=lambda r: len(r.contain), reverse=True)
    return rules


def find_override(sku_u: str, rules: list[OverrideRule]) -> OverrideRule | None:
    hit = None
    for r in rules:
        if r.contain and r.contain in sku_u:
            if hit is None or len(r.contain) > len(hit.contain):
                hit = r
    return hit
