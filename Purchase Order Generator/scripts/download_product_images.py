"""Download product/brand images from BTC Product Data — stable façade."""

from __future__ import annotations

import app_paths  # noqa: F401
from app_paths import asset_path, data_path
from run_script_gui_settings import required_product_images_dir

DEFAULT_BTC_PRODUCT_DATA = data_path("BTC_Product_Data.csv")
BRAND_IMAGE_DIR = asset_path("brand_logos")


def main() -> int:
    from download_product_images_main import run_main

    product_dir = required_product_images_dir()
    return run_main(
        default_btc=DEFAULT_BTC_PRODUCT_DATA,
        product_dir=product_dir,
        brand_dir=BRAND_IMAGE_DIR,
    )


if __name__ == "__main__":
    raise SystemExit(main())
