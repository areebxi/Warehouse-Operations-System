"""Packing-parity design folder routing for Queue DTF Des rows.

Customise = Yes  -> customise Single/Double folders only (by order number).
Otherwise        -> Normal designs folder only (by Item SKU).
No cross-folder fallback (same gate as Packing List PDF logo lookup).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.core.design_processing_personalised import process_personalised_designs
from src.core.design_processing_single import process_single_designs


def is_customise_yes(value: object) -> bool:
    return str(value or "").strip().lower() == "yes"


def find_designs_for_dtf_row(
    *,
    order_number: object,
    item_sku: object,
    customise: object,
    duplicate_index: int,
    is_duplicate_order: bool,
    designs_folder: Optional[str],
    single_designs_folder: Optional[str],
    double_designs_folder: Optional[str],
    mm_to_pixel: float,
    canvas_width_mm: float,
    canvas_height_mm: float,
    design_padding: float,
    print_size_overrides: object,
    cl_csv_path: Optional[object] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Resolve design image(s) for one DTF Des row.

    Returns (design_items, source) where source is ``personalised``, ``standard``,
    or ``""`` when nothing was found.
    """
    force_single = is_customise_yes(customise)
    if force_single:
        if not (single_designs_folder or double_designs_folder):
            return [], ""
        items = process_personalised_designs(
            order_number,
            item_sku,
            duplicate_index,
            is_duplicate_order,
            single_designs_folder,
            double_designs_folder,
            mm_to_pixel,
            canvas_width_mm,
            design_padding,
            print_size_overrides,
            canvas_height_mm=canvas_height_mm,
            force_single=True,
            cl_csv_path=cl_csv_path,
        )
        return (items or []), ("personalised" if items else "")

    if not designs_folder:
        return [], ""
    items = process_single_designs(
        item_sku,
        designs_folder,
        mm_to_pixel,
        print_size_overrides,
        canvas_width_mm=canvas_width_mm,
        canvas_height_mm=canvas_height_mm,
        design_padding=design_padding,
        force_single=False,
        cl_csv_path=cl_csv_path,
    )
    return (items or []), ("standard" if items else "")
