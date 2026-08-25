"""Tests for Step 4 Multiple Positions -> Logo/Design Image expansion."""

import pandas as pd

from scripts.pipeline_split_position.transform_logo_design import (
    _multiple_positions_lookup,
    apply_x_xz_logo_design_image,
)


def _sample_multiple_positions_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "abbreviation": ["X002", "xz1"],
            "position-1": ["f", "x93"],
            "position-2": ["b", "x6"],
            "position-3": ["", ""],
            "position-4": ["", ""],
            "position-5": ["", ""],
        }
    )


def test_multiple_positions_lookup_x002():
    found = _multiple_positions_lookup(_sample_multiple_positions_df(), "X002")
    assert found == ["f", "b"]


def test_normal_logo_expanded_from_multiple_positions_sheet():
    df = pd.DataFrame(
        [
            {
                "Item SKU": "103671LG-B/B-M-T-CHR-L",
                "Position Code": "X002",
                "Logo ID": "103671LG",
                "Logo/Design Image": "103671LG",
                "Customise": "",
                "Order Number": "05-14640-80848",
            }
        ]
    )
    apply_x_xz_logo_design_image(df, _sample_multiple_positions_df())
    assert df.at[0, "Logo/Design Image"] == "103671LG-f, 103671LG-b"


def test_no_sheet_match_leaves_normal_row_unchanged():
    df = pd.DataFrame(
        [
            {
                "Item SKU": "8513LG-M-T-BLK-L",
                "Position Code": "X1",
                "Logo ID": "8513LG",
                "Logo/Design Image": "8513LG",
                "Customise": "",
                "Order Number": "order-1",
            }
        ]
    )
    apply_x_xz_logo_design_image(df, _sample_multiple_positions_df())
    assert df.at[0, "Logo/Design Image"] == "8513LG"


def test_customise_yes_skips_multiple_positions_even_when_code_on_sheet():
    """Personalized rows keep a single Logo/Design Image even when Position Code is on the sheet."""
    df = pd.DataFrame(
        [
            {
                "Item SKU": "192633LG-M118-P2-138056",
                "Position Code": "X002",
                "Logo ID": "192633LG",
                "Logo/Design Image": "07-14642-83277",
                "Customise": "Yes",
                "Order Number": "07-14642-83277",
            }
        ]
    )
    apply_x_xz_logo_design_image(df, _sample_multiple_positions_df())
    assert df.at[0, "Logo/Design Image"] == "07-14642-83277"


def test_no_sheet_match_leaves_custom_order_unchanged_despite_m_in_sku():
    """SKUs like -M118 must not trigger LogoID-PositionCode suffix (removed -m/-xz logic)."""
    df = pd.DataFrame(
        [
            {
                "Item SKU": "192633LG-M118-P2-138056",
                "Position Code": "X011",
                "Logo ID": "192633LG",
                "Logo/Design Image": "07-14642-83277",
                "Customise": "Yes",
                "Order Number": "07-14642-83277",
            }
        ]
    )
    apply_x_xz_logo_design_image(df, _sample_multiple_positions_df())
    assert df.at[0, "Logo/Design Image"] == "07-14642-83277"
