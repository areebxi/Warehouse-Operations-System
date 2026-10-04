"""
Image resizing utilities for calculating dimensions and resizing images with constraints.

This module provides:
  - calculate_image_dimensions(...)
  - resize_image_with_constraints(...)
"""
from PIL import Image
from typing import Optional, Dict, Tuple
from src.system.logging.utils import get_run_logger
from src.core.image_orientation import apply_orientation_if_enabled
from src.core.sku_position_hints import target_mm_for_position_token
from src.core.image_max_design_size import apply_max_design_size_mm
from src.core.image_canvas_constraints import apply_canvas_constraints_mm


def calculate_image_dimensions(
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
    filename_position_token: Optional[str] = None,
    apply_max_design_size: bool = True,
) -> Tuple[int, int, float, float, str]:
    """Calculate image dimensions with size constraints (pocket/sleeve + canvas bounds)."""
    logger = get_run_logger()

    original_width = img.width
    original_height = img.height
    original_aspect = original_width / original_height

    hint_mm = target_mm_for_position_token(filename_position_token)
    if hint_mm:
        hint_w_mm, hint_h_mm = hint_mm
        token_label = str(filename_position_token).strip().upper()
        size_info = {
            "width_px": int(hint_w_mm * mm_to_pixel_factor),
            "height_px": int(hint_h_mm * mm_to_pixel_factor),
            "width_mm": float(hint_w_mm),
            "height_mm": float(hint_h_mm),
            "size_code": token_label,
            "match_type": "filename_position_hint",
            "merge_entry": token_label,
        }
        # Hint mm wins — including kids. Do not apply legacy -P.png 65×80.
        is_pocket = False
        is_sleeve = False

    log_lines = []
    log_lines.append(
        f"Sizing image - order: {order_number or 'N/A'}, SKU: {item_sku or 'N/A'}, "
        f"original: {original_width}x{original_height}px, "
        f"pocket={is_pocket}, sleeve={is_sleeve}, "
        f"filename_token={filename_position_token or 'N/A'}"
    )

    if size_info:
        target_width_px = size_info["width_px"]
        target_height_px = size_info["height_px"]
        size_code = size_info.get("size_code", "N/A")
        merge_entry = size_info.get("merge_entry") or size_code
        match_type = size_info.get("match_type", "N/A")
        log_lines.append(
            f"  Size reference: {merge_entry} "
            f"(code={size_code}, match={match_type}) -> "
            f"target {target_width_px}x{target_height_px}px"
        )

        # Apply pocket/sleeve dimension overrides if detected.
        # Skip when Override Print Size already supplied dims (or fallback dims).
        if is_pocket and match_type not in (
            "print_size_override",
            "print_size_override_fallback",
        ):
            sku_str = str(item_sku).upper() if item_sku else ""
            if "-K-" in sku_str:
                target_width_mm = 65.0
                target_height_mm = 80.0
            elif "-M-" in sku_str or "-W-" in sku_str:
                target_width_mm = 80.0
                target_height_mm = 100.0
            else:
                target_width_mm = 80.0
                target_height_mm = 100.0

            target_width_px = int(target_width_mm * mm_to_pixel_factor)
            target_height_px = int(target_height_mm * mm_to_pixel_factor)
            log_lines.append(
                f"  pocket override applied -> target={target_width_px}x{target_height_px}px "
                f"({target_width_mm:.1f}mm x {target_height_mm:.1f}mm)"
            )
        elif is_sleeve:
            target_width_mm = 100.0
            target_height_mm = 100.0
            target_width_px = int(target_width_mm * mm_to_pixel_factor)
            target_height_px = int(target_height_mm * mm_to_pixel_factor)
            log_lines.append(
                f"  sleeve override applied -> target={target_width_px}x{target_height_px}px "
                f"({target_width_mm:.1f}mm x {target_height_mm:.1f}mm)"
            )

        # Choose constraint based on original image orientation
        if img.width > img.height:
            width_px = target_width_px
            height_px = int(target_width_px / original_aspect)
            log_lines.append(
                f"  orientation=landscape -> primary constraint=width "
                f"-> tentative size={width_px}x{height_px}px"
            )
        else:
            height_px = target_height_px
            width_px = int(target_height_px * original_aspect)
            log_lines.append(
                f"  orientation=portrait -> primary constraint=height "
                f"-> tentative size={width_px}x{height_px}px"
            )

        # Validate vs the other constraint and adjust if needed
        if img.width > img.height:
            if height_px > target_height_px:
                log_lines.append(
                    f"  validation: height {height_px}px exceeds target_height_px "
                    f"{target_height_px}px -> recalc using height constraint"
                )
                height_px = target_height_px
                width_px = int(target_height_px * original_aspect)
        else:
            if width_px > target_width_px:
                log_lines.append(
                    f"  validation: width {width_px}px exceeds target_width_px "
                    f"{target_width_px}px -> recalc using width constraint"
                )
                width_px = target_width_px
                height_px = int(target_width_px / original_aspect)

        width_mm = width_px / mm_to_pixel_factor
        height_mm = height_px / mm_to_pixel_factor
        log_lines.append(
            f"  after size reference/overrides -> {width_px}x{height_px}px "
            f"({width_mm:.2f}mm x {height_mm:.2f}mm)"
        )
    else:
        width_px = img.width
        height_px = img.height
        width_mm = width_px / mm_to_pixel_factor
        height_mm = height_px / mm_to_pixel_factor
        log_lines.append(
            f"  no size_info -> using original dimensions {width_px}x{height_px}px "
            f"({width_mm:.2f}mm x {height_mm:.2f}mm)"
        )

    # Apply canvas constraints (if provided)
    width_px, height_px, width_mm, height_mm = apply_canvas_constraints_mm(
        width_px,
        height_px,
        width_mm,
        height_mm,
        mm_to_pixel_factor,
        canvas_width_mm=canvas_width_mm,
        canvas_height_mm=canvas_height_mm,
        design_padding=design_padding,
        log_lines=log_lines,
    )

    # Global max print size: never exceed 300mm × 500mm (skipped for double-folder designs)
    width_px, height_px, width_mm, height_mm = apply_max_design_size_mm(
        width_px,
        height_px,
        width_mm,
        height_mm,
        mm_to_pixel_factor,
        apply_max_design_size=apply_max_design_size,
        log_lines=log_lines,
    )

    log_lines.append(
        f"  final dimensions -> {width_px}x{height_px}px "
        f"({width_mm:.2f}mm x {height_mm:.2f}mm)"
    )

    logger.debug("\n".join(log_lines))

    log_entry = ""
    return width_px, height_px, width_mm, height_mm, log_entry
