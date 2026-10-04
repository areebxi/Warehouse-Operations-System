from __future__ import annotations

from PIL import Image
from typing import Optional, Dict, Tuple

from src.core.image_orientation import apply_orientation_if_enabled
from src.core.image_resizing_calc import calculate_image_dimensions


def resize_image_with_constraints(
    img: Image.Image,
    size_info: Optional[Dict[str, float]],
    mm_to_pixel_factor: float,
    is_pocket: bool = False,
    is_sleeve: bool = False,
    item_sku: Optional[str] = None,
    order_number: Optional[str] = None,
    canvas_width_mm: Optional[float] = None,
    canvas_height_mm: Optional[float] = None,
    design_padding: int = 25,
    allow_orientation: bool = False,
    filename_position_token: Optional[str] = None,
    apply_max_design_size: bool = True,
) -> Tuple[Image.Image, int, int, float, float]:
    """Resize the image to calculated constrained dimensions."""
    dim_kwargs = {
        "mm_to_pixel_factor": mm_to_pixel_factor,
        "is_pocket": is_pocket,
        "is_sleeve": is_sleeve,
        "item_sku": item_sku,
        "order_number": order_number,
        "canvas_width_mm": canvas_width_mm,
        "canvas_height_mm": canvas_height_mm,
        "design_padding": design_padding,
        "filename_position_token": filename_position_token,
        "apply_max_design_size": apply_max_design_size,
    }

    working_img, width_px, height_px, width_mm, height_mm = apply_orientation_if_enabled(
        img,
        size_info,
        calculate_image_dimensions,
        allow_orientation=allow_orientation,
        **dim_kwargs,
    )

    if working_img.width != width_px or working_img.height != height_px:
        resized_img = working_img.resize(
            (width_px, height_px), Image.Resampling.LANCZOS
        )
    else:
        resized_img = working_img

    if getattr(working_img, "_orient_rotated", False):
        setattr(resized_img, "_orient_rotated", True)

    return resized_img, width_px, height_px, width_mm, height_mm
