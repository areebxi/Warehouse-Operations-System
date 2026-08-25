"""Shared helper utilities for design processing flows."""

from typing import Optional, Dict, Any, Set, Union, Tuple, List, Mapping

import pandas as pd
from PIL import Image

from src.core.image_orientation import (
    ENABLE_A3_LANDSCAPE,
    apply_a3_landscape_transform,
    is_a3_size,
    is_iron_on_order,
)
from src.core.image_utils import resize_image_with_constraints
from src.core.size_code_extractor import (
    extract_size_code,
    build_print_size_override_info,
    PrintSizeOverrides,
)


def resolve_size_lookup_context(
    sku: Union[str, pd.Series],
    size_reference_df: Optional[pd.DataFrame],
    print_size_overrides: Optional[Union[PrintSizeOverrides, Set[str], Mapping]] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Resolve raw size code and reference lookup context."""
    size_code = extract_size_code(sku, size_reference_df, print_size_overrides)
    base_code_for_lookup = None
    lookup_size_code = size_code
    if isinstance(size_code, str) and "|" in size_code:
        parts = size_code.split("|", 1)
        if len(parts) == 2:
            base_code_for_lookup, lookup_size_code = parts[0], parts[1]
    return size_code, base_code_for_lookup, lookup_size_code


def apply_print_size_override_to_entries(
    sku: Union[str, pd.Series],
    entries: List[Dict[str, Any]],
    print_size_overrides: Optional[Union[PrintSizeOverrides, Set[str], Mapping]],
    mm_to_pixel_factor: float,
) -> List[Dict[str, Any]]:
    """Replace each entry's size_info when SKU matches Override Print Size."""
    override_info = build_print_size_override_info(
        sku, print_size_overrides, mm_to_pixel_factor
    )
    if override_info is None or not entries:
        return entries

    updated: List[Dict[str, Any]] = []
    for entry in entries:
        new_entry = dict(entry)
        new_entry["size_info"] = override_info
        updated.append(new_entry)
    return updated


def load_and_resize_design(
    design_path: str,
    size_info: Optional[Dict[str, Any]],
    mm_to_pixel_factor: float,
    canvas_width_mm: Optional[float],
    canvas_height_mm: Optional[float],
    design_padding: int,
    is_pocket: bool = False,
    is_sleeve: bool = False,
    item_sku: Optional[Union[str, pd.Series]] = None,
    order_label: Optional[Union[str, int]] = None,
) -> Optional[Tuple[Image.Image, int, int, float, float, Optional[Dict[str, Any]]]]:
    """Load a design image and resize according to constraints.

    Returns (image, width_px, height_px, width_mm, height_mm, effective_size_info).
    effective_size_info reflects any A3 landscape swap applied before resize.
    """
    try:
        img = Image.open(design_path)
        effective_size_info: Optional[Dict[str, Any]] = size_info
        allow_orientation = is_iron_on_order(item_sku, order_label)
        if ENABLE_A3_LANDSCAPE and size_info and is_a3_size(size_info):
            img, effective_size_info = apply_a3_landscape_transform(img, size_info)
            allow_orientation = False
        resize_kwargs = {
            "is_pocket": is_pocket,
            "is_sleeve": is_sleeve,
            "item_sku": item_sku,
            "order_number": order_label,
            "canvas_width_mm": canvas_width_mm,
            "canvas_height_mm": canvas_height_mm,
            "design_padding": design_padding,
            "allow_orientation": allow_orientation,
        }
        if size_info:
            resized = resize_image_with_constraints(
                img,
                effective_size_info,
                mm_to_pixel_factor,
                **resize_kwargs,
            )
            return (*resized, effective_size_info)
        if canvas_width_mm is not None or canvas_height_mm is not None:
            resized = resize_image_with_constraints(
                img,
                None,
                mm_to_pixel_factor,
                **resize_kwargs,
            )
            return (*resized, None)

        width_px, height_px = img.width, img.height
        return (
            img,
            width_px,
            height_px,
            width_px / mm_to_pixel_factor,
            height_px / mm_to_pixel_factor,
            None,
        )
    except Exception:
        return None
