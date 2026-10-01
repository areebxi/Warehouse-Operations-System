import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)
from pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)
from pipeline_generate_packing_list_pdf.draw_page_overlays_impl import draw_logo_overlays_impl


