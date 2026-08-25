"""Tests for Design ID Process Tracker shift offset (Separate by Logo ID only)."""

from scripts.pipeline_assign_process_number.tracker_shift_offset import (
    apply_shift_offset_to_tracker_map,
    apply_shift_offset_to_tracker_number,
    normalize_shift_label,
    shift_offset_for_input,
)


def test_shift_offset_by_label():
    assert shift_offset_for_input("1st") == 100
    assert shift_offset_for_input("2nd Shift") == 200
    assert shift_offset_for_input("5th") == 500
    assert shift_offset_for_input("unknown") is None


def test_normalize_shift_label():
    assert normalize_shift_label("1st shift") == "1st"
    assert normalize_shift_label("3RD") == "3rd"


def test_apply_shift_offset_to_tracker_number():
    assert apply_shift_offset_to_tracker_number("10000", "1st") == "10100"
    assert apply_shift_offset_to_tracker_number("10000", "2nd") == "10200"
    assert apply_shift_offset_to_tracker_number("10000.0", "1st") == "10100"
    assert apply_shift_offset_to_tracker_number("100A", "1st") == "100A"
    assert apply_shift_offset_to_tracker_number("10000", "bad") == "10000"


def test_apply_shift_offset_to_tracker_map():
    mapped = apply_shift_offset_to_tracker_map(
        {"187276lg": "10000", "other": "100A"},
        "1st",
    )
    assert mapped["187276lg"] == "10100"
    assert mapped["other"] == "100A"
