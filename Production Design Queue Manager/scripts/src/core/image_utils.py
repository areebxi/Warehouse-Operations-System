"""
Image utilities for resizing, dimension calculations, and canvas creation.

This module aggregates exports from the more granular `src.core.*` modules
so older imports keep working while the codebase becomes modular.
"""

# Re-export from size_reference
from src.core.size_reference import (
    DEFAULT_DESIGN_PADDING,
    DEFAULT_VERTICAL_PADDING,
    COLOR_BAR_WIDTH,
    COLOR_BAR_SPACING,
    NON_BAR_MARGIN,
    get_size_from_reference,
)

# Re-export from image_resizing
from src.core.image_resizing import (
    calculate_image_dimensions,
    resize_image_with_constraints,
)

# Re-export from image_orientation (optional feature; off via ENABLE_AUTO_ORIENTATION)
from src.core.image_orientation import (
    ENABLE_AUTO_ORIENTATION,
    OrientationChoice,
    is_iron_on_order,
    select_best_orientation,
)

# Re-export from canvas_creation
from src.core.canvas_creation import (
    create_canvas_image,
    save_canvas_image,
)

__all__ = [
    # Constants
    "DEFAULT_DESIGN_PADDING",
    "DEFAULT_VERTICAL_PADDING",
    "COLOR_BAR_WIDTH",
    "COLOR_BAR_SPACING",
    "NON_BAR_MARGIN",
    # Size reference functions
    "get_size_from_reference",
    # Image resizing functions
    "calculate_image_dimensions",
    "resize_image_with_constraints",
    # Orientation optimization (optional)
    "ENABLE_AUTO_ORIENTATION",
    "OrientationChoice",
    "is_iron_on_order",
    "select_best_orientation",
    # Canvas creation functions
    "create_canvas_image",
    "save_canvas_image",
]

