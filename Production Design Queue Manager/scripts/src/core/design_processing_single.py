"""Single-design processing flow."""

from typing import Optional, Dict, Any, Set, Union, List

import pandas as pd

from src.core.design_processing_helpers import (
    resolve_size_lookup_context,
    load_and_resize_design,
    apply_print_size_override_to_entries,
)
from src.core.multi_position_logic import get_position_size_entries, build_positioned_stems
from src.core.cl_print_sizes import get_cl_position_size_entries
from src.core.size_code_extractor import PrintSizeOverrides
from src.io.file_handlers import find_design_file
from src.io.file_search import find_design_file_by_code
from src.io.file_utilities import extract_design_code, remove_apparel_size_prefix
from src.system.logging.utils import get_run_logger


def process_single_designs(
    sku: Union[str, pd.Series],
    designs_folder: str,
    size_reference_df: Optional[pd.DataFrame],
    mm_to_pixel_factor: float,
    pocket_design_ids_set: Optional[Union[Set[str], PrintSizeOverrides]] = None,
    canvas_width_mm: Optional[float] = None,
    canvas_height_mm: Optional[float] = None,
    design_padding: int = 25,
    force_single: bool = False,
    print_size_overrides: Optional[Union[Set[str], PrintSizeOverrides]] = None,
) -> List[Dict[str, Any]]:
    logger = get_run_logger()
    overrides = print_size_overrides if print_size_overrides is not None else pocket_design_ids_set
    size_code, base_code_for_lookup, lookup_size_code = resolve_size_lookup_context(
        sku, size_reference_df, overrides
    )
    # Prefer live CL CSV print sizes (option B); Size References sheet is archive for sizing.
    cl_entries = get_cl_position_size_entries(
        sku, mm_to_pixel_factor, force_single=force_single
    )
    if cl_entries is not None:
        entries = cl_entries
        if size_code is None:
            size_code = str(sku).strip()
    else:
        entries = get_position_size_entries(
            size_reference_df,
            lookup_size_code,
            mm_to_pixel_factor,
            base_code=base_code_for_lookup,
            force_single=force_single,
        )
    entries = apply_print_size_override_to_entries(
        sku, entries, overrides, mm_to_pixel_factor
    )
    base_design_code = extract_design_code(sku)
    base_without_size = remove_apparel_size_prefix(base_design_code) if base_design_code else ""
    base_stems = [s for s in [base_design_code, base_without_size] if s]
    sku_str = str(sku).strip()
    results: List[Dict[str, Any]] = []

    for entry in entries:
        position = entry.get("position")
        size_info = entry.get("size_info")
        design_path = None

        if position and base_stems:
            for stem in build_positioned_stems(base_stems, position):
                design_path = find_design_file_by_code(stem, designs_folder)
                if design_path:
                    break

        if not design_path:
            if position:
                logger.debug(
                    "process_single_designs: position stem not found sku=%s position=%s",
                    sku,
                    position,
                )
            design_path = find_design_file(sku, designs_folder)

        if not design_path:
            continue

        resized = load_and_resize_design(
            design_path,
            size_info,
            mm_to_pixel_factor,
            canvas_width_mm,
            canvas_height_mm,
            design_padding,
            item_sku=sku,
        )
        if not resized:
            continue

        resized_img, width_px, height_px, width_mm, height_mm, effective_size_info = resized
        label = f"{sku_str}-{position}" if position else sku_str
        results.append(
            {
                "sku": label,
                "image": resized_img,
                "path": design_path,
                "width": width_px,
                "height": height_px,
                "width_mm": width_mm,
                "height_mm": height_mm,
                "size_code": size_code,
                "size_info": effective_size_info,
                "position": position,
            }
        )

    return results
