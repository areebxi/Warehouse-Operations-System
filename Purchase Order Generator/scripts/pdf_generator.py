"""
PDF Generator - Extracted from plain-orders cursor ai.py
This file contains only the PDF generation functionality for packing slips.
"""

import pandas as pd
from fpdf import FPDF
from pathlib import Path
from datetime import date

from app_paths import APP_ROOT, asset_path, data_path, packs_database_path, product_database_path, tag_output_dir
from pdf_generator_impl1 import PDF
from pdf_generator_impl2 import generate_packing_slips_for_tag
from pdf_generator_impl3 import generate_packing_slips, _load_btc_product_data_by_uid, _resolve_product_image_path, _load_colour_image_basenames_by_uid, _image_filename_from_url
from pdf_generator_impl4 import _load_pack_titles_map, _load_pack_names_map, _lookup_product_details, _safe_add_single_page, _read_btc_product_data_csv, _row_to_product_dict

# --- PDF Layout Constants ---
PAGE_WIDTH = 297
PAGE_HEIGHT = 210
MARGIN = 10
PRODUCT_IMG_X = MARGIN
PRODUCT_IMG_Y = 45
PRODUCT_IMG_W = 75
PRODUCT_IMG_H = 95.55
DETAILS_X_START = PRODUCT_IMG_X + PRODUCT_IMG_W + 10
BRAND_LOGO_W = 40
BRAND_LOGO_X = PAGE_WIDTH - MARGIN - BRAND_LOGO_W

# --- Column Names ---
COLUMN_NAMES = {
    # In orders.csv (PLAIN_ITEMS_CSV)
    "order_id": "Order",
    "sku": "Item SKU",
    "recipient": "Recipient",
    "quantity": "Quantity",
    "process": "Tag",
    "components": "Components",
    "component_colours": "Component Colours",

    # In Database.xlsx (PRODUCT_DATABASE_FILE)
    "product_code": "Product Code",
    "db_sku": "SKU",
    "brand": "Brand",
    "colour": "Colour",
    "size": "Size",
    "description": "Description",
    "package": "Package",
    "product_image_filename": "Product_Image_URL",
    "brand_image_filename": "Brand_Image_URL",
}

# --- File Paths ---
PLAIN_ITEMS_CSV = "packing_list_tag_30885_20250908_130713.csv"  # Example only (CLI mode)
PRODUCT_DATABASE_FILE = product_database_path()
BTC_PRODUCT_DATA_FILE = data_path("BTC_Product_Data.csv")
PACKS_DATABASE_FILE = packs_database_path()

SCRIPT_DIR = APP_ROOT
PRODUCT_IMAGE_FOLDER = asset_path("product_images")
BRAND_IMAGE_FOLDER = asset_path("brand_logos")

_COLOUR_IMAGE_BY_UID_CACHE: dict[str, str] | None = None

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
