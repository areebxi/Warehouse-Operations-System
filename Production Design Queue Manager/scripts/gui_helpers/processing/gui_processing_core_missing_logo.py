"""Missing-logo core folder processing flow."""

import os
from datetime import datetime
from src.core.canvas_arranger import pack_designs
from src.core.design_folder_routing import find_designs_for_dtf_row
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
    is_plainlg_sku,
    track_missing_size_reference_multi,
)


def process_missing_logo_file_for_folder(gui, df, order_column, sku_column, file_path):
    """Process a missing-logo DTF Des file for folder processing."""
    try:
        gui.is_personalised = True
        start_size_determination_log(file_path, "missing_logo")
        log_stats = {
            "total_designs": 0,
            "personalised_found": 0,
            "all_in_one_found": 0,
            "size_reference_used": 0,
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

            if gui.sku_missing_cl_print_size(item_sku):
                missing_entry = f"{order_number} ({item_sku})"
                if missing_entry not in missing_sizes:
                    missing_sizes.append(missing_entry)
                    track_missing_size_reference_multi(
                        df, order_column, sku_column, order_number, item_sku, missing_size_row_indices
                    )

            design_items, source = find_designs_for_dtf_row(
                order_number=order_number,
                item_sku=item_sku,
                customise=customise,
                duplicate_index=duplicate_index,
                is_duplicate_order=is_duplicate_order,
                designs_folder=gui.designs_folder,
                single_designs_folder=gui.single_designs_folder,
                double_designs_folder=gui.double_designs_folder,
                mm_to_pixel=gui.mm_to_pixel,
                canvas_width_mm=gui.canvas_width_mm,
                canvas_height_mm=gui.canvas_height_mm,
                design_padding=gui.design_padding,
                print_size_overrides=getattr(gui, "print_size_overrides", None)
                or gui.pocket_design_ids_set,
                cl_csv_path=getattr(gui, "cl_csv_path", None),
            )
            found_in_personalised = source == "personalised"

            if not design_items:
                missing_orders.append(f"{order_number} (SKU: {item_sku})")
                continue

            if found_in_personalised:
                log_stats["personalised_found"] += len(design_items)
            else:
                log_stats["all_in_one_found"] += len(design_items)

            for design_data in design_items:
                design_type = design_data.get("design_type", "single")
                design_type_for_log = design_type if found_in_personalised else "Standard"
                log_size_determination(create_design_log_entry(order_number, design_type_for_log, design_data, item_sku))
                if design_type == "double":
                    log_stats["original_dimensions_used"] += 1
                elif design_data.get("size_info"):
                    log_stats["size_reference_used"] += 1
                else:
                    log_stats["original_dimensions_used"] += 1
                log_stats["total_designs"] += 1
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
            # warning kept lightweight for folder flow
            format_missing_items_list(missing_orders, 10)
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
        content = "Error Processing Missing Logo File\n"
        content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"File: {os.path.basename(file_path) if file_path else 'Unknown file'}\n"
        content += f"Error: {e}\n"
        content += f"\n{'='*80}\n"
        content += f"Full Traceback:\n{error_traceback}\n"
        save_error_to_file(content, "error")
        return [], [], []
