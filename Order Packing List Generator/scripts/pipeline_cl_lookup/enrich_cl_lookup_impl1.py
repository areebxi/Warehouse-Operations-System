"""CL enrich logic — re-exports apply helpers + enrich_packing_data entry."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_runtime.order_number_csv import read_csv_with_order_numbers

from .enrich_cl_apply import (
    apply_cl_enrichment,
    build_cl_lookup,
    load_cl_database,
    _item_name_indicates_custom,
    _item_options_indicates_custom,
)
from .enrich_cl_const import DEFAULT_CL_CSV

__all__ = [
    "apply_cl_enrichment",
    "build_cl_lookup",
    "enrich_packing_data",
    "load_cl_database",
    "_item_name_indicates_custom",
    "_item_options_indicates_custom",
]


def enrich_packing_data(
    step1_csv_path: Path,
    workbook_path: Path | None = None,
    log: Optional[Callable[[str], None]] = None,
    *,
    cl_lookup: Optional[dict] = None,
    cl_csv_path: Path | None = None,
) -> pd.DataFrame:
    """Enrich Step 1 CSV from live CL CSV."""
    del workbook_path  # CL sheet retired; other pipeline steps still use Workbook.
    df = read_csv_with_order_numbers(step1_csv_path)
    if cl_lookup is None:
        path = Path(cl_csv_path) if cl_csv_path is not None else DEFAULT_CL_CSV
        cl_df = load_cl_database(path)
        lookup = build_cl_lookup(cl_df)
        if log:
            log(
                f"  Step 2 CL: loaded CL CSV {path.resolve()} ({len(cl_df)} rows); "
                f"{len(lookup)} lookup label(s)."
            )
    else:
        lookup = cl_lookup
        if log:
            log(f"  Step 2 CL: using preloaded lookup ({len(lookup)} label(s)).")
    return apply_cl_enrichment(df, lookup, log=log)
