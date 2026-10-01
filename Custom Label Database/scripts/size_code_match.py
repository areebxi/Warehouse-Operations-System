"""Bracket / bare-base / letter-pair / common-code matching for size codes."""
from __future__ import annotations

from size_code_index import SizeRefIndex
from size_code_util import (
    COMMON_ALLOW,
    COMMON_PREFIXES,
    GENDER_LETTERS,
    NOISE_TOKENS,
    is_leading_dash_bracket,
    strip_trailing_flags,
)


def base_token_span(tokens: list[str], base: str) -> tuple[int, int] | None:
    """Find leftmost span of tokens that join with '-' to equal base."""
    parts = [p for p in base.split("-") if p]
    if not parts:
        return None
    n = len(parts)
    for i in range(len(tokens) - n + 1):
        if tokens[i : i + n] == parts:
            return i, i + n
    for i, t in enumerate(tokens):
        if t == base:
            return i, i + 1
    return None


def gender_skip_indices(tokens: list[str], base: str) -> set[int]:
    """Indices of gender letter inside apparel bases like M-T / W-H / K-SS."""
    span = base_token_span(tokens, base)
    if not span:
        return set()
    start, _end = span
    skip: set[int] = set()
    parts = base.split("-")
    if parts and parts[0] in GENDER_LETTERS:
        skip.add(start)
    return skip


def match_normal_bracket(bracket: str, tokens: list[str]) -> bool:
    """Exact hyphen token match (YS must not match inside Y2XL)."""
    return bracket.upper() in tokens


def match_leading_dash_bracket(bracket: str, tokens: list[str], base: str) -> bool:
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
    gender_br = core in GENDER_LETTERS and len(target) == 1
    n = len(target)
    best = None
    for i in range(len(cleaned) - n + 1):
        if cleaned[i : i + n] != target:
            continue
        if gender_br and any(j in skip for j in range(i, i + n)):
            continue
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
