"""Fill newly seeded CL rows with the same steps as fill_from_seeds."""
from __future__ import annotations

import pandas as pd

from fill_from_seeds import (
    DEFAULT_CONFIG,
    DEFAULT_PRINT_SIZES,
    load_overrides,
    load_print_sizes,
    load_size_ref_index,
    pe_sizes_from_index,
    step_apparel_image,
    step_areeb,
    step_customise,
    step_dedicated_suppliers,
    step_pe_enrich,
    step_print_sizes,
    step_printing_type,
    step_supplier_name,
    step_supplier_sku,
    step_supply,
)


def fill_rows(df: pd.DataFrame, pe_index: pd.DataFrame, counts: dict) -> None:
    step_supplier_sku(df, counts)
    step_pe_enrich(df, pe_index, counts)
    step_dedicated_suppliers(df, counts)
    step_apparel_image(df, counts)
    print("  loading Size References + Shirts Print Sizes...", flush=True)
    size_index = load_size_ref_index(DEFAULT_CONFIG)
    overrides = load_overrides(DEFAULT_CONFIG)
    ps_table = load_print_sizes(DEFAULT_PRINT_SIZES)
    pe_sizes = pe_sizes_from_index(pe_index)
    step_print_sizes(
        df,
        size_index,
        overrides,
        ps_table,
        counts,
        only_missing_wh=False,
        pe_sizes=pe_sizes,
    )
    step_customise(df, counts)
    step_areeb(df, counts)
    step_supply(df, counts)
    step_printing_type(df, counts)
    step_supplier_name(df, counts)
