"""Missing-logo GUI processing flow."""

import os
import time
from tkinter import messagebox

from src.system.logging.utils import (
    start_size_determination_log,
    log_size_determination,
    finish_size_determination_log,
    save_error_to_file,
    get_run_logger,
)
from src.system.logging.run_logger import log_run_event
from src.core.design_processor import process_personalised_designs, process_single_designs
from src.core.canvas_arranger import pack_designs
from gui_helpers.common.gui_progress import update_progress, reset_progress
from .gui_processing_helpers import (
    auto_detect_customise_column,
    create_design_log_entry,
    track_missing_size_reference_multi,
    is_customise_yes,
    is_plainlg_sku,
    handle_missing_designs_error,
    handle_missing_designs_warning,
    finalize_arrangement,
)


def process_missing_logo_file(gui, df, order_column, sku_column, file_path=None, show_progress=True):
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
            if customise_col else [None] * len(order_numbers)
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
            messagebox.showwarning("Warning", "Order Number and Item SKU columns have different lengths!")
            finish_size_determination_log()
            return

        designs = []
        missing_orders = []
        missing_sizes = []
        missing_size_row_indices = []
        total_orders = len(order_numbers)
        log_stats = {'total_designs': 0, 'personalised_found': 0, 'all_in_one_found': 0, 'size_reference_used': 0, 'original_dimensions_used': 0}
        order_total_counts = {}
        for order_number in order_numbers:
            order_total_counts[order_number] = order_total_counts.get(order_number, 0) + 1
        order_occurrences = {}

        if show_progress:
            update_progress(gui, 0, f"Loading designs: 0/{total_orders}")

        for idx, (order_number, item_sku, customise) in enumerate(zip(order_numbers, item_skus, customise_vals)):
            if is_plainlg_sku(item_sku):
                continue
            if show_progress:
                progress = (idx / total_orders) * 50
                update_progress(gui, progress, f"Loading designs: {idx+1}/{total_orders}")

            order_occurrences[order_number] = order_occurrences.get(order_number, 0) + 1
            duplicate_index = order_occurrences[order_number] - 1
            is_duplicate_order = order_total_counts.get(order_number, 0) > 1

            size_code = gui.extract_size_code(item_sku)
            if gui.size_reference_df is not None and size_code:
                size_info = gui.get_size_from_reference(size_code)
                if not size_info:
                    missing_entry = f"{order_number} ({item_sku} - {size_code})"
                    if missing_entry not in missing_sizes:
                        missing_sizes.append(missing_entry)
                        track_missing_size_reference_multi(df, order_column, sku_column, order_number, item_sku, missing_size_row_indices)

            force_single = is_customise_yes(customise)
            design_items = []
            found_in_personalised = False
            if gui.single_designs_folder or gui.double_designs_folder:
                design_items = process_personalised_designs(
                    order_number, item_sku, duplicate_index, is_duplicate_order,
                    gui.single_designs_folder, gui.double_designs_folder, gui.size_reference_df,
                    gui.mm_to_pixel, gui.canvas_width_mm, gui.design_padding,
                    getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set,
                    canvas_height_mm=gui.canvas_height_mm,
                    force_single=force_single,
                )
                found_in_personalised = bool(design_items)
                if design_items:
                    log_stats['personalised_found'] += len(design_items)

            if not design_items and gui.designs_folder:
                design_items = process_single_designs(
                    item_sku, gui.designs_folder, gui.size_reference_df, gui.mm_to_pixel,
                    getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set, canvas_width_mm=gui.canvas_width_mm,
                    canvas_height_mm=gui.canvas_height_mm, design_padding=gui.design_padding,
                    force_single=force_single,
                )
                if design_items:
                    log_stats['all_in_one_found'] += len(design_items)

            if not design_items:
                missing_orders.append(f"{order_number} (SKU: {item_sku})")
                continue

            for design_data in design_items:
                design_type = design_data.get('design_type', 'single')
                if design_type == 'double':
                    log_stats['original_dimensions_used'] += 1
                elif design_data.get('size_info'):
                    log_stats['size_reference_used'] += 1
                else:
                    log_stats['original_dimensions_used'] += 1
                log_stats['total_designs'] += 1
                design_type_for_log = design_type if found_in_personalised else 'Standard'
                log_size_determination(create_design_log_entry(order_number, design_type_for_log, design_data, item_sku))
                designs.append({
                    'sku': design_data['sku'],
                    'image': design_data['image'],
                    'path': design_data['path'],
                    'width': design_data['width'],
                    'height': design_data['height'],
                    'width_mm': design_data['width_mm'],
                    'height_mm': design_data['height_mm'],
                    'size_code': design_data.get('size_code'),
                    'design_type': design_type,
                })

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
            saved_file = gui.save_missing_size_reference_rows(df, missing_size_row_indices, file_path)
            warning_msg = (
                f"Could not find size reference for {len(missing_sizes)} designs in {os.path.basename(file_path) if file_path else 'file'}:\n"
                + ", ".join(missing_sizes[:10])
                + ("..." if len(missing_sizes) > 10 else "")
                + "\n\nUsing image dimensions instead."
            )
            if saved_file:
                warning_msg += f"\n\nRows with missing size references have been saved to:\n{saved_file}"
            messagebox.showwarning("Warning", warning_msg)

        if show_progress:
            update_progress(gui, 60, "Arranging designs on canvas...")
        batches = pack_designs(designs, gui.canvas_width_mm, gui.canvas_height_mm, gui.mm_to_pixel, gui.design_padding)
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
        import traceback
        traceback.print_exc()
        error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        from datetime import datetime
        content = f"Failed to Arrange Designs (Missing Logo Mode)\n"
        content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"File: {os.path.basename(file_path) if file_path else 'Unknown file'}\n"
        content += f"Error: {e}\n"
        content += f"\n{'='*80}\n"
        content += f"Full Traceback:\n{error_traceback}\n"
        save_error_to_file(content, "error")
        logger.error("process_missing_logo_file: exception while processing file=%s error=%s", os.path.basename(file_path) if file_path else None, e)
        log_run_event(
            "processing_failed",
            level="error",
            mode="missing_logo",
            file_path=file_path or getattr(gui, "input_file_path", None),
            error=str(e),
        )
