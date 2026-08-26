"""Page geometry, scales, and layout constants for packing list PDFs.

Values match the historical definitions in generate_packing_list_pdf.py.
"""

from __future__ import annotations

from reportlab.lib.pagesizes import A4, landscape

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
MARGIN_LR = 20
MARGIN_TOP = 24
MARGIN_BOTTOM = 22
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LR * 2
CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
# Layout proportions (pt) – content ~848 wide, ~548.6 tall
CONTENT_H_PT = 548.6
SCALE_W = CONTENT_WIDTH / 848.0
SCALE_H = CONTENT_HEIGHT / CONTENT_H_PT


def pt_w(pt: float) -> float:
    return pt * SCALE_W


def pt_h(pt: float) -> float:
    return pt * SCALE_H


def rl_y(y_pt_from_top: float) -> float:
    """Convert y from top of content (pt) to reportlab y (from bottom)."""
    return PAGE_HEIGHT - MARGIN_TOP - y_pt_from_top * SCALE_H


# Top header height (pt)
TOP_H_PT = 55.8

# Left area: Items, Recipient, Gender, Size, Colour, Item Qty, Item Image URL image
LEFT_W_PT = 182
LEFT_X = MARGIN_LR
LEFT_W = pt_w(LEFT_W_PT)

# Recipient block height (pt) – increased for better readability
RECIPIENT_H_PT = 80.4  # previously 60.4

# Gender Apparel is taller than Size / Colour / Item Quantity; stack still ends at LEFT_FOUR_BOTTOM_PT.
LEFT_FOUR_TOP_PT = TOP_H_PT + RECIPIENT_H_PT  # 55.8 + 80.4 = 136.2
LEFT_FOUR_BOTTOM_PT = 322.9  # bottom of Item Qty cell (just above Picture Name / S2_Y_PT)
LEFT_FOUR_TOTAL_H_PT = LEFT_FOUR_BOTTOM_PT - LEFT_FOUR_TOP_PT
# Gender row height (pt); remainder split equally among Size, Colour, Item Quantity.
LEFT_GENDER_CELL_H_PT = 80
LEFT_OTHER_CELL_H_PT = (LEFT_FOUR_TOTAL_H_PT - LEFT_GENDER_CELL_H_PT) / 3
LEFT_SIZE_TOP_PT = LEFT_FOUR_TOP_PT + LEFT_GENDER_CELL_H_PT
LEFT_COLOUR_TOP_PT = LEFT_SIZE_TOP_PT + LEFT_OTHER_CELL_H_PT
LEFT_ITEM_QTY_TOP_PT = LEFT_COLOUR_TOP_PT + LEFT_OTHER_CELL_H_PT

# Right image area: 3 equal sections, two banner rows + two square rows
IMAGE_AREA_X_PT = 182
IMAGE_AREA_W_PT = 848.0 - IMAGE_AREA_X_PT  # 666 pt
COL_W_PT = IMAGE_AREA_W_PT / 3  # 222 pt
BANNER_H_PT = 22.8
SQUARE_S_PT = COL_W_PT  # 222 pt – square fills section width

# Y positions from top of content (pt)
B0_Y_PT = TOP_H_PT
S1_Y_PT = B0_Y_PT + BANNER_H_PT
B1_Y_PT = S1_Y_PT + SQUARE_S_PT
S2_Y_PT = B1_Y_PT + BANNER_H_PT
# Second square row (Logo 3rd, 4th, 5th) extends to bottom of content so no gap
S2_SQUARE_H_PT = CONTENT_H_PT - S2_Y_PT

IMAGE_X = MARGIN_LR + pt_w(IMAGE_AREA_X_PT)
COL_W = pt_w(COL_W_PT)
BANNER_H = pt_h(BANNER_H_PT)
SQUARE_S = pt_w(SQUARE_S_PT)

# Colors (RGB 0-1)
BLACK = (0, 0, 0)
WHITE = (1, 1, 1)
GREY_FILL = (191 / 255, 191 / 255, 191 / 255)
RED = (0.75, 0, 0)

FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_SIZE = 15
FONT_SIZE_TOP = 17
FONT_SIZE_BANNER = 16
FONT_SIZE_POSITION = FONT_SIZE_BANNER - 5
FONT_SIZE_ITEM_NAME = FONT_SIZE - 3  # 12 pt (was 10 pt, +2 pt)
FONT_SIZE_LEFT_LABEL = FONT_SIZE + 6
DATE_HEADER_FONT_SIZE = 10
DATE_HEADER_TOP_OFFSET = 10

# Buyer note band in left-bottom product-image cell (empty note → no band)
NOTE_FROM_BUYER_PREFIX = "Note From Buyer: "
NOTE_FROM_BUYER_MAX_LINES = 6
NOTE_FROM_BUYER_MAX_H_PT = 80
NOTE_FROM_BUYER_FONT_SIZE = FONT_SIZE_POSITION  # 11 pt


OUTLINE_WIDTH = 0.5
HEADER_PAD_PT = 2  # padding around Order Number, Item SKU, Process and Item Number, Item Name
HEADER_TOP_PAD_PT = 1  # extra padding at top for those header fields

# Generic inner padding for text inside boxes (in layout pt, before scaling)
BOX_PAD_X_PT = 3
BOX_PAD_Y_PT = 2
