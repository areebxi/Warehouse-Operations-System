"""
Canvas arrangement utilities for packing designs on canvas.

This module provides functions for:
    - Packing designs onto a canvas with intelligent row placement
    - Creating batches when designs exceed canvas height
    - Aligning designs within rows (left, center, right alignment based on count)
"""
from src.core.image_utils import (
    COLOR_BAR_WIDTH,
    COLOR_BAR_SPACING,
    DEFAULT_DESIGN_PADDING,
    DEFAULT_VERTICAL_PADDING,
    NON_BAR_MARGIN,
)
from src.core.canvas_placement import place_row_grid
from typing import List, Dict, Any, Optional, Tuple


def _row_width_needed(
    design_widths: List[int],
    horizontal_padding: int,
) -> int:
    """Width needed to place designs in a row (matches place_row_grid)."""
    if not design_widths:
        return 0
    # left margin + designs + (n-1) gaps between them
    return NON_BAR_MARGIN + sum(design_widths) + (len(design_widths) - 1) * horizontal_padding


def _packing_width_for_fit_check(design: Dict[str, Any]) -> Optional[int]:
    """Width a design would use when checking if it can share a row.

    Landscape non-A3 designs are assumed to pack as portrait (narrower side).
    """
    img = design.get('image')
    if img is None:
        return None
    size_code = str(design.get('size_code') or '').strip().upper()
    if size_code == 'A3' or img.width <= img.height:
        return img.width
    return img.height


def _rotate_landscape_for_packing(
    designs: List[Dict[str, Any]],
    effective_canvas_width: int,
    horizontal_padding: int,
    mm_to_pixel_factor: float,
) -> None:
    """Rotate landscape designs 90° to portrait to save canvas width.

    Size codes and resize math are unchanged — only the already-sized image
    is rotated so width and height swap. Squares and A3 are skipped.

    Skip landscape→portrait when both are true:
      1) keeping landscape leaves < 200 mm free beside it
      2) the next logo cannot fit on the same row next to it
    """
    min_free_px = int(200 * mm_to_pixel_factor)

    for idx, design in enumerate(designs):
        size_code = str(design.get('size_code') or '').strip().upper()
        if size_code == 'A3':
            continue
        img = design.get('image')
        if img is None or img.width <= img.height:
            continue

        free_beside = effective_canvas_width - _row_width_needed(
            [img.width], horizontal_padding
        )
        next_cannot_fit = True
        if idx + 1 < len(designs):
            next_width = _packing_width_for_fit_check(designs[idx + 1])
            if next_width is not None:
                next_cannot_fit = (
                    _row_width_needed(
                        [img.width, next_width], horizontal_padding
                    )
                    > effective_canvas_width
                )

        if free_beside < min_free_px and next_cannot_fit:
            continue

        design['image'] = img.rotate(90, expand=True)
        design['_pack_pass1_rotated'] = True


def _fill_row_spare_with_landscape(
    row_designs: List[Dict[str, Any]],
    effective_canvas_width: int,
    horizontal_padding: int,
    vertical_padding: int,
) -> int:
    """After a row is complete, rotate portraits to landscape to use spare width.

    Packing keeps designs portrait so more can share a row. Once the row is
    closed, rotate any portrait that still fits as landscape. Pass1 or IronOn
    auto-orient (+90°) designs use -90° to undo; native portraits use +90°.

    Returns the row height (max design height + vertical padding) after fills.
    """
    if not row_designs:
        return 0

    changed = True
    while changed:
        changed = False
        for design in reversed(row_designs):
            size_code = str(design.get('size_code') or '').strip().upper()
            if size_code == 'A3':
                continue
            img = design.get('image')
            if img is None or img.height <= img.width:
                continue

            landscape_width = img.height
            widths = []
            for d in row_designs:
                if d is design:
                    widths.append(landscape_width)
                else:
                    widths.append(d['width'])

            if _row_width_needed(widths, horizontal_padding) > effective_canvas_width:
                continue

            was_pass1 = bool(design.get('_pack_pass1_rotated'))
            was_orient = bool(design.get('_orient_rotated'))
            # Undo prior +90 (Pass1 or IronOn) with -90 so content is not flipped 180°.
            angle = -90 if (was_pass1 or was_orient) else 90
            design['image'] = img.rotate(angle, expand=True)
            design['width'] = design['image'].width
            design['height'] = design['image'].height
            design['total_width'] = design['width'] + horizontal_padding
            design['total_height'] = design['height'] + vertical_padding
            if was_pass1:
                design['_pack_pass1_rotated'] = False
            if was_orient:
                design['_orient_rotated'] = False
            changed = True

    return max(d['height'] + vertical_padding for d in row_designs)


def _place_completed_row(
    row_designs: List[Dict[str, Any]],
    y: int,
    effective_canvas_width: int,
    horizontal_padding: int,
    vertical_padding: int,
    arranged: List[Dict[str, Any]],
    is_last_row: bool = False,
) -> int:
    """Fill spare width on a finished row, place it, return actual row height."""
    row_height = _fill_row_spare_with_landscape(
        row_designs, effective_canvas_width, horizontal_padding, vertical_padding
    )
    place_row_grid(
        row_designs,
        y,
        effective_canvas_width,
        horizontal_padding,
        arranged,
        is_last_row=is_last_row,
    )
    return row_height


def _create_design_dict(
    design: Dict[str, Any],
    img_width: int,
    img_height: int,
    horizontal_padding: int,
    vertical_padding: int,
) -> Dict[str, Any]:
    """Create design dictionary with dimensions and total space needed."""
    total_width_needed = img_width + horizontal_padding  # Right padding
    total_height_needed = img_height + vertical_padding  # Bottom padding

    return {
        'sku': design['sku'],
        'image': design['image'],
        'width': img_width,
        'height': img_height,
        'total_width': total_width_needed,
        'total_height': total_height_needed,
        'size_code': design.get('size_code'),
        '_pack_pass1_rotated': bool(design.get('_pack_pass1_rotated')),
        '_orient_rotated': bool(design.get('_orient_rotated')),
    }


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
