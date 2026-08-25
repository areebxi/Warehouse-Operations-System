"""
Canvas placement utilities for aligning designs within rows.

This module provides functions for placing designs within rows with different
alignment strategies based on the number of designs.
"""
from typing import List, Dict, Any
from src.core.image_utils import DEFAULT_DESIGN_PADDING, NON_BAR_MARGIN


def _create_arranged_design(design: Dict[str, Any], x: int, y: int) -> Dict[str, Any]:
    """Create an arranged design dictionary with position."""
    return {
        'sku': design['sku'],
        'image': design['image'],
        'x': x,
        'y': y,
        'width': design['width'],
        'height': design['height'],
        'size_code': design.get('size_code'),
    }


def place_row_grid(
    row_designs: List[Dict[str, Any]],
    y: int,
    canvas_width: int,
    padding: int,
    arranged: List[Dict[str, Any]],
    is_last_row: bool = False
) -> None:
    """Place a row of designs left-aligned with a fixed minimum gap."""
    num_designs = len(row_designs)
    if num_designs == 0:
        return

    left_margin = NON_BAR_MARGIN
    # Fixed gap (default ~8 mm); leftover width stays on the color-bar side
    gap = padding if padding is not None else DEFAULT_DESIGN_PADDING

    current_x = left_margin
    for idx, design in enumerate(row_designs):
        arranged.append(_create_arranged_design(design, current_x, y))
        current_x += design['width']
        if idx != num_designs - 1:
            current_x += gap
