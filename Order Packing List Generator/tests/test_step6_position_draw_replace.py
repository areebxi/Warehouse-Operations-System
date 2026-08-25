"""Tests for Step 6 Draw replace before slash merge."""

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)
from scripts.pipeline_split_by_process_item.common import _position_after_merge

SAMPLE_DRAW_MAP = {
    "X004": "Front",
    "X1": "Front, Back",
    "x004": "Front",
}


def _row(**kwargs) -> pd.Series:
    defaults = {
        "Position": "Front Top Center",
        "Position Code": "X004",
        "Logo/Design Image": "103671LG",
    }
    defaults.update(kwargs)
    return pd.Series(defaults)


def test_lookup_draw_case_insensitive():
    assert lookup_draw_for_position_code(SAMPLE_DRAW_MAP, "x004") == "Front"
    assert lookup_draw_for_position_code(SAMPLE_DRAW_MAP, "X004") == "Front"
    assert lookup_draw_for_position_code(SAMPLE_DRAW_MAP, "missing") == ""


def test_single_position_draw_replace():
    result = _position_after_merge(
        _row(Position="Front Top Center"),
        position_code_to_draw=SAMPLE_DRAW_MAP,
    )
    assert result == "Front"


def test_multi_draw_single_logo_slash_merge():
    result = _position_after_merge(
        _row(
            Position="Front Top Center, Back Top Center",
            **{"Position Code": "X1"},
        ),
        position_code_to_draw=SAMPLE_DRAW_MAP,
    )
    assert result == "Front / Back"


def test_multi_draw_multi_logo_no_slash():
    result = _position_after_merge(
        _row(
            Position="Front Top Center, Back Top Center",
            **{"Position Code": "X1", "Logo/Design Image": "103671LG-f, 103671LG-b"},
        ),
        position_code_to_draw=SAMPLE_DRAW_MAP,
    )
    assert result == "Front, Back"


def test_default_position_code_blank():
    result = _position_after_merge(
        _row(**{"Position Code": "X"}),
        position_code_to_draw=SAMPLE_DRAW_MAP,
        default_position_code="X",
    )
    assert result == ""


def test_no_draw_fallback_to_cl_text():
    result = _position_after_merge(
        _row(**{"Position Code": "UNKNOWN"}),
        position_code_to_draw=SAMPLE_DRAW_MAP,
    )
    assert result == "Front Top Center"


def test_no_mapping_still_slash_merges_cl_text():
    result = _position_after_merge(
        _row(Position="Front Top Center, Back Top Center"),
        position_code_to_draw=None,
    )
    assert result == "Front Top Center / Back Top Center"
