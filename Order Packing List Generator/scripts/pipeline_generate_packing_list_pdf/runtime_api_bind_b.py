from pipeline_generate_packing_list_pdf.core_helpers import PROCESS_ITEM_RE as _PROCESS_ITEM_RE
from pipeline_generate_packing_list_pdf.runtime_api_bind_a import *

_safe_str = safe_str_impl
_normalize_label = normalize_label_impl
_normalize_lower = normalize_lower_impl
_logo_design_tokens = partial(logo_design_tokens_impl, safe_str=_safe_str)
_position_tokens = partial(position_tokens_impl, safe_str=_safe_str)
_parse_process_and_item = partial(
    parse_process_and_item_impl, safe_str=_safe_str, process_item_re=_PROCESS_ITEM_RE
)
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

render_one_pdf = partial(render_one_pdf_impl, csv_to_pdf=csv_to_pdf)
