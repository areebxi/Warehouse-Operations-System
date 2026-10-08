"""Generate packing-slip PDF for one ShipStation tag CSV."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from app_paths import tag_output_dir
from pdf_btc_product import (
    _load_btc_product_data_by_uid,
    _load_pack_names_map,
    _load_pack_titles_map,
)
from pdf_constants import COLUMN_NAMES, MARGIN, PACKS_DATABASE_FILE, PRODUCT_DATABASE_FILE
from pdf_generate_item import render_slip_item
from pdf_page import PDF


def generate_packing_slips_for_tag(
    csv_filename,
    tag_id,
    output_path=None,
    *,
    plain_database_path=None,
    packs_database_path=None,
):
    """Generate PDF packing slips for a specific tag ID CSV file. Returns True if a PDF was saved."""
    print(f"\n[PDF] Starting PDF generation for tag {tag_id}...")
    plain_path = Path(plain_database_path) if plain_database_path else Path(PRODUCT_DATABASE_FILE)
    packs_path = Path(packs_database_path) if packs_database_path else Path(PACKS_DATABASE_FILE)

    try:
        orders_df = pd.read_csv(
            csv_filename,
            dtype={
                COLUMN_NAMES["sku"]: str,
                COLUMN_NAMES["process"]: str,
                COLUMN_NAMES["components"]: str,
                COLUMN_NAMES["component_colours"]: str,
            },
        )
        products_df = pd.read_excel(
            plain_path,
            dtype={COLUMN_NAMES["db_sku"]: str, COLUMN_NAMES["product_code"]: str},
        )
        pack_names_map = _load_pack_names_map(str(packs_path))
        pack_titles_map = _load_pack_titles_map(str(packs_path))
        export_by_uid = _load_btc_product_data_by_uid()
        try:
            from run_script import load_packs_database

            packs_components_map = load_packs_database(str(packs_path))
        except Exception:
            packs_components_map = {}

        products_df = products_df.drop_duplicates(subset=[COLUMN_NAMES["db_sku"]], keep="first")
        products_df = products_df.set_index(COLUMN_NAMES["db_sku"])
        print(f"[PDF] Loaded {len(orders_df)} order items and {len(products_df)} products.")
        if export_by_uid:
            print(f"[PDF] BTC Product Data fallback: {len(export_by_uid)} SKUs available.")
    except FileNotFoundError as e:
        print(f"\n[ERROR] FATAL: Required file not found. Please check paths.\n    Details: {e}")
        return False
    except KeyError as e:
        print(f"\n[ERROR] FATAL: A required column is missing from a file.\n    Column Name: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] FATAL: An unexpected error occurred during file loading: {e}")
        return False

    if orders_df.empty:
        print("[WARNING] No packing-slip rows in CSV — PDF not created.")
        return False

    saved_any = False
    for process_number, process_df in orders_df.groupby(COLUMN_NAMES["process"]):
        print(f"\n--- Processing Tag: {process_number} ---")
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=MARGIN)
        pages_before = pdf.page
        for order_id, items_in_order in process_df.groupby(COLUMN_NAMES["order_id"], sort=False):
            total_items_in_order = len(items_in_order)
            print(f"   Processing Order {order_id} ({total_items_in_order} item(s))...")
            for item_count, (_, item) in enumerate(items_in_order.iterrows(), 1):
                render_slip_item(
                    pdf,
                    item,
                    products_df=products_df,
                    export_by_uid=export_by_uid,
                    packs_components_map=packs_components_map,
                    pack_names_map=pack_names_map,
                    pack_titles_map=pack_titles_map,
                    item_count=item_count,
                    total_items_in_order=total_items_in_order,
                )

        if pdf.page <= pages_before:
            print(f"   [WARNING] No PDF pages generated for tag '{process_number}' — skipping save.")
            continue

        try:
            if output_path:
                output_filename = Path(output_path)
                output_filename.parent.mkdir(parents=True, exist_ok=True)
            else:
                pdf_output_folder = tag_output_dir("pdf_output")
                date_folder = pdf_output_folder / date.today().strftime("%Y-%m-%d")
                date_folder.mkdir(parents=True, exist_ok=True)
                from run_script import pdf_filename_for_tag

                output_filename = date_folder / pdf_filename_for_tag(tag_id)
            pdf.output(str(output_filename))
            if output_filename.exists() and output_filename.stat().st_size > 0:
                saved_any = True
                print(f"   Success! PDF for tag '{tag_id}' generated at: {output_filename.resolve()}")
            else:
                print(f"   [WARNING] PDF file missing or empty after save: {output_filename}")
        except Exception as e:
            print(
                f"\n   ERROR: Could not save the PDF for tag '{tag_id}'. "
                f"Is the file open elsewhere?\n   Reason: {e}"
            )

    print(f"\n[PDF] PDF generation for tag {tag_id} completed!")
    return saved_any
