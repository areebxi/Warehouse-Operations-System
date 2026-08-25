"""Personalised core folder processing flow."""

import os
from datetime import datetime
from tkinter import messagebox

from src.core.canvas_arranger import pack_designs
from src.core.design_processor import extract_size_code, process_personalised_designs
from src.system.logging.utils import (
    finish_size_determination_log,
    log_size_determination,
    save_error_to_file,
    start_size_determination_log,
)
from .gui_processing_helpers import (
    auto_detect_customise_column,
    create_design_log_entry,
    format_missing_items_list,
    handle_missing_sizes_warning,
    is_customise_yes,
    is_plainlg_sku,
    track_missing_size_reference_multi,
)


def process_personalised_file_for_folder(gui, df, order_column, sku_column, file_path):
    """Process a personalised DTF Des file for folder processing."""
    try:
        gui.is_personalised = True
        start_size_determination_log(file_path, "personalised")
        log_stats = {
            "total_designs": 0,
            "single_designs": 0,
            "double_designs": 0,
            "pocket_overrides": 0,
            "sleeve_overrides": 0,
            "size_reference_used": 0,
            "canvas_scaled": 0,
            "original_dimensions_used": 0,
        }

        customise_col = auto_detect_customise_column(df)
        mask = df[order_column].notna() & df[sku_column].notna()
        order_numbers = df.loc[mask, order_column].tolist()
        item_skus = df.loc[mask, sku_column].tolist()
        customise_vals = (
            df.loc[mask, customise_col].tolist()
            if customise_col else [None] * len(order_numbers)
        )
        if not order_numbers or len(order_numbers) != len(item_skus):
            finish_size_determination_log()
            return [], [], []

        designs = []
        missing_orders = []
        missing_sizes = []
        missing_size_row_indices = []
        order_total_counts = {}
        for order_number in order_numbers:
            order_total_counts[order_number] = order_total_counts.get(order_number, 0) + 1
        order_occurrences = {}

        for order_number, item_sku, customise in zip(order_numbers, item_skus, customise_vals):
            if is_plainlg_sku(item_sku):
                continue

            order_occurrences[order_number] = order_occurrences.get(order_number, 0) + 1
            duplicate_index = order_occurrences[order_number] - 1
            is_duplicate_order = order_total_counts.get(order_number, 0) > 1

            overrides = getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set
            size_code = extract_size_code(item_sku, gui.size_reference_df, overrides)
            if gui.size_reference_df is not None and size_code:
                size_info = gui.get_size_from_reference(size_code)
                if not size_info:
                    missing_entry = f"{order_number} ({item_sku} - {size_code})"
                    if missing_entry not in missing_sizes:
                        missing_sizes.append(missing_entry)
                        track_missing_size_reference_multi(
                            df, order_column, sku_column, order_number, item_sku, missing_size_row_indices
                        )

            design_items = process_personalised_designs(
                order_number,
                item_sku,
                duplicate_index,
                is_duplicate_order,
                gui.single_designs_folder,
                gui.double_designs_folder,
                gui.size_reference_df,
                gui.mm_to_pixel,
                gui.canvas_width_mm,
                gui.design_padding,
                getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set,
                canvas_height_mm=gui.canvas_height_mm,
                force_single=is_customise_yes(customise),
            )

            if not design_items:
                missing_orders.append(order_number)
                continue

            for design_data in design_items:
                design_type = design_data.get("design_type", "Unknown")
                log_size_determination(create_design_log_entry(order_number, design_type, design_data, item_sku))
                if design_data.get("size_info"):
                    log_stats["size_reference_used"] += 1
                else:
                    log_stats["original_dimensions_used"] += 1
                log_stats["total_designs"] += 1
                if design_type == "single":
                    log_stats["single_designs"] += 1
                elif design_type == "double":
                    log_stats["double_designs"] += 1

                designs.append(
                    {
                        "sku": design_data["sku"],
                        "image": design_data["image"],
                        "path": design_data["path"],
                        "width": design_data["width"],
                        "height": design_data["height"],
                        "width_mm": design_data["width_mm"],
                        "height_mm": design_data["height_mm"],
                        "size_code": design_data.get("size_code"),
                        "design_type": design_type,
                    }
                )

        if not designs:
            finish_size_determination_log(log_stats)
            return [], [], missing_size_row_indices

        if missing_orders:
            missing_list = format_missing_items_list(missing_orders, 10)
            messagebox.showwarning(
                "Warning",
                f"Could not find designs for {len(missing_orders)} Order Numbers in {os.path.basename(file_path) if file_path else 'file'}:\n{missing_list}",
            )

        handle_missing_sizes_warning(
            missing_sizes, missing_size_row_indices, df, file_path, gui, save_rows=False
        )
        finish_size_determination_log(log_stats)
        batches = pack_designs(
            designs, gui.canvas_width_mm, gui.canvas_height_mm, gui.mm_to_pixel, gui.design_padding
        )
        all_designs = []
        for batch in batches:
            all_designs.extend(batch)
        return all_designs, batches, missing_size_row_indices

    except Exception as e:
        try:
            finish_size_determination_log()
        except Exception:
            pass
        import traceback
        traceback.print_exc()
        error_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        content = "Error Processing Personalised File\n"
        content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"File: {os.path.basename(file_path) if file_path else 'Unknown file'}\n"
        content += f"Error: {e}\n"
        content += f"\n{'='*80}\n"
        content += f"Full Traceback:\n{error_traceback}\n"
        save_error_to_file(content, "error")
        return [], [], []
