"""Shift tokens, leftover/plain B codes, six-field filename core."""
from __future__ import annotations

from fixed_batches import fixed_batch_codes, reserved_batch_nums
from grouping_models import IN_HOUSE, ON_DEMAND, WAREHOUSE_STOCK, slotify

FILENAME_SUPPLY = {
    slotify(WAREHOUSE_STOCK): "WAREHOUSE STOCK",
    slotify(ON_DEMAND): "SUPPLY ON DEMAND",
    slotify(IN_HOUSE): "IN HOUSE MANUFACTURE",
}

FIXED_BATCH_CODES: frozenset[str] = fixed_batch_codes()

NAMED_CODES = FIXED_BATCH_CODES  # back-compat alias

RESERVED_BATCH_NUMS: frozenset[int] = reserved_batch_nums()

def next_leftover_batch_codes(count: int) -> list[str]:
    """B1, B2, … skipping fixed-batch numbers (B80, B100, B1000, …)."""
    out: list[str] = []
    n = 1
    while len(out) < count:
        if n not in RESERVED_BATCH_NUMS:
            out.append(f"B{n}")
        n += 1
    return out

def next_plain_batch_codes(count: int) -> list[str]:
    """Plain batches 1, 2, …: B2000, B2100, B2200, B2500, B2600, B2700, … (skip reserved)."""
    out: list[str] = []
    n = 2000
    while len(out) < count:
        if n not in RESERVED_BATCH_NUMS:
            out.append(f"B{n}")
        n += 100
    return out

def six_field_core(left: list[str], shift_slot: str) -> str:
    """Filename fields 1–5: shift-finish-prime-supply-R/P. Priority is appended later.

    Supervisor 2026-09-22/23: shift first after optional fixed-batch prefix, e.g.
    B100-S1-PRINTED-2-WAREHOUSE STOCK-R-5.
    """
    finish = "PRINTED" if (left[0] if left else "") == "printed" else "PLAIN"
    prime = "1" if (len(left) > 3 and left[3] == "prime") else "2"
    supply_slot = left[9] if len(left) > 9 else "x"
    supply = FILENAME_SUPPLY.get(supply_slot, supply_slot.replace("_", " ").upper())
    cust = "P" if (len(left) > 5 and left[5] == "customised") else "R"
    shift = shift_file_token(shift_slot)
    return f"{shift}-{finish}-{prime}-{supply}-{cust}"

def shift_number(shift_slot: str) -> int:
    digits = "".join(c for c in shift_slot if c.isdigit())
    return int(digits) if digits else 1

def shift_file_token(shift_slot: str) -> str:
    return f"S{shift_number(shift_slot)}"

def shift_pair(n: int) -> tuple[str, str]:
    if n == 1:
        slot = "1st"
    elif n == 2:
        slot = "2nd"
    elif n == 3:
        slot = "3rd"
    else:
        slot = f"{n}th"
    return slot, f"{slot} Shift"
