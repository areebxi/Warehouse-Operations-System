"""Self-check: mock PP normalize + sole pocket/back from mocks map."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS.parent.parent))
sys.path.insert(0, str(SCRIPTS))

from add_labels_mock_pos import (  # noqa: E402
    apply_mock_print_positions,
    first_position_name,
    mock_print_positions_map,
)
from fix_areeb_mock_pos_lib import (  # noqa: E402
    apply_from_mocks,
    norm_pp,
    prefer_live_or_mocks,
)


def main() -> None:
    m = mock_print_positions_map()
    assert m.get("M261") == "Back Center", m.get("M261")
    assert m.get("M264") == "Front Left Pocket", m.get("M264")
    assert m.get("M260") == "Front Center", m.get("M260")
    assert first_position_name("Front Left Pocket, Back Center (M42)") == "Front Left Pocket"

    row: dict[str, str] = {
        "Custom Label": "M261-P6-17132",
        "Print Positions": "Front Center",
        "Print Position Code": "F4",
        "Position 1 Name": "Front Center",
        "Width 1 (mm)": "250",
        "Height 1 (mm)": "353",
    }
    apply_mock_print_positions("M261-P6-17132", row)
    assert row["Print Positions"] == "Back Center"
    assert row["Position 1 Name"] == "Back Center"

    pocket = dict(row)
    pocket["Print Positions"] = "Front Center"
    apply_from_mocks(pocket, "Front Left Pocket")
    assert pocket["Print Positions"] == "Front Left Pocket"
    assert pocket["Print Position Code"] == "F8"
    assert pocket["Width 1 (mm)"] == "80"

    # Order matters for repair (M42 Back,Pocket vs Pocket,Back).
    assert norm_pp("Back Center, Front Left Pocket") != norm_pp(
        "Front Left Pocket, Back Center"
    )
    assert norm_pp("Front Center") == "front center"
    assert norm_pp("Back Center (M261)") == "back center"

    live = {
        "Print_Positions": "Back Center",
        "Print_Position_Code": "B4",
        "Position_1_Name": "Back Center",
        "Width_1_mm": "250",
        "Height_1_mm": "353",
    }
    dst = {
        "Print Positions": "Front Center",
        "Print Position Code": "F4",
        "Position 1 Name": "Front Center",
        "Width 1 (mm)": "250",
        "Height 1 (mm)": "353",
    }
    assert prefer_live_or_mocks(dst, live, "Back Center", "Print_Positions") == "live"
    assert dst["Print Positions"] == "Back Center"
    assert dst["Print Position Code"] == "B4"
    print("ok")


if __name__ == "__main__":
    main()
