"""Standard single-file GUI processing flow."""

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
from src.core.design_processor import process_single_designs
from src.core.canvas_arranger import pack_designs
from gui_helpers.common.gui_progress import update_progress, reset_progress
from .gui_processing_helpers import (
    auto_detect_customise_column,
    create_design_log_entry,
    track_missing_size_reference,
    is_customise_yes,
    is_plainlg_sku,
    handle_missing_designs_error,
    handle_missing_designs_warning,
    finalize_arrangement,
)


def process_single_file(gui, df, column, file_path=None, show_progress=True):
    """Process a single DTF Des file in standard mode."""
    logger = get_run_logger()
    try:
        started_at = time.perf_counter()
        gui.is_personalised = False
        logger.info(
            "process_single_file: starting standard processing for file=%s (column=%s, designs_folder=%s)",
            os.path.basename(file_path) if file_path else None,
            column,
            gui.designs_folder,
        )
        start_size_determination_log(file_path, "standard")
        customise_col = auto_detect_customise_column(df)
        mask = df[column].notna()
        skus = df.loc[mask, column].tolist()
        customise_vals = (
            df.loc[mask, customise_col].tolist()
            if customise_col else [None] * len(skus)
        )
        log_run_event(
            "processing_started",
            mode="standard",
            file_path=file_path or getattr(gui, "input_file_path", None),
            sku_column=column,
            rows_total=len(df),
            skus_total=len(skus),
        )
        if not skus:
            messagebox.showwarning("Warning", "No SKUs found in selected column!")
            finish_size_determination_log()
            return

        designs = []
        missing_skus = []
        missing_sizes = []
        missing_size_row_indices = []
        total_skus = len(skus)
        log_stats = {'total_designs': 0, 'size_reference_used': 0, 'original_dimensions_used': 0, 'resized': 0}

        if show_progress:
            update_progress(gui, 0, f"Loading designs: 0/{total_skus}")

        for idx, (sku, customise) in enumerate(zip(skus, customise_vals)):
            if is_plainlg_sku(sku):
                continue
            if show_progress:
                progress = (idx / total_skus) * 50
                update_progress(gui, progress, f"Loading designs: {idx+1}/{total_skus}")

            size_code = gui.extract_size_code(sku)
            if gui.size_reference_df is not None and size_code:
                size_info = gui.get_size_from_reference(size_code)
                if not size_info:
                    missing_entry = f"{sku} ({size_code})"
                    if missing_entry not in missing_sizes:
                        missing_sizes.append(missing_entry)
                        track_missing_size_reference(df, column, sku, missing_size_row_indices)

            design_items = process_single_designs(
                sku,
                gui.designs_folder,
                gui.size_reference_df,
                gui.mm_to_pixel,
                getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set,
                canvas_width_mm=gui.canvas_width_mm,
                canvas_height_mm=gui.canvas_height_mm,
                design_padding=gui.design_padding,
                force_single=is_customise_yes(customise),
            )

            if design_items:
                for design_data in design_items:
                    log_size_determination(create_design_log_entry(sku, "Standard", design_data))
                    if design_data.get('size_info'):
                        log_stats['size_reference_used'] += 1
                    else:
                        log_stats['original_dimensions_used'] += 1
                    log_stats['total_designs'] += 1
                    designs.append({
                        'sku': design_data['sku'],
                        'image': design_data['image'],
                        'path': design_data['path'],
                        'width': design_data['width'],
                        'height': design_data['height'],
                        'width_mm': design_data['width_mm'],
                        'height_mm': design_data['height_mm'],
                        'size_code': design_data.get('size_code')
                    })
            else:
                missing_skus.append(sku)

        if not designs:
            log_run_event(
                "processing_completed",
                level="warning",
                mode="standard",
                file_path=file_path or getattr(gui, "input_file_path", None),
                designs_total=0,
                missing_designs_total=len(missing_skus),
                missing_sizes_total=len(missing_sizes),
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
            handle_missing_designs_error(missing_skus, file_path, "standard")
            finish_size_determination_log()
            return

        handle_missing_designs_warning(missing_skus, file_path, "standard")
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
            mode="standard",
            file_path=file_path or getattr(gui, "input_file_path", None),
            skus_total=total_skus,
            designs_total=len(designs),
            batches_total=len(batches),
            missing_designs_total=len(missing_skus),
            missing_sizes_total=len(missing_sizes),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
        )
        finish_size_determination_log(log_stats)
        finalize_arrangement(gui, batches, show_progress, file_path, "standard")

    except Exception as e:
        if show_progress:
            reset_progress(gui)
        messagebox.showerror("Error", f"Failed to arrange designs:\n{str(e)}")
        import traceback
        traceback.print_exc()
        error_traceback = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        from datetime import datetime
        content = f"Failed to Arrange Designs\n"
        content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"File: {os.path.basename(file_path) if file_path else 'Unknown file'}\n"
        content += f"Error: {e}\n"
        content += f"\n{'='*80}\n"
        content += f"Full Traceback:\n{error_traceback}\n"
        save_error_to_file(content, "error")
        logger.error("process_single_file: exception while processing file=%s error=%s", os.path.basename(file_path) if file_path else None, e)
        log_run_event(
            "processing_failed",
            level="error",
            mode="standard",
            file_path=file_path or getattr(gui, "input_file_path", None),
            error=str(e),
        )
