from __future__ import annotations
import tkinter as tk
from PIL import Image, ImageTk
from typing import List, Dict, Any, Optional, Tuple

def draw_preview(
    canvas: tk.Canvas,
    arranged_designs: List[Dict[str, Any]],
    all_batches: List[List[Dict[str, Any]]],
    canvas_width_mm: float,
    canvas_height_mm: float,
    mm_to_pixel_factor: float,
    zoom_level: float = 1.0,
    root: Optional[tk.Tk] = None,
) -> None:
    """Draw preview of arranged designs on canvas."""
    try:
        canvas.delete("all")

        batches_to_draw = _prepare_batches_for_preview(arranged_designs, all_batches, canvas)
        if not batches_to_draw:
            return

        preview_width = canvas.winfo_width()
        preview_height = canvas.winfo_height()
        if preview_width <= 1 or preview_height <= 1:
            preview_width = 800
            preview_height = 600

        scale, max_height_px, _ = _calculate_preview_scale(
            batches_to_draw,
            canvas_width_mm,
            canvas_height_mm,
            mm_to_pixel_factor,
            preview_width,
            preview_height,
            zoom_level,
        )

        canvas_width_px = int(canvas_width_mm * mm_to_pixel_factor)
        batch_spacing_px = 200
        border_width = 2
        batch_spacing_px += border_width * 2

        left_padding = 5
        current_x_offset_px = 0

        for batch_num, batch in enumerate(batches_to_draw, 1):
            if not batch:
                continue

            _draw_batch_header(
                canvas,
                batch_num,
                len(batches_to_draw),
                current_x_offset_px,
                canvas_width_px,
                scale,
                max_height_px,
                left_padding,
            )

            scaled_width = canvas_width_px * scale
            scaled_height = max_height_px * scale
            canvas.create_rectangle(
                left_padding + current_x_offset_px * scale,
                0,
                left_padding + current_x_offset_px * scale + scaled_width,
                scaled_height,
                outline="black",
                width=2,
                fill="white",
            )

            for idx, design in enumerate(batch):
                x = left_padding + current_x_offset_px * scale + design["x"] * scale
                y = design["y"] * scale
                width = design["width"] * scale
                height = design["height"] * scale

                _draw_single_design(canvas, design, x, y, width, height, idx)

            current_x_offset_px += canvas_width_px + batch_spacing_px

        bbox = canvas.bbox("all")
        if bbox:
            scroll_region = (bbox[0] - left_padding, bbox[1], bbox[2] + left_padding, bbox[3])
            canvas.config(scrollregion=scroll_region)
        else:
            canvas.config(scrollregion=canvas.bbox("all"))
    except Exception as e:
        print(f"Error drawing preview: {e}")
        import traceback

        traceback.print_exc()
        canvas.create_text(
            400,
            300,
            text=f"Error drawing preview: {str(e)}",
            font=("Arial", 12),
            fill="red",
        )
