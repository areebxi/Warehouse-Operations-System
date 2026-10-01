import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from pipeline_generate_packing_list_pdf.back_print_hint import (
    next_logo_slot_index,
    slot_is_back_print,
)
from pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos_impl1 import draw_logo_square_rows_impl, _draw_back_print_reference, _pdf_asset_log_line
from pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos_impl2 import _draw_logo_cell_image, draw_apparel_square_impl, _draw_red_margin
from pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos_impl3 import _compute_back_print_layout, _draw_prepared_image

_LOGO_FIELDS = (
    "Logo/Design Image (1st)",
    "Logo/Design Image (2nd)",
    "Logo/Design Image (3rd)",
    "Logo/Design Image (4th)",
    "Logo/Design Image (5th)",
)

_SLOT_LABELS = (
    "logo slot 1 (1st)",
    "logo slot 2 (2nd)",
    "logo slot 3 (3rd)",
    "logo slot 4 (4th)",
    "logo slot 5 (5th)",
)


