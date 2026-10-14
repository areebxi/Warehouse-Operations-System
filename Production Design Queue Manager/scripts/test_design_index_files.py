"""Letter-index PNGs (-B / -P) are separate designs."""

import os

from PIL import Image

from src.core.design_processing_single import process_single_designs


def test_b_and_p_index_pngs_are_both_queued(tmp_path) -> None:
    Image.new("RGB", (8, 8), "red").save(tmp_path / "5968ALG-B.png")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "5968ALG-P.png")
    results = process_single_designs(
        "5968ALG-M280-IronOn-A3",
        str(tmp_path),
        300 / 25.4,
        canvas_width_mm=570,
        cl_csv_path=tmp_path / "missing.csv",
    )
    names = [os.path.basename(r["path"]) for r in results]
    assert names == ["5968ALG-B.png", "5968ALG-P.png"]
    pocket = results[1]
    assert abs(pocket["width_mm"] - 80.0) < 0.2
    assert abs(pocket["height_mm"] - 100.0) < 0.2
