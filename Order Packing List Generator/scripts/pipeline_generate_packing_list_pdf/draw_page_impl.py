"""Orchestrate one packing-list PDF page draw."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional

from pipeline_generate_packing_list_pdf.draw_page_finalize import (
    finalize_logo_sections_impl,
)
from pipeline_generate_packing_list_pdf.draw_page_impl_suffix import (
    maybe_run_customise_suffix_labels,
)
from pipeline_generate_packing_list_pdf.draw_page_setup import (
    prepare_draw_page_state_impl,
)


def draw_page_impl(
    c,
    row_series,
    order_number_counts: dict,
    process_totals: Optional[Dict[str, int]],
    *,
    apparel_image_dir: Optional[Path] = None,
    logo_customise_dir: Optional[Path] = None,
    logo_normal_dir: Optional[Path] = None,
    apparel_stem_map: Optional[Dict[str, Path]] = None,
    logo_custom_stem_map: Optional[Dict[str, Path]] = None,
    logo_normal_stem_map: Optional[Dict[str, Path]] = None,
    position_code_to_draw: Optional[Dict[str, str]] = None,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
    dispatch_date_label: Optional[str] = None,
    dispatch_day_name: Optional[str] = None,
    **S,
) -> tuple[bool, bool]:
    (
        is_plain_order,
        is_scoped_custom_merge,
        base_custom_path,
        fbpi_slots,
        position_has_slash,
        ax,
        ay,
        aw,
        ah,
        had_missing_apparel,
    ) = prepare_draw_page_state_impl(
        c,
        row_series,
        order_number_counts,
        process_totals,
        apparel_image_dir=apparel_image_dir,
        logo_customise_dir=logo_customise_dir,
        logo_custom_stem_map=logo_custom_stem_map,
        logo_normal_dir=logo_normal_dir,
        logo_normal_stem_map=logo_normal_stem_map,
        apparel_stem_map=apparel_stem_map,
        position_code_to_draw=position_code_to_draw,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
        dispatch_date_label=dispatch_date_label,
        dispatch_day_name=dispatch_day_name,
        **S,
    )
    had_missing_logo = finalize_logo_sections_impl(
        c,
        row_series,
        order_number_counts,
        fbpi_slots=fbpi_slots,
        base_custom_path=base_custom_path,
        is_scoped_custom_merge=is_scoped_custom_merge,
        logo_customise_dir=logo_customise_dir,
        logo_custom_stem_map=logo_custom_stem_map,
        logo_normal_dir=logo_normal_dir,
        logo_normal_stem_map=logo_normal_stem_map,
        position_has_slash=position_has_slash,
        position_code_to_draw=position_code_to_draw,
        ax=ax,
        ay=ay,
        aw=aw,
        ah=ah,
        is_plain_order=is_plain_order,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
        **S,
    )
    maybe_run_customise_suffix_labels(
        c,
        row_series,
        is_plain_order=is_plain_order,
        position_has_slash=position_has_slash,
        fbpi_slots=fbpi_slots,
        base_custom_path=base_custom_path,
        is_scoped_custom_merge=is_scoped_custom_merge,
        apparel_image_dir=apparel_image_dir,
        apparel_stem_map=apparel_stem_map,
        logo_customise_dir=logo_customise_dir,
        logo_custom_stem_map=logo_custom_stem_map,
        logo_normal_dir=logo_normal_dir,
        logo_normal_stem_map=logo_normal_stem_map,
        order_number_counts=order_number_counts,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
        **S,
    )
    return bool(had_missing_logo), bool(had_missing_apparel)
