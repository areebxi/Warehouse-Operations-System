from __future__ import annotations
from src.core.image_utils import (
    COLOR_BAR_WIDTH,
    COLOR_BAR_SPACING,
    DEFAULT_DESIGN_PADDING,
    DEFAULT_VERTICAL_PADDING,
    NON_BAR_MARGIN,
)
from src.core.canvas_placement import place_row_grid
from typing import List, Dict, Any, Optional, Tuple

def pack_designs(
    designs: List[Dict[str, Any]],
    canvas_width_mm: float,
    canvas_height_mm: float,
    mm_to_pixel_factor: float,
    design_padding: Optional[int] = None
) -> List[List[Dict[str, Any]]]:
    """Pack designs on canvas with grid-based row placement."""
    if design_padding is None:
        design_padding = DEFAULT_DESIGN_PADDING

    # Convert canvas size to pixels
    canvas_width_px = int(canvas_width_mm * mm_to_pixel_factor)
    canvas_height_px = int(canvas_height_mm * mm_to_pixel_factor)

    horizontal_padding = design_padding
    vertical_padding = DEFAULT_VERTICAL_PADDING

    effective_canvas_width = canvas_width_px - COLOR_BAR_WIDTH - COLOR_BAR_SPACING

    for design in designs:
        img = design.get("image")
        if img is not None and getattr(img, "_orient_rotated", False):
            design["_orient_rotated"] = True

    _rotate_landscape_for_packing(
        designs,
        effective_canvas_width,
        horizontal_padding,
        mm_to_pixel_factor,
    )

    batches: List[List[Dict[str, Any]]] = []
    current_batch: List[Dict[str, Any]] = []
    current_y = vertical_padding
    row_designs: List[Dict[str, Any]] = []
    row_height = 0
    design_index = 0

    while design_index < len(designs):
        design = designs[design_index]
        img = design['image']

        fits, potential_row_height = _try_add_design_to_row(
            design,
            row_designs,
            row_height,
            current_y,
            effective_canvas_width,
            canvas_height_px,
            horizontal_padding,
            vertical_padding,
        )

        if fits:
            row_designs.append(
                _create_design_dict(
                    design,
                    img.width,
                    img.height,
                    horizontal_padding,
                    vertical_padding,
                )
            )
            row_height = potential_row_height
            design_index += 1
            continue

        # Row doesn't fit with this design
        if row_designs and current_y + row_height > canvas_height_px - vertical_padding:
            current_batch, current_y, row_designs, row_height = _start_new_batch(
                batches,
                current_batch,
                row_designs,
                current_y,
                effective_canvas_width,
                horizontal_padding,
                vertical_padding,
            )
            continue

        row_designs, current_y, row_height, batch_started = _handle_row_full(
            row_designs,
            design,
            current_y,
            row_height,
            effective_canvas_width,
            canvas_height_px,
            horizontal_padding,
            vertical_padding,
            current_batch,
            batches,
        )

        if batch_started:
            current_batch = []
            design_index += 1
            continue

        design_index += 1

    # Place remaining designs in last row
    if row_designs:
        _place_completed_row(
            row_designs,
            current_y,
            effective_canvas_width,
            horizontal_padding,
            vertical_padding,
            current_batch,
            is_last_row=True,
        )

    if current_batch:
        batches.append(current_batch)

    return batches if batches else [[]]
