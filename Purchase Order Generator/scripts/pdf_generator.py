"""
PDF Generator — stable façade for packing-slip generation.
Logic lives in pdf_page / pdf_generate_* / pdf_btc_* helpers.
"""

from __future__ import annotations

from pdf_btc_images import (  # noqa: F401
    _image_filename_from_url,
    _load_colour_image_basenames_by_uid,
    _read_btc_product_data_csv,
    _resolve_product_image_path,
)
from pdf_btc_product import (  # noqa: F401
    _load_btc_product_data_by_uid,
    _load_pack_names_map,
    _load_pack_titles_map,
    _lookup_product_details,
    _row_to_product_dict,
)
from pdf_constants import (  # noqa: F401
    BRAND_IMAGE_FOLDER,
    BRAND_LOGO_W,
    BRAND_LOGO_X,
    BTC_PRODUCT_DATA_FILE,
    COLUMN_NAMES,
    DETAILS_X_START,
    MARGIN,
    PACKS_DATABASE_FILE,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    PLAIN_ITEMS_CSV,
    PRODUCT_DATABASE_FILE,
    PRODUCT_IMAGE_FOLDER,
    PRODUCT_IMG_H,
    PRODUCT_IMG_W,
    PRODUCT_IMG_X,
    PRODUCT_IMG_Y,
    SCRIPT_DIR,
)
from pdf_generate_cli import generate_packing_slips  # noqa: F401
from pdf_generate_helpers import _safe_add_single_page  # noqa: F401
from pdf_generate_tag import generate_packing_slips_for_tag  # noqa: F401
from pdf_page import PDF  # noqa: F401

__all__ = [
    "PDF",
    "generate_packing_slips",
    "generate_packing_slips_for_tag",
    "COLUMN_NAMES",
    "PLAIN_ITEMS_CSV",
    "PRODUCT_DATABASE_FILE",
    "PRODUCT_IMAGE_FOLDER",
    "BRAND_IMAGE_FOLDER",
]

if __name__ == "__main__":
    print("PDF Generator - Packing Slips")
    print("=" * 50)
    print("Make sure you have:")
    print(f"1. {PLAIN_ITEMS_CSV} - Orders data")
    print(f"2. {PRODUCT_DATABASE_FILE} - Product database")
    print(f"3. {PRODUCT_IMAGE_FOLDER} - Product images folder")
    print(f"4. {BRAND_IMAGE_FOLDER} - Brand logos folder")
    print()
    generate_packing_slips()
