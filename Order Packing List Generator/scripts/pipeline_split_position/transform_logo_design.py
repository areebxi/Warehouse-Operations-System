from typing import Callable, Optional



import pandas as pd



from .normalize import _normalize_label





def _multiple_positions_lookup(

    multiple_positions_df: pd.DataFrame | None,

    position_code: str,

) -> list[str]:

    """

    Look up position code in Multiple Positions by abbreviation.

    Returns list of position values (e.g. ['f', 'b']) in order; empty if not found.

    """

    if multiple_positions_df is None or multiple_positions_df.empty:

        return []

    pc = _normalize_label(position_code).lower()

    if not pc:

        return []

    cols = list(multiple_positions_df.columns)

    abbrev_col = cols[0]

    pos_cols = cols[1:]

    for _, row in multiple_positions_df.iterrows():

        ab = _normalize_label(row.get(abbrev_col)).lower()

        if ab == pc:

            return [

                _normalize_label(row.get(c))

                for c in pos_cols

                if _normalize_label(row.get(c))

            ]

    return []





def _customise_is_yes(val) -> bool:

    """Match fill_prime / pipeline convention: Customise means Yes (case-insensitive)."""

    if pd.isna(val):

        return False

    return str(val).strip().lower() == "yes"





def _logo_design_from_position_suffixes(base: str, positions: list[str]) -> str:

    return ", ".join(f"{base}-{p}" for p in positions)





def apply_x_xz_logo_design_image(

    matched_df: pd.DataFrame,

    multiple_positions_df: pd.DataFrame | None,

    log: Optional[Callable[[str], None]] = None,

) -> None:

    """

    Rewrite Logo/Design Image using the Multiple Positions sheet.



    For non-personalized matched rows with a Logo ID:

    - If Position Code matches a row on the Multiple Positions sheet, set

      Logo/Design Image to comma-separated base-suffix tokens (e.g. 103671LG-f, 103671LG-b).

    - Otherwise leave Logo/Design Image unchanged from step 3.



    Personalized rows (Customise = Yes) are skipped; Logo/Design Image stays as step 3 wrote it.

    """

    for col in ("Position Code", "Logo ID", "Logo/Design Image"):

        if col not in matched_df.columns:

            return



    has_customise = "Customise" in matched_df.columns

    mp_rows = 0



    for idx, row in matched_df.iterrows():

        if has_customise and _customise_is_yes(row.get("Customise")):

            continue



        logo_id = _normalize_label(row.get("Logo ID"))

        if not logo_id:

            continue



        pos_code = _normalize_label(row.get("Position Code"))

        positions = _multiple_positions_lookup(multiple_positions_df, pos_code)

        if positions:

            matched_df.at[idx, "Logo/Design Image"] = _logo_design_from_position_suffixes(

                logo_id, positions

            )

            mp_rows += 1



    if log and mp_rows:

        log(

            f"  Step 4 Logo/Design: {mp_rows} row(s) expanded via Multiple Positions sheet "

            "(e.g. LogoID-f, LogoID-b). Customise=Yes rows are skipped."

        )


