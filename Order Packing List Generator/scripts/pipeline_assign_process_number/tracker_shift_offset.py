"""
Design ID Process Tracker shift offset — isolated Step 5 modifier for Separate by Logo ID.

When Separate by Logo ID is enabled and a row gets a Process Number from workbook sheet
"Design ID Process Tracker", adds a shift-based offset to numeric tracker values only:
  1st -> +100, 2nd -> +200, 3rd -> +300, 4th -> +400, 5th -> +500

Does not affect normal 6-part assignment, fixed process numbers, or non-tracker logo paths.
Set USE_SHIFT_OFFSET = False to disable without changing other pipeline code.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional

from .normalize import _normalize, _normalize_process_start

USE_SHIFT_OFFSET = True

SHIFT_OFFSET_BY_LABEL: dict[str, int] = {
    "1st": 100,
    "2nd": 200,
    "3rd": 300,
    "4th": 400,
    "5th": 500,
}


def _log(msg: str, log: Optional[Callable[[str], None]]) -> None:
    if log:
        log(msg)


def normalize_shift_label(shift_input: str) -> str | None:
    """Map user shift input (e.g. '1st', '2nd Shift') to '1st'..'5th', or None."""
    s = _normalize(shift_input).lower().replace(" shift", "").strip()
    if not s:
        return None
    if s in SHIFT_OFFSET_BY_LABEL:
        return s
    for key in SHIFT_OFFSET_BY_LABEL:
        if s.startswith(key):
            return key
    return None


def shift_offset_for_input(shift_input: str) -> int | None:
    """Return +100..+500 for 1st..5th shift, or None if shift is unrecognized."""
    label = normalize_shift_label(shift_input)
    if label is None:
        return None
    return SHIFT_OFFSET_BY_LABEL[label]


def _is_pure_numeric_process_number(process_number: str) -> bool:
    s = _normalize_process_start(process_number)
    if not s:
        return False
    try:
        return float(s).is_integer()
    except (TypeError, ValueError):
        return False


def apply_shift_offset_to_tracker_number(process_number: str, shift_input: str) -> str:
    """
    Add shift offset to a Design ID Process Tracker Process Number when numeric.
    Non-numeric values (e.g. 100A) are returned unchanged.
    Unrecognized shift returns the normalized tracker number unchanged.
    """
    base = _normalize_process_start(process_number)
    if not base or not _is_pure_numeric_process_number(base):
        return base or _normalize(process_number)

    offset = shift_offset_for_input(shift_input)
    if offset is None:
        return base

    return str(int(float(base)) + offset)


def apply_shift_offset_to_tracker_map(
    tracker_map: dict[str, str],
    shift_input: str,
    log: Optional[Callable[[str], None]] = None,
) -> dict[str, str]:
    """
    Apply shift offsets to all numeric values in a Design ID Process Tracker map.
    Used only when Separate by Logo ID is enabled.
    """
    if not USE_SHIFT_OFFSET or not tracker_map:
        return tracker_map

    offset = shift_offset_for_input(shift_input)
    label = normalize_shift_label(shift_input)
    if offset is None:
        _log(
            "Design ID Process Tracker shift offset: unrecognized shift "
            f"{shift_input!r}; numeric tracker Process Numbers unchanged.",
            log,
        )
        return tracker_map

    out: dict[str, str] = {}
    adjusted = 0
    for design_id, process_number in tracker_map.items():
        new_val = apply_shift_offset_to_tracker_number(process_number, shift_input)
        out[design_id] = new_val
        if new_val != _normalize_process_start(process_number):
            adjusted += 1

    _log(
        f"Design ID Process Tracker shift offset: {label} shift (+{offset}) applied to "
        f"{adjusted}/{len(tracker_map)} numeric Process Number mapping(s).",
        log,
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Standalone CLI: apply tracker shift offset to one Process Number."""
    parser = argparse.ArgumentParser(
        description=(
            "Apply Design ID Process Tracker shift offset to a numeric Process Number "
            "(Separate by Logo ID only; 1st=+100 .. 5th=+500)."
        )
    )
    parser.add_argument("process_number", help="Tracker Process Number (e.g. 10000)")
    parser.add_argument("shift", help="Shift label (1st, 2nd, 3rd, 4th, 5th)")
    args = parser.parse_args(argv)

    if not USE_SHIFT_OFFSET:
        print("USE_SHIFT_OFFSET is False; returning normalized input unchanged.", file=sys.stderr)
        print(_normalize_process_start(args.process_number))
        return 0

    result = apply_shift_offset_to_tracker_number(args.process_number, args.shift)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
