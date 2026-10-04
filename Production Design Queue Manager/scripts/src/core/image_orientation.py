"""Optional orientation for size-referenced designs.

ENABLE_AUTO_ORIENTATION: pick original vs 90° by output area (IronOn only).
ENABLE_A3_LANDSCAPE: A3 size_code forces rotate 90° + swap size box (skips IronOn).
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple, Union

from PIL import Image

from src.system.logging.utils import get_run_logger
from src.core.image_orientation_impl import (
    A3_SIZE_CODE,
    IRON_ON_MARKER,
    apply_a3_landscape_transform,
    is_a3_size,
    is_iron_on_order,
    swap_size_info_landscape,
)

ENABLE_AUTO_ORIENTATION = True
ENABLE_A3_LANDSCAPE = True

DimensionCalculator = Callable[..., Tuple[int, int, float, float, str]]


@dataclass(frozen=True)
class OrientationChoice:
    """Image and constrained dimensions for the chosen orientation."""

    image: Image.Image
    width_px: int
    height_px: int
    width_mm: float
    height_mm: float
    rotated: bool


def _design_area(width_px: int, height_px: int) -> int:
    return width_px * height_px


def _result_matches_target_orientation(
    width_px: int, height_px: int, size_info: Dict[str, Any]
) -> bool:
    target_landscape = size_info["width_px"] >= size_info["height_px"]
    result_landscape = width_px >= height_px
    return target_landscape == result_landscape


def _is_square_skip_trial(img: Image.Image, size_info: Dict[str, Any]) -> bool:
    return (
        img.width == img.height
        and size_info["width_px"] == size_info["height_px"]
    )


def _pick_orientation(
    area_orig: int,
    area_rot: int,
    orig_w: int,
    orig_h: int,
    rot_w: int,
    rot_h: int,
    size_info: Dict[str, Any],
) -> bool:
    """Return True to use the 90°-rotated orientation."""
    if area_rot > area_orig:
        return True
    if area_rot < area_orig:
        return False
    orig_match = _result_matches_target_orientation(orig_w, orig_h, size_info)
    rot_match = _result_matches_target_orientation(rot_w, rot_h, size_info)
    return rot_match and not orig_match


def select_best_orientation(
    img: Image.Image,
    size_info: Dict[str, Any],
    calculate_dimensions: DimensionCalculator,
    mm_to_pixel_factor: float,
    is_pocket: bool = False,
    is_sleeve: bool = False,
    item_sku: Optional[str] = None,
    order_number: Optional[str] = None,
    canvas_width_mm: Optional[float] = None,
    canvas_height_mm: Optional[float] = None,
    design_padding: int = 25,
    filename_position_token: Optional[str] = None,
) -> OrientationChoice:
    """
    Choose original or 90°-rotated orientation for size-referenced resizing.

    Args:
        img: Source image (unrotated).
        size_info: Size reference dict (required).
        calculate_dimensions: Typically image_resizing.calculate_image_dimensions.
    """
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
    }

    orig_w, orig_h, orig_w_mm, orig_h_mm, _ = calculate_dimensions(
        img, size_info, **dim_kwargs
    )
    area_orig = _design_area(orig_w, orig_h)

    if _is_square_skip_trial(img, size_info):
        return OrientationChoice(
            image=img,
            width_px=orig_w,
            height_px=orig_h,
            width_mm=orig_w_mm,
            height_mm=orig_h_mm,
            rotated=False,
        )

    rotated_img = img.rotate(90, expand=True)
    rot_w, rot_h, rot_w_mm, rot_h_mm, _ = calculate_dimensions(
        rotated_img, size_info, **dim_kwargs
    )
    area_rot = _design_area(rot_w, rot_h)

    if not _pick_orientation(
        area_orig, area_rot, orig_w, orig_h, rot_w, rot_h, size_info
    ):
        return OrientationChoice(
            image=img,
            width_px=orig_w,
            height_px=orig_h,
            width_mm=orig_w_mm,
            height_mm=orig_h_mm,
            rotated=False,
        )

    logger = get_run_logger()
    logger.debug(
        "orientation=rotated_90 area_orig=%s area_rot=%s -> using rotated",
        area_orig,
        area_rot,
    )
    return OrientationChoice(
        image=rotated_img,
        width_px=rot_w,
        height_px=rot_h,
        width_mm=rot_w_mm,
        height_mm=rot_h_mm,
        rotated=True,
    )


def apply_orientation_if_enabled(
    img: Image.Image,
    size_info: Optional[Dict[str, Any]],
    calculate_dimensions: DimensionCalculator,
    allow_orientation: bool = False,
    **dim_kwargs: Any,
) -> Tuple[Image.Image, int, int, float, float]:
    """
    Return (working_image, width_px, height_px, width_mm, height_mm).

    If size_info is missing, auto-orientation is disabled, or allow_orientation
    is False (non–IronOn orders), dimensions are computed for the original image only.
    """
    if size_info is None or not ENABLE_AUTO_ORIENTATION or not allow_orientation:
        w, h, w_mm, h_mm, _ = calculate_dimensions(img, size_info, **dim_kwargs)
        return img, w, h, w_mm, h_mm

    choice = select_best_orientation(
        img, size_info, calculate_dimensions, **dim_kwargs
    )
    if choice.rotated:
        # Packing Pass 2 must undo with -90°, not apply another +90°.
        setattr(choice.image, "_orient_rotated", True)
    return (
        choice.image,
        choice.width_px,
        choice.height_px,
        choice.width_mm,
        choice.height_mm,
    )
