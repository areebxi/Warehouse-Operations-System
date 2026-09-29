"""Process-number / DTF Des stem helpers for convert + print.

Packing now names files `DTF Des-PB100-S1.xlsx` and writes Process Num like
`B100-S1-1`. Legacy inputs stay `DTF Des-P100.xlsx` / pure numeric `100`.
"""
from __future__ import annotations

import re

# Packing batch+shift token inside a Des stem (DTF Des-PB100-S1 → B100-S1).
_BATCH_SHIFT_STEM_RE = re.compile(r"(B\d+-S\d+)", re.IGNORECASE)
# In-file process: B100-S1-1 (batch+shift + process increment).
_BATCH_PROC_RE = re.compile(r"^(B\d+-S\d+)-(\d+)$", re.IGNORECASE)
_DIGITS_RE = re.compile(r"(\d+)")


def dtf_id_from_stem(stem: str) -> str | None:
    """Job/log key from a DTF Des filename stem.

    Prefer `B100-S1` from `DTF Des-PB100-S1` (not the trailing shift `1`).
    Else last numeric token (legacy `DTF Des-P100` → `100`).
    """
    s = (stem or "").strip()
    if not s:
        return None
    m = _BATCH_SHIFT_STEM_RE.search(s)
    if m:
        return m.group(1).upper()
    matches = _DIGITS_RE.findall(s)
    return matches[-1] if matches else None


def process_number_sort_key(pn: object) -> tuple:
    """Numeric when pure digits; batch+shift by trailing process N; else string."""
    s = str(pn or "").strip()
    if s.isdigit():
        return (0, int(s), "")
    m = _BATCH_PROC_RE.match(s)
    if m:
        return (1, m.group(1).upper(), int(m.group(2)))
    return (2, s.casefold(), 0)


def is_consecutive_process(prev: object, curr: object) -> bool:
    """True for 100→101 or B100-S1-1→B100-S1-2 (same batch+shift)."""
    a = str(prev or "").strip()
    b = str(curr or "").strip()
    if a.isdigit() and b.isdigit():
        return int(b) == int(a) + 1
    ma = _BATCH_PROC_RE.match(a)
    mb = _BATCH_PROC_RE.match(b)
    if ma and mb and ma.group(1).casefold() == mb.group(1).casefold():
        return int(mb.group(2)) == int(ma.group(2)) + 1
    return False


if __name__ == "__main__":
    # ponytail: fails if Des stem keys or B#-S# consecutive drift.
    assert dtf_id_from_stem("DTF Des-PB100-S1") == "B100-S1"
    assert dtf_id_from_stem("DTF Des-PB1-S1") == "B1-S1"
    assert dtf_id_from_stem("DTF Des-P100") == "100"
    assert is_consecutive_process("B100-S1-1", "B100-S1-2")
    assert not is_consecutive_process("B100-S1-1", "B8000-S1-2")
    assert process_number_sort_key("B100-S1-2") < process_number_sort_key("B100-S1-10")
    print("process_numbers ok")
