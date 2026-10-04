"""Load design images for personalised GUI processing."""
from __future__ import annotations

from src.core.design_processor import process_personalised_designs
from src.system.logging.utils import log_size_determination
from gui_helpers.common.gui_background import run_keeping_ui_alive
from gui_helpers.common.gui_progress import update_progress
from .gui_processing_helpers import (
    create_design_log_entry,
    is_customise_yes,
    is_plainlg_sku,
    track_missing_size_reference_multi,
)


def load_personalised_designs(
    gui,
    *,
    df,
    order_column,
    sku_column,
    order_numbers,
    item_skus,
    customise_vals,
    order_total_counts,
    show_progress,
    total_orders,
    missing_sizes,
    missing_size_row_indices,
    missing_orders,
    log_stats,
    designs,
) -> None:
    order_occurrences = {}
    if show_progress:
        update_progress(gui, 0, f"Loading designs: 0/{total_orders}")

    for idx, (order_number, item_sku, customise) in enumerate(
        zip(order_numbers, item_skus, customise_vals)
    ):
        if is_plainlg_sku(item_sku):
            continue
        if show_progress:
            progress = (idx / total_orders) * 50
            update_progress(gui, progress, f"Loading designs: {idx + 1}/{total_orders}")

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

        design_items = run_keeping_ui_alive(
            gui,
            process_personalised_designs,
            order_number,
            item_sku,
            duplicate_index,
            is_duplicate_order,
            gui.single_designs_folder,
            gui.double_designs_folder,
            gui.mm_to_pixel,
            gui.canvas_width_mm,
            gui.design_padding,
            getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set,
            canvas_height_mm=gui.canvas_height_mm,
            force_single=is_customise_yes(customise),
            cl_csv_path=getattr(gui, "cl_csv_path", None),
        )

        if not design_items:
            missing_orders.append(order_number)
            continue

        for design_data in design_items:
            design_type = design_data.get("design_type", "Unknown")
            log_size_determination(
                create_design_log_entry(order_number, design_type, design_data, item_sku)
            )
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
