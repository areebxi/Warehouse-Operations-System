"""Filled rectangles and static page blocks for packing list PDFs."""

from __future__ import annotations

from reportlab.pdfgen import canvas

from . import pdf_page_layout as L


def draw_rect_impl(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill_rgb) -> None:
    c.setFillColorRGB(*fill_rgb)
    c.setStrokeColorRGB(*L.BLACK)
    c.setLineWidth(L.OUTLINE_WIDTH)
    c.rect(x, y, w, h, fill=1, stroke=0)


def rect_at_impl(x_pt, y_pt_from_top, w_pt, h_pt):
    """Return (x, rl_y_bottom, width, height) in page coords."""
    x = L.MARGIN_LR + x_pt * L.SCALE_W
    rl_y = L.rl_y(y_pt_from_top + h_pt)
    return (x, rl_y, w_pt * L.SCALE_W, h_pt * L.SCALE_H)


def draw_blocks_impl(c: canvas.Canvas) -> None:
    """Draw all filled areas: left area blocks and right image area (banners + squares)."""
    # Left: Gender (taller), Size, Colour, Item Quantity
    gx, gy, gw, gh = rect_at_impl(0, L.LEFT_FOUR_TOP_PT, L.LEFT_W_PT, L.LEFT_GENDER_CELL_H_PT)
    draw_rect_impl(c, gx, gy, gw, gh, L.WHITE)
    for y_top, h_pt in (
        (L.LEFT_SIZE_TOP_PT, L.LEFT_OTHER_CELL_H_PT),
        (L.LEFT_COLOUR_TOP_PT, L.LEFT_OTHER_CELL_H_PT),
        (L.LEFT_ITEM_QTY_TOP_PT, L.LEFT_OTHER_CELL_H_PT),
    ):
        rx, ry, rw, rh = rect_at_impl(0, y_top, L.LEFT_W_PT, h_pt)
        draw_rect_impl(c, rx, ry, rw, rh, L.WHITE)

    # Left bottom cell (below Item Qty, aligned with Logo 3rd row)
    pn_h = L.CONTENT_H_PT - L.S2_Y_PT
    pnx, pny, pnw, pnh = rect_at_impl(0, L.S2_Y_PT, L.LEFT_W_PT, pn_h)
    draw_rect_impl(c, pnx, pny, pnw, pnh, L.WHITE)

    # Right image area – banner row 0 (black blank, 1st, 2nd)
    for col in range(3):
        bx, by, bw, bh = rect_at_impl(
            L.IMAGE_AREA_X_PT + col * L.COL_W_PT, L.B0_Y_PT, L.COL_W_PT, L.BANNER_H_PT
        )
        draw_rect_impl(c, bx, by, bw, bh, L.BLACK)

    # Right – square row 1: Apparel (white), Logo 1st (grey), Logo 2nd (grey)
    ax, ay, aw, ah = rect_at_impl(L.IMAGE_AREA_X_PT, L.S1_Y_PT, L.COL_W_PT, L.SQUARE_S_PT)
    draw_rect_impl(c, ax, ay, aw, ah, L.WHITE)
    for col in range(1, 3):
        lx, ly, lw, lh = rect_at_impl(
            L.IMAGE_AREA_X_PT + col * L.COL_W_PT, L.S1_Y_PT, L.COL_W_PT, L.SQUARE_S_PT
        )
        draw_rect_impl(c, lx, ly, lw, lh, L.GREY_FILL)

    # Right – banner row 2 (3rd, 4th, 5th)
    for col in range(3):
        bx, by, bw, bh = rect_at_impl(
            L.IMAGE_AREA_X_PT + col * L.COL_W_PT, L.B1_Y_PT, L.COL_W_PT, L.BANNER_H_PT
        )
        draw_rect_impl(c, bx, by, bw, bh, L.BLACK)

    # Right – square row 3: Logo 3rd, 4th, 5th (grey), height fills to content bottom
    for col in range(3):
        lx, ly, lw, lh = rect_at_impl(
            L.IMAGE_AREA_X_PT + col * L.COL_W_PT, L.S2_Y_PT, L.COL_W_PT, L.S2_SQUARE_H_PT
        )
        draw_rect_impl(c, lx, ly, lw, lh, L.GREY_FILL)

    # Top header background (left + right) – white
    top_y = L.rl_y(L.TOP_H_PT)
    draw_rect_impl(c, L.LEFT_X, top_y, L.LEFT_W, L.pt_h(L.TOP_H_PT), L.WHITE)
    draw_rect_impl(
        c,
        L.IMAGE_X,
        top_y,
        L.IMAGE_AREA_W_PT * L.SCALE_W,
        L.pt_h(L.TOP_H_PT),
        L.WHITE,
    )
