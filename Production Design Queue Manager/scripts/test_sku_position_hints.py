"""ponytail: 1-SP JPEG is a hint — PNG queued, JPEG never placed."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from src.core.design_processing_personalised import process_personalised_designs
from src.core.design_processing_single import process_single_designs
from src.core.sku_position_hints import (
    POSITION_HINT_EXTENSIONS,
    POSITION_HINT_MM,
    POSITION_HINT_TOKENS,
    flags_for_position_token,
    normalize_position_token,
    target_mm_for_position_token,
)
from src.io.file_handlers import (
    find_design_file_vba_logic,
    find_sku_position_variant_files,
    resolve_sku_position_hint,
)
from src.io.file_utilities import IMAGE_EXTENSIONS
from test_sku_position_hints_impl1 import test_legacy_pocket_sleeve_png_kids_65x80, test_duplicate_png_plus_p_jpeg_queues_png_only, test_normal_mode_ignores_jpeg_hints, _personalised, test_unique_order_png_size_reference, test_slash_in_sku_becomes_hyphen
from test_sku_position_hints_impl2 import test_unique_order_ignores_sku_jpeg_hint, test_apparel_size_s_in_sku_is_not_sleeve, test_kids_sku_filename_p_hint_is_80x100_not_65x80, test_first_token_wins_and_index_zero_stem, _entries, test_duplicate_png_plus_s1_jpeg, test_jpeg_only_falls_through_to_double, test_double_folder_sku_png_unchanged, test_token_tables, _png, _jpg, _near

ORDER = "204-6115657-9842723"
SKU = "189397LG-M-T-BLK-4XL-YES"
KIDS_SKU = "189397LG-K-T-BLK-M-YES"
APPAREL_S_SKU = "189397LG-M-T-BLK-S-YES"
FACTOR = 1.0


def main() -> None:
    test_token_tables()
    test_unique_order_png_size_reference()
    test_legacy_pocket_sleeve_png_kids_65x80()
    test_duplicate_png_plus_p_jpeg_queues_png_only()
    test_duplicate_png_plus_s1_jpeg()
    test_apparel_size_s_in_sku_is_not_sleeve()
    test_jpeg_only_falls_through_to_double()
    test_double_folder_sku_png_unchanged()
    test_normal_mode_ignores_jpeg_hints()
    test_kids_sku_filename_p_hint_is_80x100_not_65x80()
    test_first_token_wins_and_index_zero_stem()
    test_slash_in_sku_becomes_hyphen()
    test_unique_order_ignores_sku_jpeg_hint()
    print("sku_position_hints ok")


if __name__ == "__main__":
    main()
