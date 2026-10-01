"""PDF packing-slip layout constants and shared paths."""
from __future__ import annotations

from app_paths import APP_ROOT, asset_path, data_path, packs_database_path, product_database_path

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
