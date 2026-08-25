"""Tests for Step 4 Logo IDs to Positions -> Position assignment."""

import pandas as pd

from scripts.pipeline_split_position.transform_position_codes import (
    apply_logo_id_positions,
    build_position_lookup,
    insert_position_code,
)


def _logo_map() -> dict[str, str]:
    return {
        "159731lg": "Front Top Center",
        "128357lg": "Front Top Center, Back Top Center",
    }


def test_logo_id_match_sets_position():
    df = pd.DataFrame(
        [{"Logo ID": "159731LG", "Position": "", "Gender Apparel": "Mens-T-Shirt"}]
    )
    apply_logo_id_positions(df, _logo_map())
    assert df.at[0, "Position"] == "Front Top Center"


def test_logo_id_match_overrides_existing_cl_position():
    df = pd.DataFrame(
        [
            {
                "Logo ID": "159731LG",
                "Position": "Back Top Center",
                "Gender Apparel": "Mens-T-Shirt",
            }
        ]
    )
    apply_logo_id_positions(df, _logo_map())
    assert df.at[0, "Position"] == "Front Top Center"


def test_unknown_logo_id_leaves_position_unchanged():
    df = pd.DataFrame(
        [{"Logo ID": "999999LG", "Position": "Back Top Center", "Gender Apparel": "Mens-T-Shirt"}]
    )
    apply_logo_id_positions(df, _logo_map())
    assert df.at[0, "Position"] == "Back Top Center"


def test_blank_logo_id_leaves_position_unchanged():
    df = pd.DataFrame(
        [{"Logo ID": "", "Position": "", "Gender Apparel": "Mens-T-Shirt"}]
    )
    apply_logo_id_positions(df, _logo_map())
    assert df.at[0, "Position"] == ""


def test_missing_logo_id_column_is_no_op():
    df = pd.DataFrame([{"Position": "Back Top Center", "Gender Apparel": "Mens-T-Shirt"}])
    apply_logo_id_positions(df, _logo_map())
    assert df.at[0, "Position"] == "Back Top Center"


def test_case_insensitive_logo_id_lookup():
    df = pd.DataFrame(
        [{"Logo ID": "159731lg", "Position": "", "Gender Apparel": "Mens-T-Shirt"}]
    )
    apply_logo_id_positions(df, _logo_map())
    assert df.at[0, "Position"] == "Front Top Center"


def test_logo_id_position_flows_to_position_code():
    df = pd.DataFrame(
        [{"Logo ID": "159731LG", "Position": "", "Gender Apparel": "Mens-T-Shirt"}]
    )
    apply_logo_id_positions(df, _logo_map())

    pq_df = pd.DataFrame(
        {
            "P": ["Default Position", "Front Top Center"],
            "Q": ["X", "X2"],
        }
    )
    default_code, position_to_code = build_position_lookup(pq_df)
    insert_position_code(df, default_code, position_to_code)

    assert df.at[0, "Position"] == "Front Top Center"
    assert df.at[0, "Position Code"] == "X2"
