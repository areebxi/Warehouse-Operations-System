"""Personalised-design processing flow."""

from typing import Optional, Dict, Any, Set, Union, List

import pandas as pd

from src.core.design_processing_helpers import (
    resolve_size_lookup_context,
    load_and_resize_design,
    apply_print_size_override_to_entries,
)
from src.core.image_utils import DEFAULT_DESIGN_PADDING
from src.core.multi_position_logic import get_position_size_entries
from src.core.cl_print_sizes import get_cl_position_size_entries
from src.core.size_code_extractor import PrintSizeOverrides
from src.io.file_handlers import find_design_file_vba_logic


def process_personalised_designs(
    order_number: Union[str, int],
    item_sku: Union[str, pd.Series],
    duplicate_index: int,
    is_duplicate_order: bool,
    single_designs_folder: Optional[str],
    double_designs_folder: Optional[str],
    size_reference_df: Optional[pd.DataFrame],
    mm_to_pixel_factor: float,
    canvas_width_mm: float,
    design_padding: Optional[int] = None,
    pocket_design_ids_set: Optional[Union[Set[str], PrintSizeOverrides]] = None,
    canvas_height_mm: Optional[float] = None,
    force_single: bool = False,
    print_size_overrides: Optional[Union[Set[str], PrintSizeOverrides]] = None,
) -> List[Dict[str, Any]]:
    if design_padding is None:
        design_padding = DEFAULT_DESIGN_PADDING

    overrides = print_size_overrides if print_size_overrides is not None else pocket_design_ids_set
    size_code, base_code_for_lookup, lookup_size_code = resolve_size_lookup_context(
        item_sku, size_reference_df, overrides
    )
    cl_entries = get_cl_position_size_entries(
        item_sku, mm_to_pixel_factor, force_single=force_single
    )
    if cl_entries is not None:
        entries = cl_entries
        if size_code is None:
            size_code = str(item_sku).strip()
    else:
        entries = get_position_size_entries(
            size_reference_df,
            lookup_size_code,
            mm_to_pixel_factor,
            base_code=base_code_for_lookup,
            force_single=force_single,
        )
    entries = apply_print_size_override_to_entries(
        item_sku, entries, overrides, mm_to_pixel_factor
    )
    order_str = str(order_number).strip()
    results: List[Dict[str, Any]] = []

    for entry in entries:
        position = entry.get("position")
        size_info = entry.get("size_info")
        search_order = f"{order_str}-{position}" if position else order_str

        single_path, single_type, is_pocket, is_sleeve = find_design_file_vba_logic(
            search_order,
            0 if position else duplicate_index,
            single_designs_folder=single_designs_folder,
            double_designs_folder=double_designs_folder,
            folder_type="single",
            exclude_path=None,
            item_sku=item_sku,
            is_duplicate_order=is_duplicate_order if not position else False,
        )

        if single_path:
            resized = load_and_resize_design(
                single_path,
                size_info,
                mm_to_pixel_factor,
                canvas_width_mm,
                canvas_height_mm,
                design_padding,
                is_pocket=is_pocket,
                is_sleeve=is_sleeve,
                item_sku=item_sku,
                order_label=order_number,
            )
            if resized:
                resized_img, width_px, height_px, width_mm, height_mm, effective_size_info = resized
                label = f"{order_number} (Single)"
                if is_pocket:
                    label = f"{order_number} (Single-Pocket)"
                elif is_sleeve:
                    label = f"{order_number} (Single-Sleeve)"
                if position:
                    label = f"{label}-{position}"
                results.append(
                    {
                        "sku": label,
                        "image": resized_img,
                        "path": single_path,
                        "width": width_px,
                        "height": height_px,
                        "width_mm": width_mm,
                        "height_mm": height_mm,
                        "size_code": size_code,
                        "size_info": effective_size_info,
                        "design_type": single_type,
                        "position": position,
                    }
                )
                continue

        double_path, _, _, _ = find_design_file_vba_logic(
            search_order,
            0 if position else duplicate_index,
            single_designs_folder=single_designs_folder,
            double_designs_folder=double_designs_folder,
            folder_type="double",
            exclude_path=None,
            item_sku=item_sku,
            is_duplicate_order=is_duplicate_order if not position else False,
        )
        if not double_path:
            continue

        resized = load_and_resize_design(
            double_path,
            None,
            mm_to_pixel_factor,
            canvas_width_mm,
            canvas_height_mm,
            design_padding,
            item_sku=item_sku,
            order_label=order_number,
        )
        if not resized:
            continue

        resized_img, width_px, height_px, width_mm, height_mm, _ = resized
        label = f"{order_number} (Double)"
        if position:
            label = f"{label}-{position}"
        results.append(
            {
                "sku": label,
                "image": resized_img,
                "path": double_path,
                "width": width_px,
                "height": height_px,
                "width_mm": width_mm,
                "height_mm": height_mm,
                "size_code": size_code,
                "size_info": size_info,
                "design_type": "double",
                "position": position,
            }
        )

    return results
