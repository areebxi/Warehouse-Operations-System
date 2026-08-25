from typing import Optional

from scripts.pipeline_generate_packing_list_pdf.core_helpers import is_plain_order_sku_impl
from scripts.pipeline_generate_packing_list_pdf.draw_page_date_header import (
    draw_page_date_header_impl,
)


def prepare_draw_page_state_impl(
    c,
    row_series,
    order_number_counts,
    process_totals,
    *,
    top_h_pt,
    left_x,
    left_w,
    image_x,
    image_area_w_pt,
    scale_w,
    header_pad_pt,
    header_top_pad_pt,
    font_size_top,
    font_size_item_name,
    font_size_left_label,
    recipient_h_pt,
    left_w_pt,
    box_pad_x_pt,
    box_pad_y_pt,
    left_four_top_pt,
    left_gender_cell_h_pt,
    left_size_top_pt,
    left_colour_top_pt,
    left_item_qty_top_pt,
    left_other_cell_h_pt,
    content_h_pt,
    s2_y_pt,
    default_position_code,
    image_area_x_pt,
    col_w_pt,
    b0_y_pt,
    b1_y_pt,
    banner_h_pt,
    font_size_position,
    white,
    s1_y_pt,
    square_s_pt,
    font_size_banner,
    black,
    red,
    logo_customise_dir,
    logo_custom_stem_map,
    position_code_to_draw,
    apparel_image_dir,
    apparel_stem_map,
    safe_str,
    pt_h,
    rl_y,
    draw_blocks,
    draw_page_header_left,
    draw_left_bottom_item_image,
    resolve_custom_logo_context,
    draw_position_banners,
    draw_apparel_square,
    rect_at,
    draw_text_in_box,
    draw_text_in_padded_box,
    draw_recipient_name_in_box,
    draw_rect,
    get_field_value,
    parse_process_and_item,
    pt_w,
    prepare_image_from_url,
    image_reader_cls,
    logo_design_tokens,
    find_image_custom_exact,
    find_image_custom_logo,
    find_image_custom_fbpi,
    position_tokens,
    find_image,
    prepare_image,
    pdf_asset_log=None,
    pdf_page_index=0,
    dispatch_date_label: Optional[str] = None,
    dispatch_day_name: Optional[str] = None,
):
    top_h = pt_h(top_h_pt)
    top_y = rl_y(top_h_pt)
    draw_blocks(c)
    if dispatch_date_label and dispatch_day_name:
        draw_page_date_header_impl(c, dispatch_date_label, dispatch_day_name)
    item_sku_raw = safe_str(row_series.get("Item SKU", ""))
    is_plain_order = is_plain_order_sku_impl(item_sku_raw)

    draw_page_header_left(
        c, row_series, order_number_counts, process_totals, top_y=top_y, top_h=top_h, left_x=left_x, left_w=left_w, image_x=image_x, image_area_w_pt=image_area_w_pt, scale_w=scale_w, header_pad_pt=header_pad_pt, header_top_pad_pt=header_top_pad_pt, font_size_top=font_size_top, font_size_item_name=font_size_item_name, recipient_h_pt=recipient_h_pt, left_w_pt=left_w_pt, top_h_pt=top_h_pt, box_pad_x_pt=box_pad_x_pt, box_pad_y_pt=box_pad_y_pt, left_four_top_pt=left_four_top_pt, left_gender_cell_h_pt=left_gender_cell_h_pt, left_size_top_pt=left_size_top_pt, left_colour_top_pt=left_colour_top_pt, left_item_qty_top_pt=left_item_qty_top_pt, left_other_cell_h_pt=left_other_cell_h_pt, font_size_left_label=font_size_left_label, black=black, red=red, draw_text_in_padded_box=draw_text_in_padded_box, draw_text_in_box=draw_text_in_box, draw_recipient_name_in_box=draw_recipient_name_in_box, draw_rect=draw_rect, rect_at=rect_at, get_field_value=get_field_value, safe_str=safe_str, parse_process_and_item=parse_process_and_item, pt_w=pt_w, pt_h=pt_h, rl_y=rl_y
    )

    draw_left_bottom_item_image(
        c,
        row_series,
        is_plain_order=is_plain_order,
        content_h_pt=content_h_pt,
        s2_y_pt=s2_y_pt,
        left_w_pt=left_w_pt,
        rect_at=rect_at,
        safe_str=safe_str,
        prepare_image_from_url=prepare_image_from_url,
        image_reader_cls=image_reader_cls,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
    )

    is_customised, is_scoped_custom_merge, base_custom_path, fbpi_slots = resolve_custom_logo_context(
        row_series, order_number_counts, is_plain_order=is_plain_order, logo_customise_dir=logo_customise_dir, logo_custom_stem_map=logo_custom_stem_map, safe_str=safe_str, logo_design_tokens=logo_design_tokens, find_image_custom_exact=find_image_custom_exact, find_image_custom_logo=find_image_custom_logo, find_image_custom_fbpi=find_image_custom_fbpi
    )

    position_has_slash = draw_position_banners(
        c, row_series, is_customised=is_customised, fbpi_slots=fbpi_slots, position_code_to_draw=position_code_to_draw, default_position_code=default_position_code, image_area_x_pt=image_area_x_pt, col_w_pt=col_w_pt, b0_y_pt=b0_y_pt, b1_y_pt=b1_y_pt, banner_h_pt=banner_h_pt, font_size_position=font_size_position, white=white, rect_at=rect_at, draw_text_in_box=draw_text_in_box, safe_str=safe_str, position_tokens=position_tokens, pt_h=pt_h
    )

    ax, ay, aw, ah, had_missing_apparel_local = draw_apparel_square(
        c, row_series, order_number_counts, is_plain_order=is_plain_order, image_area_x_pt=image_area_x_pt, s1_y_pt=s1_y_pt, col_w_pt=col_w_pt, square_s_pt=square_s_pt, font_size_banner=font_size_banner, black=black, red=red, rect_at=rect_at, get_field_value=get_field_value, safe_str=safe_str, find_image=find_image, apparel_image_dir=apparel_image_dir, apparel_stem_map=apparel_stem_map, prepare_image=prepare_image, draw_text_in_box=draw_text_in_box, image_reader_cls=image_reader_cls, pdf_asset_log=pdf_asset_log, pdf_page_index=pdf_page_index
    )

    return (
        is_plain_order,
        is_scoped_custom_merge,
        base_custom_path,
        fbpi_slots,
        position_has_slash,
        ax,
        ay,
        aw,
        ah,
        had_missing_apparel_local,
    )
