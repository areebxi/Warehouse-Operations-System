"""Main preview drawing routine."""

import time
import tkinter as tk

from src.system.logging.run_logger import log_run_event

from .gui_preview_helpers import (
    LEFT_PADDING,
    OUTLINE_ALLOWANCE,
    PREVIEW_BG,
    RIGHT_PADDING,
    build_batch_preview_image,
    calculate_preview_scale,
    get_cached_batch_photo,
)


def draw_preview(gui, reuse_cache=False):
    """Draw preview of arranged designs on canvas (all designs, one image per batch).

    reuse_cache: when True (debounced resize), keep PhotoImages whose scale key still matches.
    """
    started_at = time.perf_counter()
    try:
        gui.preview_canvas.delete("all")
        if hasattr(gui, "all_batches") and gui.all_batches and len(gui.all_batches) > 0:
            batches_to_draw = gui.all_batches
        elif gui.arranged_designs:
            batches_to_draw = [gui.arranged_designs]
        else:
            return

        if not reuse_cache:
            gui._preview_photo_cache = {}

        canvas_width_px = int(gui.canvas_width_mm * gui.mm_to_pixel)
        canvas_height_px = int(gui.canvas_height_mm * gui.mm_to_pixel)
        scale, max_height_px, batch_spacing_px = calculate_preview_scale(
            gui, batches_to_draw, canvas_width_px, canvas_height_px
        )
        scale_key = round(scale, 4)

        # Keep strong refs for currently displayed photos; reuse cache when scale matches
        gui._preview_photos = []

        current_x_offset_px = 0
        scaled_height = max_height_px * scale
        scaled_width = canvas_width_px * scale
        designs_drawn = 0

        for batch_num, batch in enumerate(batches_to_draw, 1):
            if not batch:
                continue

            if len(batches_to_draw) > 1:
                label_x_scaled = (
                    LEFT_PADDING
                    + current_x_offset_px * scale
                    + scaled_width / 2
                )
                gui.preview_canvas.create_text(
                    label_x_scaled,
                    -25,
                    text=f"Batch {batch_num} / {len(batches_to_draw)}",
                    font=("Arial", 12, "bold"),
                    fill="red",
                )
                if batch_num > 1:
                    separator_x = LEFT_PADDING + current_x_offset_px * scale
                    gui.preview_canvas.create_line(
                        separator_x,
                        0,
                        separator_x,
                        scaled_height,
                        fill="red",
                        width=2,
                    )

            origin_x = LEFT_PADDING + current_x_offset_px * scale
            gui.preview_canvas.create_rectangle(
                origin_x,
                0,
                origin_x + scaled_width,
                scaled_height,
                outline="black",
                width=2,
                fill=PREVIEW_BG,
            )

            cache_key = (batch_num, scale_key, canvas_width_px, int(max_height_px))
            photo = get_cached_batch_photo(
                gui,
                cache_key,
                lambda b=batch: build_batch_preview_image(
                    b, canvas_width_px, max_height_px, scale
                ),
            )
            gui._preview_photos.append(photo)
            gui.preview_canvas.create_image(origin_x, 0, anchor=tk.NW, image=photo)
            designs_drawn += len(batch)

            current_x_offset_px += canvas_width_px + batch_spacing_px

        # Drop cache entries for other scales to limit memory
        cache = getattr(gui, "_preview_photo_cache", {})
        gui._preview_photo_cache = {
            k: v for k, v in cache.items() if len(k) > 1 and k[1] == scale_key
        }

        # Include outline + right padding so the black border is fully scrollable/visible
        bbox = gui.preview_canvas.bbox("all")
        if bbox:
            gui.preview_canvas.config(
                scrollregion=(
                    bbox[0] - LEFT_PADDING,
                    bbox[1] - 10,
                    bbox[2] + RIGHT_PADDING + OUTLINE_ALLOWANCE,
                    bbox[3] + 50,
                )
            )
        else:
            total_width_needed = (
                len(batches_to_draw) * canvas_width_px
                + (len(batches_to_draw) - 1) * batch_spacing_px
            )
            total_width_scaled = total_width_needed * scale
            total_height_scaled = max_height_px * scale
            gui.preview_canvas.config(
                scrollregion=(
                    0,
                    -50,
                    LEFT_PADDING + total_width_scaled + RIGHT_PADDING + OUTLINE_ALLOWANCE,
                    total_height_scaled + 50,
                )
            )
        gui.preview_canvas.xview_moveto(0)
        gui.preview_canvas.yview_moveto(0)

        # Log full arrange draws only (skip debounced resize redraws that reuse cache)
        if not reuse_cache:
            log_run_event(
                "preview_drawn",
                designs_total=designs_drawn,
                batches_total=len(batches_to_draw),
                scale=round(scale, 4),
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
    except Exception as e:
        import traceback

        traceback.print_exc()
        log_run_event(
            "preview_draw_failed",
            level="error",
            error=str(e),
            reuse_cache=reuse_cache,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )
        gui.preview_canvas.create_text(
            400,
            300,
            text=f"Error drawing preview: {str(e)}",
            font=("Arial", 12),
            fill="red",
        )
