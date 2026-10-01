from __future__ import annotations
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Tuple
import pandas as pd  # type: ignore[import]
from pipeline_cl_lookup.enrich_cl_lookup import NEW_COLUMNS, enrich_packing_data
from pipeline_cl_lookup.fetch_input_csv import (
    OUTPUT_COLUMNS,
    fetch_input_csv,
    write_fetched_csv,
)
from pipeline_assign_process_number.service import run as run_assign_process_number
from pipeline_fill_prime_images.service import fill_packing_columns
from pipeline_packing_rules.service import apply_packing_rules_to_csv
from pipeline_generate_excel_outputs.service import run as run_generate_excel_outputs
from pipeline_generate_packing_list_pdf.runtime_api import (
    build_image_stem_map,
    collect_image_match_details,
    csv_to_pdf,
    format_image_match_log,
    format_missing_report,
    load_position_code_to_draw,
    render_one_pdf,
)
from pipeline_runtime.filter_missing_logos import filter_step6_csvs_for_missing_logos
from pipeline_runtime.pipeline_log import PipelineLog, detail_callable
from pipeline_runtime.runner_missing import run_missing_logos_pipeline
from pipeline_runtime.runner_step6_outputs import run_step6_style_outputs
from pipeline_runtime.runner_step8_pdf import run_step8_pdf_generation_impl
from pipeline_runtime.runner_utils import (
    ALL_ORDERS_PATH,
    _copy_outputs_to_shift_dirs,
    _ensure_dir,
    _move_missing_logo_to_root,
    _move_unmatched_to_root,
    _sanitize_process_for_filename,
    _update_all_orders_log,
    log_csv_preview,
)
from pipeline_split_by_process_item.common import pin_batch_shift
from pipeline_split_by_process_item.service import run as run_split_by_process_and_item_number
from pipeline_split_position.service import run as run_split_and_assign_position_codes
from shared.demo_images import demo_image_lookup, effective_image_dirs  # noqa: E402

def discover_step6_csvs(output_root: Path, token: str) -> list[Path]:
    """Process CSVs left after Step 6 (missing logos already stripped before naming)."""
    exclude_names = {
        f"1_fetch_input_csv_{token}.csv",
        f"1b_apply_rules_{token}.csv",
        f"2_enrich_cl_lookup_{token}.csv",
        f"3_fill_prime_and_images_{token}.csv",
        f"4_matched_split_and_assign_position_codes_{token}.csv",
        f"5_assign_process_number_{token}.csv",
        f"unmatched_orders_{token}.csv",
        f"missing_logo_orders_{token}.csv",
    }
    return sorted(
        p
        for p in output_root.glob("*.csv")
        if p.name not in exclude_names and not p.name.startswith("_")
    )
