"""Image resizing: calculate dimensions + resize with constraints."""

from src.core.image_resizing_calc import calculate_image_dimensions
from src.core.image_resizing_impl import resize_image_with_constraints
from src.core.image_max_design_size import MAX_DESIGN_HEIGHT_MM, MAX_DESIGN_WIDTH_MM

__all__ = [
    "MAX_DESIGN_HEIGHT_MM",
    "MAX_DESIGN_WIDTH_MM",
    "calculate_image_dimensions",
    "resize_image_with_constraints",
]
