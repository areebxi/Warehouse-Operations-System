"""
Step 2: Enrich packing data from live Custom Label Database CSV.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_runtime.order_number_csv import read_csv_with_order_numbers

from .enrich_cl_apply import (
    _customise_is_yes,
    _item_name_indicates_custom,
    _item_options_indicates_custom,
    apply_cl_enrichment,
    build_cl_lookup,
    key_after_first_dash,
    load_cl_database,
)
from .enrich_cl_const import (
    CL_DB_COLUMN_ALIASES,
    CUSTOM_LABEL_COL,
    DATA_DIR,
    DEFAULT_CL_CSV,
    DEFAULT_WORKBOOK,
    NEW_COLUMNS,
    PROJECT_ROOT,
    _ITEM_NAME_CUSTOM_KEYWORDS,
    _ITEM_OPTIONS_CUSTOM_PHRASES,
    _WAREHOUSE,
    wh,
)


def enrich_packing_data(
    step1_csv_path: Path,
    workbook_path: Path | None = None,
    log: Optional[Callable[[str], None]] = None,
    *,
    cl_lookup: Optional[dict] = None,
    cl_csv_path: Path | None = None,
) -> pd.DataFrame:
    """
    Enrich Step 1 CSV from live CL CSV.

    ``workbook_path`` is unused for CL lookup (kept for call-site compatibility).
    Pass ``cl_csv_path`` to override the default Custom_Label_Database.csv path.
    """
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


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/enrich_cl_lookup.py <step1_csv> [cl_csv] [output_csv]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    step1 = sys.argv[1]
    cl_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CL_CSV

    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])
    else:
        stem = Path(step1).stem
        prefix = "1_fetch_input_csv_"
        token = stem[len(prefix) :] if stem.startswith(prefix) else stem
        output_path = wh.packing_output_dir() / f"2_enrich_cl_lookup_{token}.csv"

    step1_path = Path(step1)
    output_path = Path(output_path)

    df = enrich_packing_data(step1_path, cl_csv_path=cl_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Enriched {len(df)} rows -> {output_path}")


if __name__ == "__main__":
    main()
