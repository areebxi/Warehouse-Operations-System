"""Extract a Size References size code from a Custom Label."""
from __future__ import annotations

from size_code_index import OverrideRule, SizeRefIndex, find_override
from size_code_match import try_bare_base, try_bracket_match, try_common_code, try_letter_pair
from size_code_util import normalize_sku


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
            code = b_code
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
