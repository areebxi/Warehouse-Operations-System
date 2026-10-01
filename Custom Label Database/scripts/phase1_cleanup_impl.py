from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

def standardize_age_size(val: str) -> tuple[str, str | None]:
    """Return (new_value, rule_name_or_None)."""
    if not val:
        return val, None

    original = val

    # Already canonical "N-N Years"
    m = re.match(r"^(\d+)-(\d+) Years$", val)
    if m:
        return val, None

    # "N-N years" / mixed case / extra spaces
    m = re.match(r"^(\d+)\s*[-–]\s*(\d+)\s+[Yy]ears\s*$", val)
    if m:
        canon = f"{m.group(1)}-{m.group(2)} Years"
        if canon != original:
            return canon, "years_casing_or_spacing"
        return val, None

    # N-NY / N-Ny
    m = RE_NY.match(val)
    if m:
        return f"{m.group(1)}-{m.group(2)} Years", "short_Y"

    # Stuck "5Years"
    m = RE_STUCK_NO_SPACE.match(val)
    if m:
        return f"{m.group(1)} Years", "stuck_Years"

    # Single "5 years" / "5 Years " etc. (not age-band)
    m = re.match(r"^(\d+)\s*[Yy]ears\s*$", val)
    if m:
        canon = f"{m.group(1)} Years"
        if canon != original:
            return canon, "single_years_casing"
        return val, None

    # Bare N-N for known kids age bands only
    m = RE_BARE.match(val)
    if m:
        bare = f"{m.group(1)}-{m.group(2)}"
        if bare in AGE_BANDS:
            return f"{bare} Years", "bare_age_band"

    return original, None
def clean_text(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val)
    s = RE_X000D.sub("", s)
    s = RE_CRLF.sub(" ", s)
    s = s.strip()
    return s
