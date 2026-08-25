from typing import Callable, Dict, Optional


def draw_page_header_left_impl(
    c,
    row_series,
    order_number_counts: dict,
    process_totals: Optional[Dict[str, int]],
    *,
    top_y: float,
    top_h: float,
    left_x: float,
    left_w: float,
    image_x: float,
    image_area_w_pt: float,
    scale_w: float,
    header_pad_pt: float,
    header_top_pad_pt: float,
    font_size_top: float,
    font_size_item_name: float,
    recipient_h_pt: float,
    left_w_pt: float,
    top_h_pt: float,
    box_pad_x_pt: float,
    box_pad_y_pt: float,
    left_four_top_pt: float,
    left_gender_cell_h_pt: float,
    left_size_top_pt: float,
    left_colour_top_pt: float,
    left_item_qty_top_pt: float,
    left_other_cell_h_pt: float,
    font_size_left_label: float,
    black,
    red,
    draw_text_in_padded_box: Callable[..., None],
    draw_text_in_box: Callable[..., None],
    draw_recipient_name_in_box: Callable[..., None],
    draw_rect: Callable[..., None],
    rect_at: Callable[..., tuple],
    get_field_value: Callable[..., str],
    safe_str: Callable[..., str],
    parse_process_and_item: Callable[..., tuple],
    pt_w: Callable[[float], float],
    pt_h: Callable[[float], float],
    rl_y: Callable[[float], float],
) -> None:
    items_val = get_field_value(row_series, "Items", order_number_counts)
    draw_text_in_padded_box(
        c,
        left_x,
        top_y + 0.5,
        left_w,
        top_h - 1,
        items_val,
        False,
        black,
        "center",
        font_size_top,
        wrap=True,
    )
    right_header_x = image_x
    right_header_w = image_area_w_pt * scale_w
    draw_text_in_box(c, right_header_x + pt_w(header_pad_pt), rl_y(20.4) + 0.5 + pt_h(header_pad_pt), right_header_w / 2 - 2 * pt_w(header_pad_pt), pt_h(20.4) - 0.5 - 2 * pt_h(header_pad_pt) - pt_h(header_top_pad_pt), get_field_value(row_series, "Order Number", order_number_counts), False, black, "left", font_size_top)
    draw_text_in_box(c, right_header_x + right_header_w / 2 + pt_w(header_pad_pt), rl_y(20.4) + 0.5 + pt_h(header_pad_pt), right_header_w / 2 - 2 * pt_w(header_pad_pt), pt_h(20.4) - 0.5 - 2 * pt_h(header_pad_pt) - pt_h(header_top_pad_pt), get_field_value(row_series, "Item SKU", order_number_counts), False, black, "right", font_size_top)
    process_header_text = get_field_value(row_series, "Process and Item Number", order_number_counts)
    raw_pin = safe_str(row_series.get("Process and Item Number"))
    if process_totals:
        process_id, item_index = parse_process_and_item(raw_pin)
        if process_id and item_index:
            total = process_totals.get(process_id, 0) or 1
            item_label = "Item" if total == 1 else "Items"
            if raw_pin:
                process_header_text = f"{raw_pin} ({total} {item_label})"
            else:
                process_header_text = f"Process {process_id} Item-{item_index} ({total} {item_label})"
    draw_text_in_box(c, right_header_x + pt_w(header_pad_pt), rl_y(40.8) + 0.5 + pt_h(header_pad_pt), right_header_w - 2 * pt_w(header_pad_pt), pt_h(20.4) - 0.5 - 2 * pt_h(header_pad_pt) - pt_h(header_top_pad_pt), process_header_text, False, black, "left", font_size_top)
    draw_text_in_box(c, right_header_x + pt_w(header_pad_pt), rl_y(55.8) + 0.5 + pt_h(header_pad_pt), right_header_w - 2 * pt_w(header_pad_pt), pt_h(15) - 0.5 - 2 * pt_h(header_pad_pt) - pt_h(header_top_pad_pt), get_field_value(row_series, "Item Name", order_number_counts), False, black, "left", font_size_item_name)

    base_order = safe_str(
        row_series.get("Order Number (Base)") or row_series.get("Order Number")
    )
    count = order_number_counts.get(base_order, 1)
    first_idx = order_number_counts.get(("__first__", base_order))
    is_first_page = count > 1 and (first_idx is None or row_series.name == first_idx)

    rx, ry, rw, rh = rect_at(0, top_h_pt, left_w_pt, recipient_h_pt)
    fill_color = red if (count > 1 and not is_first_page) else black
    draw_rect(c, rx, ry, rw, rh, fill_color)

    recipient_text = ""
    if count <= 1 or is_first_page:
        recipient_text = get_field_value(row_series, "Recipient Name", order_number_counts)

    pad_rx = rx + pt_w(box_pad_x_pt)
    pad_ry = ry + pt_h(box_pad_y_pt)
    pad_rw = rw - 2 * pt_w(box_pad_x_pt)
    pad_rh = rh - 2 * pt_h(box_pad_y_pt)
    draw_recipient_name_in_box(
        c,
        pad_rx,
        pad_ry,
        pad_rw,
        pad_rh,
        recipient_text,
        vertical_nudge=4,
    )

    gx, gy, gw, gh = rect_at(0, left_four_top_pt, left_w_pt, left_gender_cell_h_pt)
    draw_text_in_padded_box(
        c,
        gx,
        gy,
        gw,
        gh,
        get_field_value(row_series, "Gender Apparel", order_number_counts),
        False,
        black,
        "center",
        font_size=font_size_left_label,
        wrap=True,
    )

    sx, sy, sw, sh = rect_at(0, left_size_top_pt, left_w_pt, left_other_cell_h_pt)
    draw_text_in_padded_box(
        c,
        sx,
        sy,
        sw,
        sh,
        get_field_value(row_series, "Size", order_number_counts),
        True,
        red,
        "center",
        font_size=font_size_left_label,
        wrap=True,
    )

    cx, cy, cw, ch = rect_at(0, left_colour_top_pt, left_w_pt, left_other_cell_h_pt)
    draw_text_in_padded_box(
        c,
        cx,
        cy,
        cw,
        ch,
        get_field_value(row_series, "Colour", order_number_counts),
        False,
        black,
        "center",
        font_size=font_size_left_label,
        wrap=True,
    )

    ix, iy, iw, ih = rect_at(0, left_item_qty_top_pt, left_w_pt, left_other_cell_h_pt)
    draw_text_in_padded_box(
        c,
        ix,
        iy,
        iw,
        ih,
        get_field_value(row_series, "Item Quantity", order_number_counts),
        True,
        red,
        "center",
        font_size=font_size_left_label,
        wrap=True,
    )
