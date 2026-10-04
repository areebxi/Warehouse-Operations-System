"""Apparel + logo draw façade for packing-list PDFs.

Re-exports the cohesive modules (logo rows/cell, apparel square, primitives).
The older apparel_and_logos_impl1/2/3 split left helpers across modules and
caused NameErrors (_pdf_asset_log_line, etc.) when those impls were live.
"""

from pipeline_generate_packing_list_pdf.draw_page_apparel_square import (
    draw_apparel_square_impl,
)
from pipeline_generate_packing_list_pdf.draw_page_back_layout import (
    _compute_back_print_layout,
)
from pipeline_generate_packing_list_pdf.draw_page_image_primitives import (
    _LOGO_FIELDS,
    _SLOT_LABELS,
    _draw_back_print_reference,
    _draw_prepared_image,
    _draw_red_margin,
    _pdf_asset_log_line,
)
from pipeline_generate_packing_list_pdf.draw_page_logo_cell import (
    _draw_logo_cell_image,
)
from pipeline_generate_packing_list_pdf.draw_page_logo_rows import (
    draw_logo_square_rows_impl,
)
