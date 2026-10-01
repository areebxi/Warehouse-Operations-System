"""Landscape/portrait rotate helpers for canvas packing."""
from src.core.image_utils import NON_BAR_MARGIN
from src.core.canvas_placement import place_row_grid
from typing import List, Dict, Any, Optional

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
