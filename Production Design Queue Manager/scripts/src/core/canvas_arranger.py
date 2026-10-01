"""Canvas packing — stable façade."""

from __future__ import annotations

from src.core.canvas_arranger_impl import pack_designs
from src.core.canvas_arranger_rotate import (
    _create_design_dict,
    _fill_row_spare_with_landscape,
    _packing_width_for_fit_check,
    _place_completed_row,
    _rotate_landscape_for_packing,
    _row_width_needed,
)
from src.core.canvas_arranger_row import (
    _handle_row_full,
    _start_new_batch,
    _try_add_design_to_row,
)

__all__ = [
    "pack_designs",
]
