"""Row-fit / batch-boundary helpers for canvas packing."""
from src.core.canvas_placement import place_row_grid
from src.core.canvas_arranger_rotate import (
    _create_design_dict,
    _place_completed_row,
    _row_width_needed,
)
from typing import List, Dict, Any, Optional, Tuple

def _try_add_design_to_row(
    design: Dict[str, Any],
    row_designs: List[Dict[str, Any]],
    row_height: int,
    current_y: int,
    effective_canvas_width: int,
    canvas_height_px: int,
    horizontal_padding: int,
    vertical_padding: int,
) -> Tuple[bool, Optional[int]]:
    """Try to add design to current row if it fits."""
    img = design['image']
    img_width = img.width
    img_height = img.height
    total_height_needed = img_height + vertical_padding

    widths = [d['width'] for d in row_designs] + [img_width]
    if _row_width_needed(widths, horizontal_padding) <= effective_canvas_width:
        potential_row_height = max(row_height, total_height_needed)

        # Check if current row (after adding this design) fits in canvas height
        if current_y + potential_row_height <= canvas_height_px - vertical_padding:
            return True, potential_row_height

    return False, None


def _start_new_batch(
    batches: List[List[Dict[str, Any]]],
    current_batch: List[Dict[str, Any]],
    row_designs: List[Dict[str, Any]],
    current_y: int,
    effective_canvas_width: int,
    horizontal_padding: int,
    vertical_padding: int,
) -> Tuple[List[Dict[str, Any]], int, List[Dict[str, Any]], int]:
    """Start a new batch, placing remaining row designs as last row."""
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

    return [], vertical_padding, [], 0


def _handle_row_full(
    row_designs: List[Dict[str, Any]],
    design: Dict[str, Any],
    current_y: int,
    row_height: int,
    effective_canvas_width: int,
    canvas_height_px: int,
    horizontal_padding: int,
    vertical_padding: int,
    current_batch: List[Dict[str, Any]],
    batches: List[List[Dict[str, Any]]]
) -> Tuple[List[Dict[str, Any]], int, int, bool]:
    """Handle case when current row is full."""
    row_count = len(row_designs)
    saved_y = current_y

    # Place current row first (complete the row; fill spare after packing)
    placed_row_height = row_height
    if row_designs:
        placed_row_height = _place_completed_row(
            row_designs,
            current_y,
            effective_canvas_width,
            horizontal_padding,
            vertical_padding,
            current_batch,
            is_last_row=False,
        )

    new_current_y = current_y + placed_row_height

    img = design['image']
    total_height_needed = img.height + vertical_padding

    # Check if new row (with this design) fits in canvas height
    if new_current_y + total_height_needed > canvas_height_px - vertical_padding:
        # Current canvas is full, start new batch
        if row_count > 0 and current_batch:
            # Remove last row_count designs from current_batch
            for _ in range(row_count):
                if current_batch:
                    current_batch.pop()

            # Re-place already-filled row as the last row of this batch
            place_row_grid(
                row_designs,
                saved_y,
                effective_canvas_width,
                horizontal_padding,
                current_batch,
                is_last_row=True,
            )

        if current_batch:
            batches.append(current_batch)
        current_batch = []
        new_current_y = vertical_padding

        new_row_designs = [
            _create_design_dict(design, img.width, img.height, horizontal_padding, vertical_padding)
        ]
        new_row_height = total_height_needed
        return new_row_designs, new_current_y, new_row_height, True

    new_row_designs = [
        _create_design_dict(design, img.width, img.height, horizontal_padding, vertical_padding)
    ]
    new_row_height = total_height_needed
    return new_row_designs, new_current_y, new_row_height, False
