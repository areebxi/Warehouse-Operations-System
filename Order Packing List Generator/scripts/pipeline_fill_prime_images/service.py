from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import (
    coerce_order_number_columns,
    read_csv_with_order_numbers,
)

from .config import PREFIX_STEP2, REQUIRED_COLUMNS
from .helpers import (
    _customise_is_yes,
    _extract_normal_logo_tokens,
    _first_per_token,
    _is_prime,
    _order_number_as_logo_token,
)


def fill_packing_columns_df(
    df: pd.DataFrame,
    log: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """Fill Prime / Apparel Image / Logo/Design Image on an in-memory DataFrame."""
    df = coerce_order_number_columns(df.copy())

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Step-2 data is missing required column(s): {', '.join(missing)}"
        )

    for col in ("Prime", "Apparel Image", "Logo/Design Image"):
        df[col] = df[col].astype(object)
    df["Logo ID"] = ""

    n_prime_yes = 0
    n_customise_logo = 0
    n_sku_logo_tokens = 0
    n_per_forced_custom = 0
    n_empty_logo = 0

    for idx, row in df.iterrows():
        if _is_prime(row.get("Tags")):
            df.at[idx, "Prime"] = "Yes"
            n_prime_yes += 1
        else:
            df.at[idx, "Prime"] = ""

        pn = row.get("Picture Name")
        df.at[idx, "Apparel Image"] = (
            "" if pd.isna(pn) else (str(pn).strip() if isinstance(pn, str) else str(pn))
        )

        if _customise_is_yes(row.get("Customise")):
            order_num = row.get("Order Number")
            df.at[idx, "Logo/Design Image"] = _order_number_as_logo_token(order_num)
            item_sku = row.get("Item SKU")
            logo_id = _extract_normal_logo_tokens(item_sku)
            if not logo_id:
                logo_id = _first_per_token(item_sku)
            df.at[idx, "Logo ID"] = logo_id
            n_customise_logo += 1
        else:
            item_sku = row.get("Item SKU")
            normal_list = _extract_normal_logo_tokens(item_sku)
            if normal_list:
                df.at[idx, "Logo/Design Image"] = normal_list
                df.at[idx, "Logo ID"] = normal_list
                n_sku_logo_tokens += 1
            else:
                per_token = _first_per_token(item_sku)
                if per_token:
                    order_num = row.get("Order Number")
                    df.at[idx, "Logo/Design Image"] = _order_number_as_logo_token(order_num)
                    df.at[idx, "Customise"] = "Yes"
                    df.at[idx, "Logo ID"] = per_token
                    n_per_forced_custom += 1
                else:
                    df.at[idx, "Logo/Design Image"] = ""
                    df.at[idx, "Logo ID"] = ""
                    n_empty_logo += 1

    if log:
        n = len(df)
        log(
            f"  Step 3 fill: Apparel Image = Picture Name for all {n} row(s). "
            f"Prime=Yes on {n_prime_yes} row(s)."
        )
        log(
            f"  Step 3 Logo/Design Image: {n_customise_logo} row(s) already Customise=Yes -> value from Order Number; "
            f"{n_sku_logo_tokens} row(s) from LG/TSU/AV/HK/fawad tokens in Item SKU; "
            f"{n_per_forced_custom} row(s) used …PER token in SKU -> Order Number + forced Customise=Yes; "
            f"{n_empty_logo} row(s) left blank (no tokens)."
        )

    return df


def fill_packing_columns(
    step2_csv_path: Path,
    log: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """Read step-2 CSV, fill Prime / Apparel Image / Logo/Design Image; return DataFrame."""
    df = read_csv_with_order_numbers(step2_csv_path)
    return fill_packing_columns_df(df, log=log)


def fill_apparel_and_logo_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill Apparel Image and Logo/Design Image columns in a DataFrame (e.g. from Missing Logos Excel).
    Uses same logic as fill_packing_columns: Apparel Image = Picture Name;
    Logo/Design Image = Order Number if Customise Yes, else LG/TSU/AV/HK/fawad tokens from Item SKU.
    Adds columns if missing; overwrites if present.
    """
    df = coerce_order_number_columns(df.copy())
    for col in ("Apparel Image", "Logo/Design Image"):
        if col not in df.columns:
            df[col] = ""
    if "Customise" not in df.columns:
        df["Customise"] = ""
    for idx, row in df.iterrows():
        pn = row.get("Picture Name")
        df.at[idx, "Apparel Image"] = (
            "" if pd.isna(pn) else (str(pn).strip() if isinstance(pn, str) else str(pn))
        )
        if _customise_is_yes(row.get("Customise")):
            order_num = row.get("Order Number")
            df.at[idx, "Logo/Design Image"] = _order_number_as_logo_token(order_num)
        else:
            item_sku = row.get("Item SKU")
            normal_list = _extract_normal_logo_tokens(item_sku)
            if normal_list:
                df.at[idx, "Logo/Design Image"] = normal_list
            else:
                per_token = _first_per_token(item_sku)
                if per_token:
                    order_num = row.get("Order Number")
                    df.at[idx, "Logo/Design Image"] = _order_number_as_logo_token(order_num)
                    df.at[idx, "Customise"] = "Yes"
                else:
                    df.at[idx, "Logo/Design Image"] = ""
    return df


def _token_from_step2_stem(stem: str) -> str:
    """Derive output token from step-2 filename stem (e.g. 2_enrich_cl_lookup_XYZ -> XYZ)."""
    if stem.startswith(PREFIX_STEP2):
        return stem[len(PREFIX_STEP2) :]
    return stem

