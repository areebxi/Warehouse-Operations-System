"""
Custom Label → size code → Size References mm lookup.

Pipeline (Custom Label always):
  Override contain (flag only) → Size Reference longest-base + brackets
  → bare base → bare fallback → letter-pair → common codes
  → resolve mm → Override / F8 pocket hardcodes may replace dims.

Façade: callers keep `from size_code_logic import …`.
"""
from __future__ import annotations

from size_code_index import (
    MergeBase,
    OverrideRule,
    SizeRefIndex,
    SrRow,
    find_override,
    load_overrides,
    load_size_ref_index,
)
from size_code_extract import extract_size_code, split_size_code
from size_code_match import (
    base_token_span,
    gender_skip_indices,
    match_leading_dash_bracket,
    match_normal_bracket,
    try_bare_base,
    try_bracket_match,
    try_common_code,
    try_letter_pair,
)
from size_code_resolve import (
    apply_dim_overrides,
    n_designs_from_rows,
    pocket_dims_for_sku,
    resolve_print_dims,
    resolve_sr_rows,
    slot_dimensions,
)
from size_code_util import (
    COMMON_ALLOW,
    COMMON_PREFIXES,
    FLAG_TOKENS,
    GENDER_LETTERS,
    NOISE_TOKENS,
    POCKET_ADULT,
    POCKET_KIDS,
    RE_CRLF,
    RE_PAREN,
    clean,
    is_leading_dash_bracket,
    normalize_sku,
    parse_sku_value,
    strip_trailing_flags,
    to_num,
)

__all__ = [
    "COMMON_ALLOW",
    "COMMON_PREFIXES",
    "FLAG_TOKENS",
    "GENDER_LETTERS",
    "MergeBase",
    "NOISE_TOKENS",
    "OverrideRule",
    "POCKET_ADULT",
    "POCKET_KIDS",
    "RE_CRLF",
    "RE_PAREN",
    "SizeRefIndex",
    "SrRow",
    "apply_dim_overrides",
    "base_token_span",
    "clean",
    "extract_size_code",
    "find_override",
    "gender_skip_indices",
    "is_leading_dash_bracket",
    "load_overrides",
    "load_size_ref_index",
    "match_leading_dash_bracket",
    "match_normal_bracket",
    "n_designs_from_rows",
    "normalize_sku",
    "parse_sku_value",
    "pocket_dims_for_sku",
    "resolve_print_dims",
    "resolve_sr_rows",
    "slot_dimensions",
    "split_size_code",
    "strip_trailing_flags",
    "to_num",
    "try_bare_base",
    "try_bracket_match",
    "try_common_code",
    "try_letter_pair",
]


def _selfcheck() -> None:
    # ponytail: pure unit asserts — no live Size References / CL reads
    assert is_leading_dash_bracket("-L")
    assert not is_leading_dash_bracket("YXS")
    assert parse_sku_value("K-SS (YXS)") == ("K-SS", ["YXS"])
    assert parse_sku_value("M-T (-L)") == ("M-T", ["-L"])
    assert split_size_code("M-T|-L") == ("M-T", "-L")
    assert split_size_code("A4") == ("A4", None)
    assert normalize_sku("x-Yes")[1] == ["X", "YES"]
    assert strip_trailing_flags(["M", "T", "YES"]) == ["M", "T"]
    assert try_letter_pair(["M", "T", "BLK", "L"]) == "M-T"
    assert pocket_dims_for_sku("M260-K-T-BLK-YXS") == POCKET_KIDS
    assert pocket_dims_for_sku("M260-M-T-BLK-L") == POCKET_ADULT


if __name__ == "__main__":
    _selfcheck()
    print("size_code_logic selfcheck OK")
