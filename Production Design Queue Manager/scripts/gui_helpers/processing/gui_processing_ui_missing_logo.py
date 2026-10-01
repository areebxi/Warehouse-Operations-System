"""Missing-logo GUI processing flow."""

from __future__ import annotations

import os
import time
import traceback
from datetime import datetime
from tkinter import messagebox

from src.system.logging.utils import (
    start_size_determination_log,
    finish_size_determination_log,
    save_error_to_file,
    get_run_logger,
)
from src.system.logging.run_logger import log_run_event
from src.core.canvas_arranger import pack_designs
from gui_helpers.common.gui_progress import update_progress, reset_progress
from .gui_processing_helpers import (
    auto_detect_customise_column,
    handle_missing_designs_error,
    handle_missing_designs_warning,
    finalize_arrangement,
)
from .gui_processing_ui_missing_logo_load import load_missing_logo_designs


def process_missing_logo_file(
    gui, df, order_column, sku_column, file_path=None, show_progress=True
):
    """Process missing-logo mode for one file."""
    logger = get_run_logger()
    try:
        started_at = time.perf_counter()
        gui.is_personalised = True
        start_size_determination_log(file_path, "missing_logo")
        customise_col = auto_detect_customise_column(df)
        mask = df[order_column].notna() & df[sku_column].notna()
        order_numbers = df.loc[mask, order_column].tolist()
        item_skus = df.loc[mask, sku_column].tolist()
        customise_vals = (
            df.loc[mask, customise_col].tolist()
            if customise_col
            else [None] * len(order_numbers)
        )
        log_run_event(
            "processing_started",
            mode="missing_logo",
            file_path=file_path or getattr(gui, "input_file_path", None),
            order_column=order_column,
            sku_column=sku_column,
            rows_total=len(df),
            orders_total=len(order_numbers),
            item_skus_total=len(item_skus),
        )
        if not order_numbers:
            messagebox.showwarning("Warning", "No Order Numbers found in selected column!")
            finish_size_determination_log()
            return
        if len(order_numbers) != len(item_skus):
            messagebox.showwarning(
                "Warning", "Order Number and Item SKU columns have different lengths!"
            )
            finish_size_determination_log()
            return

        designs = []
        missing_orders = []
        missing_sizes = []
        missing_size_row_indices = []
        total_orders = len(order_numbers)
        log_stats = {
            "total_designs": 0,
            "personalised_found": 0,
            "all_in_one_found": 0,
            "size_reference_used": 0,
            "original_dimensions_used": 0,
        }
        order_total_counts = {}
        for order_number in order_numbers:
            order_total_counts[order_number] = order_total_counts.get(order_number, 0) + 1

        load_missing_logo_designs(
            gui,
            df=df,
            order_column=order_column,
            sku_column=sku_column,
            order_numbers=order_numbers,
            item_skus=item_skus,
            customise_vals=customise_vals,
            order_total_counts=order_total_counts,
            show_progress=show_progress,
            total_orders=total_orders,
            missing_sizes=missing_sizes,
            missing_size_row_indices=missing_size_row_indices,
            missing_orders=missing_orders,
            log_stats=log_stats,
            designs=designs,
        )

        if not designs:
            log_run_event(
                "processing_completed",
                level="warning",
                mode="missing_logo",
                file_path=file_path or getattr(gui, "input_file_path", None),
                designs_total=0,
                missing_designs_total=len(missing_orders),
                missing_sizes_total=len(missing_sizes),
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
            handle_missing_designs_error(missing_orders, file_path, "missing_logo")
            finish_size_determination_log()
            return

        handle_missing_designs_warning(missing_orders, file_path, "missing_logo")
        if missing_sizes:
            saved_file = gui.save_missing_size_reference_rows(
                df, missing_size_row_indices, file_path
            )
            warning_msg = (
                f"Could not find size reference for {len(missing_sizes)} designs in "
                f"{os.path.basename(file_path) if file_path else 'file'}:\n"
                + ", ".join(missing_sizes[:10])
                + ("..." if len(missing_sizes) > 10 else "")
                + "\n\nUsing image dimensions instead."
            )
            if saved_file:
                warning_msg += (
                    f"\n\nRows with missing size references have been saved to:\n{saved_file}"
                )
            messagebox.showwarning("Warning", warning_msg)

        if show_progress:
            update_progress(gui, 60, "Arranging designs on canvas...")
        batches = pack_designs(
            designs, gui.canvas_width_mm, gui.canvas_height_mm, gui.mm_to_pixel, gui.design_padding
        )
        log_run_event(
            "processing_completed",
            mode="missing_logo",
            file_path=file_path or getattr(gui, "input_file_path", None),
            orders_total=total_orders,
            designs_total=len(designs),
            batches_total=len(batches),
            missing_designs_total=len(missing_orders),
            missing_sizes_total=len(missing_sizes),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )
        finish_size_determination_log(log_stats)
        finalize_arrangement(gui, batches, show_progress, file_path, "missing_logo")

    except Exception as e:
        try:
            finish_size_determination_log()
        except Exception:
            pass
        try:
            if show_progress:
                reset_progress(gui)
        except Exception:
            pass
        try:
            messagebox.showerror("Error", f"Failed to arrange designs:\n{str(e)}")
        except Exception:
            pass
        traceback.print_exc()
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        content = (
            "Failed to Arrange Designs (Missing Logo Mode)\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"File: {os.path.basename(file_path) if file_path else 'Unknown file'}\n"
            f"Error: {e}\n\n{'=' * 80}\nFull Traceback:\n{error_traceback}\n"
        )
        save_error_to_file(content, "error")
        logger.error(
            "process_missing_logo_file: exception while processing file=%s error=%s",
            os.path.basename(file_path) if file_path else None,
            e,
        )
        log_run_event(
            "processing_failed",
            level="error",
            mode="missing_logo",
            file_path=file_path or getattr(gui, "input_file_path", None),
            error=str(e),
        )
