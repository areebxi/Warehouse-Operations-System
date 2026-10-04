"""Customise logo filename suffix labels after logo sections are drawn."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

from pipeline_generate_packing_list_pdf.draw_page_logo_suffix_labels_step import (
    run_logo_filename_suffix_label_step_impl,
)


def maybe_run_customise_suffix_labels(
    c,
    row_series,
    *,
    is_plain_order: bool,
    position_has_slash: bool,
    fbpi_slots,
    base_custom_path,
    is_scoped_custom_merge: bool,
    apparel_image_dir: Optional[Path],
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_customise_dir: Optional[Path],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    logo_normal_dir: Optional[Path],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    order_number_counts: dict,
    pdf_asset_log: Optional[Callable[[str], None]],
    pdf_page_index: int,
    **S,
) -> None:
    from pipeline_generate_packing_list_pdf.back_print_hint import has_fbpi_side_files

    safe_str = S["safe_str"]
    get_field_value = S["get_field_value"]
    find_image = S["find_image"]
    logo_image_for_slot = S["logo_image_for_slot"]
    if (
        is_plain_order
        or position_has_slash
        or (
            safe_str(row_series.get("Customise", "")).lower() != "yes"
            and not has_fbpi_side_files(fbpi_slots)
        )
    ):
        return

    resolved_apparel_path: Optional[Path] = None
    apparel_text = get_field_value(row_series, "Apparel Image", order_number_counts)
    if apparel_image_dir is not None or apparel_stem_map is not None:
        for name in (apparel_text, safe_str(row_series.get("Picture Name", ""))):
            if not name:
                continue
            candidate = find_image(apparel_image_dir, name, apparel_stem_map, recursive=False)
            if candidate is not None:
                resolved_apparel_path = candidate
                break

    def _resolved_logo_path_for_suffix_label(slot_index: int) -> Optional[Path]:
        return logo_image_for_slot(
            slot_index,
            row_series,
            fbpi_slots=fbpi_slots,
            base_custom_path=base_custom_path,
            is_scoped_custom_merge=is_scoped_custom_merge,
            logo_customise_dir=logo_customise_dir,
            logo_custom_stem_map=logo_custom_stem_map,
            logo_normal_dir=logo_normal_dir,
            logo_normal_stem_map=logo_normal_stem_map,
            safe_str=safe_str,
            logo_design_tokens=S["logo_design_tokens"],
            find_image_custom_exact=S["find_image_custom_exact"],
            find_image_custom_logo=S["find_image_custom_logo"],
            find_image_normal_logo=S["find_image_normal_logo"],
        )

    run_logo_filename_suffix_label_step_impl(
        c,
        row_series,
        is_plain_order=is_plain_order,
        image_area_x_pt=S["image_area_x_pt"],
        col_w_pt=S["col_w_pt"],
        b0_y_pt=S["b0_y_pt"],
        b1_y_pt=S["b1_y_pt"],
        banner_h_pt=S["banner_h_pt"],
        font_size_position=S["font_size_position"],
        white=S["white"],
        black=S["black"],
        safe_str=safe_str,
        rect_at=S["rect_at"],
        draw_text_in_box=S["draw_text_in_box"],
        draw_rect=S["draw_rect"],
        pt_h=S["pt_h"],
        resolved_logo_path_for_slot=_resolved_logo_path_for_suffix_label,
        logo_design_tokens=S["logo_design_tokens"],
        fbpi_slots=fbpi_slots,
        resolved_apparel_path=resolved_apparel_path,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
    )
