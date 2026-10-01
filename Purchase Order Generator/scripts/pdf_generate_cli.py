"""CLI entry for generating packing slips from the example CSV."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from app_paths import tag_output_dir
from pdf_btc_product import _load_btc_product_data_by_uid, _lookup_product_details
from pdf_constants import COLUMN_NAMES, MARGIN, PLAIN_ITEMS_CSV, PRODUCT_DATABASE_FILE, SCRIPT_DIR
from pdf_page import PDF

def generate_packing_slips():
    """Main function to load data and generate PDFs based on Process Number."""
    print("\n🚀 Starting packing slip generation...")

    try:
        orders_df = pd.read_csv(PLAIN_ITEMS_CSV, dtype={COLUMN_NAMES['sku']: str, COLUMN_NAMES['process']: str})
        products_df = pd.read_excel(PRODUCT_DATABASE_FILE, dtype={COLUMN_NAMES['db_sku']: str, COLUMN_NAMES['product_code']: str})
        # Load Pack Names and Titles maps via openpyxl
        pack_names_map = _load_pack_names_map(PACKS_DATABASE_FILE)
        pack_titles_map = _load_pack_titles_map(PACKS_DATABASE_FILE)
        export_by_uid = _load_btc_product_data_by_uid()
        
        products_df = products_df.drop_duplicates(subset=[COLUMN_NAMES['db_sku']], keep='first')
        products_df = products_df.set_index(COLUMN_NAMES['db_sku'])
        
        print(f"✅ Loaded {len(orders_df)} order items and {len(products_df)} products.")
    except FileNotFoundError as e:
        print(f"\n❌ FATAL ERROR: Required file not found. Please check paths.\n    Details: {e}")
        return
    except KeyError as e:
        print(f"\n❌ FATAL ERROR: A required column is missing from a file.\n    Column Name: {e}")
        return
    except Exception as e:
        print(f"\n❌ FATAL ERROR: An unexpected error occurred during file loading: {e}")
        return
    
    orders_df = orders_df.sort_values(by=COLUMN_NAMES['process'])
    
    grouped_by_process = orders_df.groupby(COLUMN_NAMES['process'])

    for process_number, process_df in grouped_by_process:
        print(f"\n--- 🏭 Processing Group: {process_number} ---")
        
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=MARGIN)

        grouped_orders = process_df.groupby(COLUMN_NAMES['order_id'], sort=False)

        for order_id, items_in_order in grouped_orders:
            total_items_in_order = len(items_in_order)
            print(f"   📦 Processing Order {order_id} ({total_items_in_order} item(s))...")

            for item_count, (_, item) in enumerate(items_in_order.iterrows(), 1):
                sku = item.get(COLUMN_NAMES['sku'])
                print(f"     - Item {item_count}/{total_items_in_order}, SKU: {sku}")

                if not sku or pd.isna(sku):
                    continue

                product_details = _lookup_product_details(products_df, sku, export_by_uid)
                if not product_details:
                    print(f"     ⚠️ Warning: Product details not found in database for SKU '{sku}'.")
                
                normalized_pack = str(sku).split('-')[0] if sku and '-' in str(sku) else str(sku)
                pack_name_value = pack_names_map.get(normalized_pack, '')
                pack_title_value = pack_titles_map.get(normalized_pack, '')
                pdf.add_packing_slip(item.to_dict(), product_details, item_count, total_items_in_order, pack_product=product_details, pack_name=pack_name_value, pack_title=pack_title_value)

        try:
            pdf_output_folder = tag_output_dir("pdf_output")
            today_str = date.today().strftime("%Y-%m-%d")
            date_folder = pdf_output_folder / today_str
            date_folder.mkdir(parents=True, exist_ok=True)
            
            actual_process_id = str(process_number).split()[-1]
            output_filename = date_folder / f"{actual_process_id}.pdf"
            
            pdf.output(str(output_filename))
            print(f"   🎉 Success! PDF for process '{process_number}' generated at: {output_filename.resolve()}")
        except Exception as e:
            print(f"\n   ❌ FATAL ERROR: Could not save the PDF for process '{process_number}'. Is the file open elsewhere?\n   Reason: {e}")

    print("\n\n✅ All PDF files have been generated successfully!")

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
