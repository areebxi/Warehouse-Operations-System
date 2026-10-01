"""Six-field process names on bins."""
from __future__ import annotations

from datetime import date

from grouping_models import ProcessBin
from grouping_shift import (
    next_leftover_batch_codes,
    next_plain_batch_codes,
    shift_number,
    six_field_core,
)

def _bin_is_today(b: ProcessBin, run: date) -> bool:
    """Any due/overdue line makes the pile today (mixed today+future counts as today)."""
    return any(o.ship_by is not None and o.ship_by <= run for o in b.orders)

def _bin_is_prime(b: ProcessBin) -> bool:
    if not b.orders:
        return False
    left = b.orders[0].left
    return len(left) > 3 and left[3] == "prime"

def _apply_six_field_names(bins: list[ProcessBin], run: date) -> None:
    """On-disk name only. Grouping keys are unchanged.

    Field 6 is packing-list order in that shift: today first, then prime first,
    then as files are made (fixed batches, then leftover). More ranking later.

    Leftover piles get B1, B2, … (skipping reserved fixed-batch numbers).
    Supervisor 2026-09-23.
    """
    bins.sort(key=lambda b: _bin_sort_key(b, run))
    leftover = [b for b in bins if b.orders and not b.floor_code]
    plain = [b for b in leftover if b.orders[0].finish == "plain"]
    other = [b for b in leftover if b.orders[0].finish != "plain"]
    for b, code in zip(plain, next_plain_batch_codes(len(plain))):
        b.floor_code = code
    for b, code in zip(other, next_leftover_batch_codes(len(other))):
        b.floor_code = code
    next_pri: dict[str, int] = {}
    for b in bins:
        if not b.orders:
            continue
        core = six_field_core(b.orders[0].left, b.shift_slot)
        stem = f"{b.floor_code}-{core}" if b.floor_code else core
        n = next_pri.get(b.shift_slot, 0) + 1
        next_pri[b.shift_slot] = n
        b.process_name = f"{stem}-{n}"

def _batch_sort_num(code: str) -> int:
    """B100 → 100 for priority sort. Digits only; unknown → 0."""
    digits = "".join(c for c in code if c.isdigit())
    return int(digits) if digits else 0

def _bin_sort_key(b: ProcessBin, run: date) -> tuple:
    shift_i = shift_number(b.shift_slot) - 1
    date_i = 0 if _bin_is_today(b, run) else 1
    prime_i = 0 if _bin_is_prime(b) else 1
    if b.floor_code:
        return (shift_i, date_i, prime_i, 0, _batch_sort_num(b.floor_code), "")
    return (shift_i, date_i, prime_i, 1, 0, b.process_name)
