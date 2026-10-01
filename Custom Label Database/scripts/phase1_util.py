"""Text/size helpers for phase1_cleanup."""
from __future__ import annotations

import re

import pandas as pd

AGE_BANDS = [
    "1-2",
    "2-3",
    "3-4",
    "4-5",
    "5-6",
    "7-8",
    "9-11",
    "12-13",
    "12-14",
    "14-15",
]

RE_X000D = re.compile(r"_x000D_", re.IGNORECASE)
RE_CRLF = re.compile(r"[\r\n]+")
RE_NY = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s*Y$", re.IGNORECASE)
RE_STUCK_NO_SPACE = re.compile(r"^(\d+)Years$", re.IGNORECASE)
RE_BARE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")


def clean_text(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val)
    s = RE_X000D.sub("", s)
    s = RE_CRLF.sub(" ", s)
    return s.strip()


def standardize_age_size(val: str) -> tuple[str, str | None]:
    """Return (new_value, rule_name_or_None)."""
    if not val:
        return val, None
    original = val

    m = re.match(r"^(\d+)-(\d+) Years$", val)
    if m:
        return val, None

    m = re.match(r"^(\d+)\s*[-–]\s*(\d+)\s+[Yy]ears\s*$", val)
    if m:
        canon = f"{m.group(1)}-{m.group(2)} Years"
        if canon != original:
            return canon, "years_casing_or_spacing"
        return val, None

    m = RE_NY.match(val)
    if m:
        return f"{m.group(1)}-{m.group(2)} Years", "short_Y"

    m = RE_STUCK_NO_SPACE.match(val)
    if m:
        return f"{m.group(1)} Years", "stuck_Years"

    m = re.match(r"^(\d+)\s*[Yy]ears\s*$", val)
    if m:
        canon = f"{m.group(1)} Years"
        if canon != original:
            return canon, "single_years_casing"
        return val, None

    m = RE_BARE.match(val)
    if m:
        bare = f"{m.group(1)}-{m.group(2)}"
        if bare in AGE_BANDS:
            return f"{bare} Years", "bare_age_band"

    return original, None
