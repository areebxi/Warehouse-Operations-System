"""Download product/brand images from BTC Product Data — stable façade."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests

import app_paths  # noqa: F401
from app_paths import asset_path, data_path
from download_product_images_jobs import (
    database_filenames,
    download_one,
    filename_from_url,
    iter_download_jobs,
    load_btc_product_data,
    pick_product_url,
)

DEFAULT_BTC_PRODUCT_DATA = data_path("BTC_Product_Data.csv")
PRODUCT_IMAGE_DIR = asset_path("product_images")
BRAND_IMAGE_DIR = asset_path("brand_logos")


def main() -> int:
    from download_product_images_main import run_main

    return run_main(
        default_btc=DEFAULT_BTC_PRODUCT_DATA,
        product_dir=PRODUCT_IMAGE_DIR,
        brand_dir=BRAND_IMAGE_DIR,
    )


if __name__ == "__main__":
    raise SystemExit(main())
