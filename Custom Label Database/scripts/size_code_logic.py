"""
Custom Label → size code → Size References mm lookup.

Pipeline (Custom Label always):
  Override contain (flag only) → Size Reference longest-base + brackets
  → bare base → bare fallback → letter-pair → common codes
  → resolve mm → Override / F8 pocket hardcodes may replace dims.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd

FLAG_TOKENS = frozenset({"YES", "Y", "NO", "N"})
GENDER_LETTERS = frozenset({"M", "W", "K"})
# Tokens that are noise for common-code fallback
NOISE_TOKENS = frozenset(
    {
        "YES",
        "Y",
        "NO",
        "N",
        "BLK",
        "WHI",
        "WHE",
        "NAV",
        "NVY",
        "RED",
        "PNK",
        "LPNK",
        "HPNK",
        "GRN",
        "BLU",
        "LBL",
        "LBLU",
        "ORG",
        "ORN",
        "YEL",
        "PRP",
        "GRY",
        "GRY",
        "BGE",
        "CRM",
        "NTRL",
        "MULTI",
        "PACK",
        "PAK",
        "PER",
        "F",
        "B",
        "P",
        "S",
        "M",
        "L",
        "XL",
        "XS",
        "2XL",
        "3XL",
        "4XL",
        "5XL",
        "XXL",
        "YS",
        "YXS",
        "YM",
        "YL",
        "YXL",
        "Y2XL",
        "LG",
        "ALG",
    }
)
COMMON_ALLOW = frozenset({"A3", "A4", "A5", "A6", "BS", "BG", "QD", "SH", "W", "C"})
COMMON_PREFIXES = ("BG", "QD", "SH", "TPC", "BZ", "C8", "W1", "SF")

POCKET_ADULT = (80, 100)
POCKET_KIDS = (65, 80)

RE_PAREN = re.compile(r"\(([^)]*)\)")
RE_CRLF = re.compile(r"[\r\n]+")


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return RE_CRLF.sub(" ", s).strip()


def to_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def normalize_sku(sku: str) -> tuple[str, list[str]]:
    """Uppercase SKU; split on '-'; drop empties; strip trailing '.' on tokens."""
    s = clean(sku).upper()
    tokens = [t.rstrip(".") for t in s.split("-") if t and t.rstrip(".")]
    return s, tokens


def strip_trailing_flags(tokens: list[str]) -> list[str]:
    out = list(tokens)
    while out and out[-1] in FLAG_TOKENS:
        out.pop()
    return out


def parse_sku_value(sku_val: str) -> tuple[str, list[str]]:
    """'K-SS (YXS)' / 'M-T (-L)' / 'K-SS (YS) (YXS)' → (base, brackets)."""
    raw = clean(sku_val).upper()
    if not raw:
        return "", []
    brackets = [b.strip().upper() for b in RE_PAREN.findall(raw) if b.strip()]
    base = RE_PAREN.sub("", raw)
    base = re.sub(r"\s+", " ", base).strip()
    base = re.sub(r"\s*-\s*", "-", base)
    return base, brackets


def is_leading_dash_bracket(bracket: str) -> bool:
    return bracket.startswith("-")


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
    sr = _read_size_ref_table(config_path)
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
            # Store under each bracket key; also under full multi-bracket signature
            for br in brackets:
                mb.brackets[br].append(row)
        else:
            mb.bare_rows.append(row)

    bases = sorted(by_base.keys(), key=len, reverse=True)
    return SizeRefIndex(by_base=by_base, bases_longest_first=bases, by_exact_sku=dict(by_exact))


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


def base_token_span(tokens: list[str], base: str) -> tuple[int, int] | None:
    """Find leftmost span of tokens that join with '-' to equal base."""
    parts = [p for p in base.split("-") if p]
    if not parts:
        return None
    n = len(parts)
    for i in range(len(tokens) - n + 1):
        if tokens[i : i + n] == parts:
            return i, i + n
    # Also allow base as single token (e.g. W115, A4, 10AILG)
    for i, t in enumerate(tokens):
        if t == base:
            return i, i + 1
    return None


def gender_skip_indices(tokens: list[str], base: str) -> set[int]:
    """Indices of gender letter inside apparel bases like M-T / W-H / K-SS."""
    span = base_token_span(tokens, base)
    if not span:
        return set()
    start, end = span
    skip: set[int] = set()
    parts = base.split("-")
    if parts and parts[0] in GENDER_LETTERS:
        # first token of span is gender
        skip.add(start)
    return skip


def match_normal_bracket(bracket: str, tokens: list[str]) -> bool:
    """Exact hyphen token match (YS must not match inside Y2XL)."""
    br = bracket.upper()
    return br in tokens


def match_leading_dash_bracket(
    bracket: str, tokens: list[str], base: str
) -> bool:
    """
    Leading-dash apparel (-S, -2XL, -1-2Y): consecutive tokens anywhere;
    prefer rightmost span; strip trailing YES/Y/NO/N; skip gender token
    that is part of M-T / W-H / K-SS.
    """
    if not bracket.startswith("-"):
        return False
    core = bracket[1:].upper()
    target = [p for p in core.split("-") if p]
    if not target:
        return False
    cleaned = strip_trailing_flags(tokens)
    skip = gender_skip_indices(cleaned, base)
    # When matching gender-like brackets (-M/-W/-K), skip gender indices
    gender_br = core in GENDER_LETTERS and len(target) == 1
    n = len(target)
    best = None
    for i in range(len(cleaned) - n + 1):
        if cleaned[i : i + n] != target:
            continue
        if gender_br and any(j in skip for j in range(i, i + n)):
            continue
        # Prefer rightmost
        best = i
    return best is not None


def try_bracket_match(
    sku_u: str, tokens: list[str], index: SizeRefIndex
) -> tuple[str, int] | None:
    """
    Walk bases longest-first; base must be substring of SKU;
    then try that base's brackets longest-first.
    Returns (BASE|BRACKET, base_len) or None.
    """
    tokens_work = strip_trailing_flags(tokens)

    for base in index.bases_longest_first:
        if base not in sku_u:
            continue
        mb = index.by_base[base]
        if not mb.brackets:
            continue
        br_keys = sorted(mb.brackets.keys(), key=len, reverse=True)
        for br in br_keys:
            if is_leading_dash_bracket(br):
                ok = match_leading_dash_bracket(br, tokens_work, base)
            else:
                ok = match_normal_bracket(br, tokens_work)
            if ok:
                return f"{base}|{br}", len(base)
    return None


def try_bare_base(
    sku_u: str, index: SizeRefIndex, *, skip_bases_with_brackets: bool
) -> tuple[str, int] | None:
    """
    Longest Merge_clean substring in the SKU that has a bare SR row.
    Returns (base, base_len) or None.

    Phase B (skip_bases_with_brackets=True): skip bases that also have bracket
    variants so short apparel templates don't steal from paper sizes like A4.
    Phase C (False): allow those bases when a dedicated bare row exists
    (e.g. bare K-H next to K-H (YS) (YXS)).
    """
    for base in index.bases_longest_first:
        if base not in sku_u:
            continue
        mb = index.by_base[base]
        if not mb.has_bare:
            continue
        if skip_bases_with_brackets and mb.brackets:
            continue
        return base, len(base)
    return None


def try_letter_pair(tokens: list[str]) -> str | None:
    """Adjacent single-letter alpha tokens → X-Y. Prefer ending in -T; else last pair."""
    cleaned = strip_trailing_flags(tokens)
    pairs: list[str] = []
    for i in range(len(cleaned) - 1):
        a, b = cleaned[i], cleaned[i + 1]
        if len(a) == 1 and a.isalpha() and len(b) == 1 and b.isalpha():
            pairs.append(f"{a}-{b}")
    if not pairs:
        return None
    for p in reversed(pairs):
        if p.endswith("-T"):
            return p
    return pairs[-1]


def try_common_code(tokens: list[str]) -> str | None:
    cleaned = strip_trailing_flags(tokens)
    for t in cleaned:
        if len(t) < 2 or len(t) > 4:
            continue
        if t in COMMON_ALLOW:
            return t
        if t in NOISE_TOKENS:
            continue
        if not any(c.isalpha() for c in t):
            continue
        if t in COMMON_ALLOW or any(t.startswith(p) for p in COMMON_PREFIXES):
            return t
        return t
    return None


def extract_size_code(
    custom_label: str,
    index: SizeRefIndex,
    overrides: list[OverrideRule],
) -> tuple[str | None, OverrideRule | None]:
    """
    Returns (size_code, override_rule_or_None).
    Override contain only flags dims-later; extraction continues.

    Conflict: if both bare and bracket hit → longer base wins
    (e.g. 10AILG-M-T beats M-T|-L). Equal length → prefer bracket.
    """
    sku_u, tokens = normalize_sku(custom_label)
    if not sku_u:
        return None, None

    ov = find_override(sku_u, overrides)

    bracket_hit = try_bracket_match(sku_u, tokens, index)
    bare_hit = try_bare_base(sku_u, index, skip_bases_with_brackets=True)
    if not bare_hit:
        bare_hit = try_bare_base(sku_u, index, skip_bases_with_brackets=False)

    code = None
    if bracket_hit and bare_hit:
        b_code, b_len = bracket_hit
        bare_code, bare_len = bare_hit
        if bare_len > b_len:
            code = bare_code
        else:
            code = b_code  # longer bracket base, or equal → prefer composite
    elif bracket_hit:
        code = bracket_hit[0]
    elif bare_hit:
        code = bare_hit[0]

    if not code:
        code = try_letter_pair(tokens)
    if not code:
        code = try_common_code(tokens)
    return code, ov


def split_size_code(code: str) -> tuple[str, str | None]:
    if "|" in code:
        base, br = code.split("|", 1)
        return base, br
    return code, None


def _rows_for_exact(index: SizeRefIndex, sku_value: str) -> list[SrRow]:
    return list(index.by_exact_sku.get(sku_value.upper(), []))


def resolve_sr_rows(code: str, index: SizeRefIndex) -> list[SrRow]:
    """
    Prefer exact (base, bracket) pair → bare base → contains / bracket-only fallbacks.
    """
    base, br = split_size_code(code)
    mb = index.by_base.get(base)

    if br is not None:
        # Try exact reconstructed SKU values
        candidates = [
            f"{base} ({br})",
            f"{base}({br})",
        ]
        # If br already has leading dash stored as -S
        if not br.startswith("-"):
            candidates.append(f"{base} (-{br})")
        for cand in candidates:
            rows = _rows_for_exact(index, cand)
            if rows:
                return rows
        if mb:
            # Direct bracket map (keys as stored, with or without dash)
            for key in (br, br.lstrip("-"), f"-{br.lstrip('-')}"):
                if key in mb.brackets:
                    return list(mb.brackets[key])

    # Bare base
    if mb and mb.bare_rows:
        return list(mb.bare_rows)

    # Exact bare sku value
    rows = _rows_for_exact(index, base)
    if rows:
        return rows

    # Bracket-only fallback: any rows under this base
    if mb and mb.brackets:
        # pick first bracket's rows (stable: longest bracket key)
        key = sorted(mb.brackets.keys(), key=len, reverse=True)[0]
        return list(mb.brackets[key])

    return []


def pocket_dims_for_sku(sku_u: str) -> tuple[int, int]:
    if re.search(r"(^|-)K(-|$)", sku_u):
        return POCKET_KIDS
    return POCKET_ADULT


def apply_dim_overrides(
    rows_wh: list[tuple[int | None, int | None]],
    sku_u: str,
    override: OverrideRule | None,
    size_code: str | None,
) -> list[tuple[int | None, int | None]]:
    """
    After SR lookup: Override Print Size may replace dims.
    Width & Height present → use them.
    Blank → hardcoded pocket: -K- → 65×80, else 80×100.
    F8 size codes also force pocket dims.
    """
    force_pocket = False
    forced: tuple[int, int] | None = None

    if override is not None:
        if override.w is not None and override.h is not None:
            forced = (override.w, override.h)
        else:
            force_pocket = True

    if size_code and size_code.upper().startswith("F8"):
        force_pocket = True

    if "F8-" in sku_u or sku_u.startswith("F8"):
        # F8 in label often means pocket print
        if forced is None:
            force_pocket = True

    if force_pocket and forced is None:
        forced = pocket_dims_for_sku(sku_u)

    if forced is None:
        return rows_wh

    return [forced for _ in rows_wh] if rows_wh else [forced]


def n_designs_from_rows(rows: list[SrRow], pos_count: int) -> int:
    nd = 1
    for r in rows:
        if r.n_designs:
            nd = max(nd, r.n_designs)
            break
    return max(nd, pos_count, 1)


def slot_dimensions(
    rows: list[SrRow], n_slots: int
) -> list[tuple[int | None, int | None]]:
    """Map SR rows (by Number of Designs / suffix order) onto slots 1..n."""
    # Preserve order; unique by suffix when multi-row same dims patterns
    ordered = list(rows)
    out: list[tuple[int | None, int | None]] = []
    for i in range(n_slots):
        if i < len(ordered):
            out.append((ordered[i].w, ordered[i].h))
        elif ordered:
            out.append((ordered[-1].w, ordered[-1].h))
        else:
            out.append((None, None))
    return out


def resolve_print_dims(
    custom_label: str,
    print_positions: str,
    index: SizeRefIndex,
    overrides: list[OverrideRule],
    max_slots: int = 4,
) -> dict:
    """
    Full resolve for one Custom Label row.
    Returns dict with size_code, override, n_slots, position_names, widths, heights, source.
    """
    sku_u, _ = normalize_sku(custom_label)
    code, ov = extract_size_code(custom_label, index, overrides)
    pos_names = [p.strip() for p in clean(print_positions).split(",") if p.strip()]
    if not pos_names:
        pos_names = []

    rows: list[SrRow] = []
    if code:
        rows = resolve_sr_rows(code, index)

    n = n_designs_from_rows(rows, len(pos_names)) if rows else max(len(pos_names), 1)
    n = min(n, max_slots)
    if not pos_names:
        # still allow WH fill from n_designs alone
        pass

    whs = slot_dimensions(rows, n) if rows else [(None, None)] * n
    whs = apply_dim_overrides(whs, sku_u, ov, code)

    # If override/pocket produced dims but rows empty
    if (not rows) and ov is not None:
        forced = apply_dim_overrides([(None, None)], sku_u, ov, code)[0]
        n = min(max(len(pos_names), 1), max_slots)
        whs = [forced] * n

    return {
        "size_code": code,
        "override": ov.contain if ov else None,
        "n_slots": n,
        "position_names": pos_names[:max_slots],
        "whs": whs[:max_slots],
        "matched_rows": len(rows),
    }
