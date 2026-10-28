"""Self-check for Areeb position fix helpers."""
from __future__ import annotations

import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from fix_areeb_pos_lib import copy_print_from_live, mm_ok, sole_center


def test_sole_and_copy() -> None:
    row = {
        "Print Positions": "Front Left Pocket, Back Center",
        "Print Position Code": "F8",
        "Position 1 Name": "Front Left Pocket",
        "Width 1 (mm)": "80",
        "Height 1 (mm)": "100",
        "Design Image Suffix 1": "P",
        "Position 2 Name": "Back Center",
        "Width 2 (mm)": "237",
        "Height 2 (mm)": "336",
        "Design Image Suffix 2": "B",
        "Print Size 1": "A4",
        "Print Size 2": "",
        "Position 3 Name": "",
        "Width 3 (mm)": "",
        "Height 3 (mm)": "",
        "Design Image Suffix 3": "",
        "Position 4 Name": "",
        "Width 4 (mm)": "",
        "Height 4 (mm)": "",
        "Design Image Suffix 4": "",
        "Print Size 3": "",
        "Print Size 4": "",
    }
    sole_center(row, back=False, width="237", height="336")
    assert row["Print Positions"] == "Front Center"
    assert row["Position 1 Name"] == "Front Center"
    assert row["Print Position Code"] == "F4"
    assert row["Width 1 (mm)"] == "237"
    assert row["Position 2 Name"] == ""
    assert row["Design Image Suffix 1"] == ""
    assert not mm_ok("80", "100")
    assert mm_ok("237", "336")

    live = {
        "Print_Positions": "Front Center",
        "Print_Position_Code": "F4",
        "Position_1_Name": "Front Center",
        "Width_1_mm": "237",
        "Height_1_mm": "336",
        "Position_2_Name": "",
        "Width_2_mm": "",
        "Height_2_mm": "",
        "Print_Size_1": "A4",
        "Print_Size_2": "",
        "Position_3_Name": "",
        "Position_4_Name": "",
        "Width_3_mm": "",
        "Height_3_mm": "",
        "Width_4_mm": "",
        "Height_4_mm": "",
        "Print_Size_3": "",
        "Print_Size_4": "",
    }
    dst = {
        "Print Positions": "",
        "Print Position Code": "",
        "Position 1 Name": "",
        "Width 1 (mm)": "",
        "Height 1 (mm)": "",
        "Print Size 1": "",
        "Position 2 Name": "x",
        "Width 2 (mm)": "1",
        "Height 2 (mm)": "1",
        "Print Size 2": "",
        "Position 3 Name": "",
        "Position 4 Name": "",
        "Width 3 (mm)": "",
        "Height 3 (mm)": "",
        "Width 4 (mm)": "",
        "Height 4 (mm)": "",
        "Print Size 3": "",
        "Print Size 4": "",
        "Design Image Suffix 1": "",
        "Design Image Suffix 2": "",
        "Design Image Suffix 3": "",
        "Design Image Suffix 4": "",
    }
    copy_print_from_live(dst, live)
    assert dst["Print Positions"] == "Front Center"
    assert dst["Width 1 (mm)"] == "237"


if __name__ == "__main__":
    test_sole_and_copy()
    print("ok")
