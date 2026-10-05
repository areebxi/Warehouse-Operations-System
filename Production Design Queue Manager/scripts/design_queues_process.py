"""Headless Design Queues processing for SharedInbox watcher."""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from shared import paths as wh
from src.core.canvas_arranger import pack_designs
from src.core.canvas_creation import create_canvas_image, save_canvas_image
from src.core.design_folder_routing import find_designs_for_dtf_row
from src.core import DEFAULT_DESIGN_PADDING
from src.io import load_color_bar_from_app_dir, load_queue_data_sources
from gui_helpers.processing.gui_processing_helpers_folder import (
    auto_detect_customise_column,
    auto_detect_order_column,
    auto_detect_sku_column,
    load_dataframe_from_file,
)
from gui_helpers.processing.gui_processing_helpers_messages import is_plainlg_sku
from design_queues_inbox import APP_ROOT, LOG, WAREHOUSE_ROOT

def _build_ctx(settings: dict) -> SimpleNamespace:
    cl_csv_path, overrides, config_workbook_path = load_queue_data_sources(
        settings.get("cl_csv_path"),
        settings.get("config_workbook_path"),
        app_dir=str(APP_ROOT),
    )
    color_bar_image, color_bar_path = load_color_bar_from_app_dir(str(APP_ROOT))
    dpi = 300
    use_demo = bool(settings.get("use_demo_images"))
    if str(WAREHOUSE_ROOT) not in sys.path:
        sys.path.insert(0, str(WAREHOUSE_ROOT))
    from shared.demo_images import effective_design_dirs

    designs, single, double = effective_design_dirs(
        use_demo,
        settings.get("designs_folder"),
        settings.get("single_designs_folder"),
        settings.get("double_designs_folder"),
        from_path=WAREHOUSE_ROOT,
    )
    return SimpleNamespace(
        canvas_width_mm=570.0,
        canvas_height_mm=3000.0,
        dpi=dpi,
        mm_to_pixel=dpi / 25.4,
        design_padding=DEFAULT_DESIGN_PADDING,
        designs_folder=str(designs) if designs else None,
        single_designs_folder=str(single) if single else None,
        double_designs_folder=str(double) if double else None,
        use_demo_images=use_demo,
        cl_csv_path=cl_csv_path,
        config_workbook_path=config_workbook_path,
        print_size_overrides=overrides or {},
        pocket_design_ids_set=set((overrides or {}).keys()),
        color_bar_image=color_bar_image,
        color_bar_path=color_bar_path,
        is_personalised=True,
        dtf_queues_folder=settings.get("dtf_queues_folder") or None,
    )


def _output_stem(file_path: Path) -> str:
    # Match GUI naming: P50.png / P50_Part 1.png (overwrite on re-run).
    return re.sub(r"^DTF\s*Des-", "", file_path.stem, flags=re.IGNORECASE).strip()


def _save_batches(ctx: SimpleNamespace, batches: list, file_path: Path) -> list[Path]:
    out_dir = wh.queue_output_dir() / datetime.now().strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _output_stem(file_path)
    saved: list[Path] = []
    for i, batch in enumerate(batches, 1):
        part_text = f"PART {i}" if len(batches) > 1 else None
        canvas = create_canvas_image(
            batch,
            ctx.canvas_width_mm,
            ctx.canvas_height_mm,
            ctx.mm_to_pixel,
            ctx.dpi,
            color_bar_image=ctx.color_bar_image,
            des_text=stem,
            part_text=part_text,
        )
        if len(batches) > 1:
            out_path = out_dir / f"{stem}_Part {i}.png"
        else:
            out_path = out_dir / f"{stem}.png"
        save_canvas_image(canvas, str(out_path), ctx.dpi)
        saved.append(out_path)
    _copy_saved_to_dtf_queues(ctx, saved)
    return saved


def _copy_saved_to_dtf_queues(ctx: SimpleNamespace, saved: list[Path]) -> None:
    folder = getattr(ctx, "dtf_queues_folder", None)
    if not folder or not saved:
        return
    from src.io.dtf_queues_copy import copy_pngs_to_dtf_queues

    ok, msg = copy_pngs_to_dtf_queues([str(p) for p in saved], folder)
    if ok:
        LOG.info("DTF Queues copy: %s", msg.split("\n", 1)[0])
    else:
        LOG.warning("DTF Queues copy skipped/failed: %s", msg)


def process_design_queues_file_headless(ctx: SimpleNamespace, file_path: Path) -> list[Path]:
    df = load_dataframe_from_file(str(file_path))
    order_column = auto_detect_order_column(df)
    sku_column = auto_detect_sku_column(df)
    if not order_column or not sku_column:
        raise ValueError("DTF Des missing Order Number or Item SKU column")
    if not (
        ctx.single_designs_folder or ctx.double_designs_folder or ctx.designs_folder
    ):
        raise ValueError(
            "No design folders configured "
            "(enable Testing in Queue settings or set designs_folder / "
            "single_designs_folder / double_designs_folder)"
        )

    customise_col = auto_detect_customise_column(df)
    mask = df[order_column].notna() & df[sku_column].notna()
    order_numbers = df.loc[mask, order_column].tolist()
    item_skus = df.loc[mask, sku_column].tolist()
    customise_vals = (
        df.loc[mask, customise_col].tolist() if customise_col else [None] * len(order_numbers)
    )

    designs = []
    order_total_counts: dict = {}
    for order_number in order_numbers:
        order_total_counts[order_number] = order_total_counts.get(order_number, 0) + 1
    order_occurrences: dict = {}

    for order_number, item_sku, customise in zip(order_numbers, item_skus, customise_vals):
        if is_plainlg_sku(item_sku):
            continue
        order_occurrences[order_number] = order_occurrences.get(order_number, 0) + 1
        duplicate_index = order_occurrences[order_number] - 1
        is_duplicate_order = order_total_counts.get(order_number, 0) > 1
        design_items, _source = find_designs_for_dtf_row(
            order_number=order_number,
            item_sku=item_sku,
            customise=customise,
            duplicate_index=duplicate_index,
            is_duplicate_order=is_duplicate_order,
            designs_folder=ctx.designs_folder,
            single_designs_folder=ctx.single_designs_folder,
            double_designs_folder=ctx.double_designs_folder,
            mm_to_pixel=ctx.mm_to_pixel,
            canvas_width_mm=ctx.canvas_width_mm,
            canvas_height_mm=ctx.canvas_height_mm,
            design_padding=ctx.design_padding,
            print_size_overrides=ctx.print_size_overrides or ctx.pocket_design_ids_set,
            cl_csv_path=getattr(ctx, "cl_csv_path", None),
        )
        for design_data in design_items:
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
                    "design_type": design_data.get("design_type", "single"),
                }
            )

    if not designs:
        raise ValueError("No designs found for Design Queues auto-run")

    batches = pack_designs(
        designs,
        ctx.canvas_width_mm,
        ctx.canvas_height_mm,
        ctx.mm_to_pixel,
        ctx.design_padding,
    )
    return _save_batches(ctx, batches, file_path)
