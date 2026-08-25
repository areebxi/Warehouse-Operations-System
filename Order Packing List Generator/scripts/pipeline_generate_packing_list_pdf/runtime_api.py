from functools import partial
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
from reportlab.lib.utils import ImageReader

from scripts.pipeline_generate_packing_list_pdf.core_helpers import (
    get_field_value_impl,
    logo_design_tokens_impl,
    normalize_label_impl,
    normalize_lower_impl,
    parse_process_and_item_impl,
    position_tokens_impl,
    safe_str_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    draw_apparel_square_impl,
    draw_logo_square_rows_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_banners import (
    draw_position_banners_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_bindings import (
    build_draw_page_static_args_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_custom_logo_context import (
    resolve_custom_logo_context_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_header_left import (
    draw_page_header_left_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_impl import draw_page_impl
from scripts.pipeline_generate_packing_list_pdf.draw_page_left_bottom import (
    draw_left_bottom_item_image_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_logo_lookup import (
    logo_image_for_slot_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_overlays import (
    draw_logo_overlays_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_shapes import (
    draw_blocks_impl,
    draw_rect_impl,
    rect_at_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_text import (
    draw_recipient_name_in_box_impl,
    draw_text_in_box_impl,
    draw_text_in_padded_box_impl,
)
from scripts.pipeline_generate_packing_list_pdf.image_prepare_runtime import (
    prepare_image_from_url_runtime_impl,
    prepare_image_runtime_impl,
)
from scripts.pipeline_generate_packing_list_pdf.images import (
    build_image_stem_map_impl,
    find_image_custom_exact_impl,
    find_image_custom_fbpi_impl,
    find_image_custom_logo_impl,
    find_image_impl,
    find_image_normal_logo_impl,
)
from scripts.pipeline_generate_packing_list_pdf.pdf_page_layout import PAGE_HEIGHT, PAGE_WIDTH
from scripts.pipeline_generate_packing_list_pdf.position_draw_mapping import (
    find_pqr_columns_by_header_impl,
    load_position_code_to_draw_impl,
    lookup_draw_for_position_code,
)
from scripts.pipeline_generate_packing_list_pdf.reporting import (
    build_order_counts_impl,
    build_process_totals_impl,
    collect_image_match_details_impl,
    count_image_lookup_stats_impl,
    format_image_match_log_impl,
    format_missing_report_impl,
)
from scripts.pipeline_generate_packing_list_pdf.runtime_config import (
    DEFAULT_POSITION_CODE,
    IMAGE_CACHE,
    IMAGE_DPI,
    MAX_PAGES_PER_PDF,
    PROCESS_INFO_SHEET,
    URL_IMAGE_CACHE,
    URL_IMAGE_MAX_BYTES,
    URL_IMAGE_TIMEOUT_SEC,
)
from scripts.pipeline_generate_packing_list_pdf.service import (
    csv_to_pdf_impl,
    render_one_pdf_impl,
)

try:
    from PIL import Image  # type: ignore[import]
    # Allow very large source files so prepare_image can downscale before PDF draw.
    try:
        Image.MAX_IMAGE_PIXELS = None  # type: ignore[attr-defined]
    except Exception:
        pass
except Exception:
    Image = None  # type: ignore[assignment]


_PROCESS_ITEM_RE = re.compile(r"^Process\s+(\S+)\s+Item-(\d+)")

_safe_str = safe_str_impl
_normalize_label = normalize_label_impl
_normalize_lower = normalize_lower_impl
_logo_design_tokens = partial(logo_design_tokens_impl, safe_str=_safe_str)
_position_tokens = partial(position_tokens_impl, safe_str=_safe_str)
_parse_process_and_item = partial(parse_process_and_item_impl, safe_str=_safe_str, process_item_re=_PROCESS_ITEM_RE)
_get_field_value = partial(get_field_value_impl, safe_str=_safe_str, logo_design_tokens=_logo_design_tokens)

build_image_stem_map = build_image_stem_map_impl
load_position_code_to_draw = partial(
    load_position_code_to_draw_impl,
    process_info_sheet=PROCESS_INFO_SHEET,
    normalize_label=_normalize_label,
    find_pqr_columns_by_header=find_pqr_columns_by_header_impl,
)

_prepare_image = partial(
    prepare_image_runtime_impl,
    image_dpi=IMAGE_DPI,
    image_cache=IMAGE_CACHE,
    image_module=Image,
)
_prepare_image_from_url = partial(
    prepare_image_from_url_runtime_impl,
    image_dpi=IMAGE_DPI,
    url_image_cache=URL_IMAGE_CACHE,
    image_module=Image,
    timeout_sec=URL_IMAGE_TIMEOUT_SEC,
    max_bytes=URL_IMAGE_MAX_BYTES,
)

_DRAW_PAGE_STATIC_ARGS = build_draw_page_static_args_impl(
    default_position_code=DEFAULT_POSITION_CODE,
    image_reader_cls=ImageReader,
    draw_blocks=draw_blocks_impl,
    draw_page_header_left=draw_page_header_left_impl,
    draw_left_bottom_item_image=draw_left_bottom_item_image_impl,
    resolve_custom_logo_context=resolve_custom_logo_context_impl,
    draw_position_banners=draw_position_banners_impl,
    draw_apparel_square=draw_apparel_square_impl,
    logo_image_for_slot=logo_image_for_slot_impl,
    draw_logo_overlays=draw_logo_overlays_impl,
    draw_logo_square_rows=draw_logo_square_rows_impl,
    safe_str=_safe_str,
    logo_design_tokens=_logo_design_tokens,
    normalize_lower=_normalize_lower,
    find_image_custom_exact=find_image_custom_exact_impl,
    find_image_custom_logo=find_image_custom_logo_impl,
    find_image_normal_logo=find_image_normal_logo_impl,
    find_image_custom_fbpi=find_image_custom_fbpi_impl,
    find_image=find_image_impl,
    prepare_image_from_url=_prepare_image_from_url,
    prepare_image=_prepare_image,
    rect_at=rect_at_impl,
    draw_text_in_box=draw_text_in_box_impl,
    draw_text_in_padded_box=draw_text_in_padded_box_impl,
    draw_recipient_name_in_box=draw_recipient_name_in_box_impl,
    draw_rect=draw_rect_impl,
    get_field_value=_get_field_value,
    parse_process_and_item=_parse_process_and_item,
    position_tokens=_position_tokens,
)


def draw_page(
    c,
    row_series,
    order_number_counts: dict,
    process_totals: Optional[Dict[str, int]] = None,
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
) -> tuple[bool, bool]:
    return draw_page_impl(
        c,
        row_series,
        order_number_counts,
        process_totals,
        apparel_image_dir=apparel_image_dir,
        logo_customise_dir=logo_customise_dir,
        logo_normal_dir=logo_normal_dir,
        apparel_stem_map=apparel_stem_map,
        logo_custom_stem_map=logo_custom_stem_map,
        logo_normal_stem_map=logo_normal_stem_map,
        position_code_to_draw=position_code_to_draw,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
        dispatch_date_label=dispatch_date_label,
        dispatch_day_name=dispatch_day_name,
        **_DRAW_PAGE_STATIC_ARGS,
    )


build_order_counts = partial(build_order_counts_impl, safe_str=_safe_str)
build_process_totals = partial(build_process_totals_impl, parse_process_and_item=_parse_process_and_item)
collect_image_match_details = partial(
    collect_image_match_details_impl,
    safe_str=_safe_str,
    logo_design_tokens=_logo_design_tokens,
    find_image=find_image_impl,
    find_image_normal_logo=find_image_normal_logo_impl,
    resolve_custom_logo_context=resolve_custom_logo_context_impl,
    logo_image_for_slot=logo_image_for_slot_impl,
    find_image_custom_exact=find_image_custom_exact_impl,
    find_image_custom_logo=find_image_custom_logo_impl,
    find_image_custom_fbpi=find_image_custom_fbpi_impl,
)
count_image_lookup_stats = partial(
    count_image_lookup_stats_impl,
    safe_str=_safe_str,
    logo_design_tokens=_logo_design_tokens,
    find_image=find_image_impl,
    find_image_normal_logo=find_image_normal_logo_impl,
    resolve_custom_logo_context=resolve_custom_logo_context_impl,
    logo_image_for_slot=logo_image_for_slot_impl,
    find_image_custom_exact=find_image_custom_exact_impl,
    find_image_custom_logo=find_image_custom_logo_impl,
    find_image_custom_fbpi=find_image_custom_fbpi_impl,
)
format_image_match_log = format_image_match_log_impl
format_missing_report = format_missing_report_impl

_CSV_STATIC = {
    "page_width": PAGE_WIDTH,
    "page_height": PAGE_HEIGHT,
    "max_pages_per_pdf": MAX_PAGES_PER_PDF,
    "build_image_stem_map": build_image_stem_map,
    "build_order_counts": build_order_counts,
    "build_process_totals": build_process_totals,
    "draw_page": draw_page,
}


def csv_to_pdf(
    csv_path: Path,
    output_path: Path,
    apparel_image_dir: Optional[Path] = None,
    logo_customise_dir: Optional[Path] = None,
    logo_normal_dir: Optional[Path] = None,
    apparel_stem_map: Optional[Dict[str, Path]] = None,
    logo_custom_stem_map: Optional[Dict[str, Path]] = None,
    logo_normal_stem_map: Optional[Dict[str, Path]] = None,
    position_code_to_draw: Optional[Dict[str, str]] = None,
    show_process_item_count: bool = True,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    date_dd_mm_yyyy: Optional[str] = None,
) -> Tuple[int, List[Path], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    return csv_to_pdf_impl(
        csv_path,
        output_path,
        apparel_image_dir,
        logo_customise_dir,
        logo_normal_dir,
        apparel_stem_map,
        logo_custom_stem_map,
        logo_normal_stem_map,
        position_code_to_draw,
        show_process_item_count,
        pdf_asset_log,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        **_CSV_STATIC,
    )


render_one_pdf = partial(render_one_pdf_impl, csv_to_pdf=csv_to_pdf)
