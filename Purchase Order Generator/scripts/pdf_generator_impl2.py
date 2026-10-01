from __future__ import annotations
import pandas as pd
from fpdf import FPDF
from pathlib import Path
from datetime import date
from app_paths import APP_ROOT, asset_path, data_path, packs_database_path, product_database_path, tag_output_dir

def generate_packing_slips_for_tag(csv_filename, tag_id, output_path=None):
    """Generate PDF packing slips for a specific tag ID CSV file. Returns True if a PDF was saved."""
    print(f"\n[PDF] Starting PDF generation for tag {tag_id}...")

    try:
        orders_df = pd.read_csv(
            csv_filename,
            dtype={
                COLUMN_NAMES['sku']: str,
                COLUMN_NAMES['process']: str,
                COLUMN_NAMES['components']: str,
                COLUMN_NAMES['component_colours']: str,
            },
        )
        products_df = pd.read_excel(PRODUCT_DATABASE_FILE, dtype={COLUMN_NAMES['db_sku']: str, COLUMN_NAMES['product_code']: str})
        # Load Pack Names and Titles maps via openpyxl
        pack_names_map = _load_pack_names_map(PACKS_DATABASE_FILE)
        pack_titles_map = _load_pack_titles_map(PACKS_DATABASE_FILE)
        export_by_uid = _load_btc_product_data_by_uid()
        try:
            from run_script import load_packs_database
            packs_components_map = load_packs_database(str(PACKS_DATABASE_FILE))
        except Exception:
            packs_components_map = {}
        
        products_df = products_df.drop_duplicates(subset=[COLUMN_NAMES['db_sku']], keep='first')
        products_df = products_df.set_index(COLUMN_NAMES['db_sku'])
        
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

    # Group by tag (process) - should be all the same tag
    grouped_by_process = orders_df.groupby(COLUMN_NAMES['process'])

    for process_number, process_df in grouped_by_process:
        print(f"\n--- Processing Tag: {process_number} ---")
        
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=MARGIN)
        pages_before = pdf.page

        grouped_orders = process_df.groupby(COLUMN_NAMES['order_id'], sort=False)

        for order_id, items_in_order in grouped_orders:
            total_items_in_order = len(items_in_order)
            print(f"   Processing Order {order_id} ({total_items_in_order} item(s))...")

            for item_count, (_, item) in enumerate(items_in_order.iterrows(), 1):
                sku = item.get(COLUMN_NAMES['sku'])
                linked_sku = item.get('Linked SKU', '') if 'Linked SKU' in item else ''
                components_str = item.get(COLUMN_NAMES['components'], '') if COLUMN_NAMES['components'] in item else ''
                colours_str = item.get(COLUMN_NAMES['component_colours'], '') if COLUMN_NAMES['component_colours'] in item else ''
                
                # Use linked SKU for product lookup if available (for non-pack items)
                lookup_sku = linked_sku if linked_sku else sku
                
                print(f"     - Item {item_count}/{total_items_in_order}, SKU: {sku}")
                if linked_sku and linked_sku != sku:
                    print(f"       Using linked SKU for product lookup: {linked_sku}")

                if not sku or pd.isna(sku):
                    continue

                # If components present, treat as Pack of N
                components = []
                if isinstance(components_str, str) and components_str.strip():
                    components = [c.strip() for c in components_str.split(',') if c.strip()]

                # OOS / issue CSV rows omit Components — recover from Packs Database
                if not components:
                    normalized_pack_lookup = str(sku).split('-')[0] if sku and '-' in str(sku) else str(sku)
                    pack_entries = packs_components_map.get(str(normalized_pack_lookup).strip(), [])
                    if pack_entries:
                        components = [str(e.get("sku", "")).strip() for e in pack_entries if e.get("sku")]
                        if not (isinstance(colours_str, str) and colours_str.strip()):
                            colours_str = ",".join(str(e.get("colour", "") or "") for e in pack_entries)

                if components:
                    # Build product details list for each component
                    component_products = []
                    for comp_sku in components:
                        comp_details = _lookup_product_details(products_df, comp_sku, export_by_uid)
                        if not comp_details:
                            print(f"       Warning: Product details not found for component SKU '{comp_sku}'.")
                        component_products.append({**comp_details, COLUMN_NAMES['db_sku']: comp_sku})

                    # Attach colours string into item_data so renderer can show colours instead of IDs
                    item_dict = item.to_dict()
                    item_dict[COLUMN_NAMES['component_colours']] = colours_str
                    pack_product_details = _lookup_product_details(products_df, sku, export_by_uid) or None
                    normalized_pack = str(sku).split('-')[0] if sku and '-' in str(sku) else str(sku)
                    pack_name_value = pack_names_map.get(normalized_pack, '')
                    pack_title_value = pack_titles_map.get(normalized_pack, '')

                    add_pack_fn = getattr(pdf, 'add_pack_slip', None)
                    if callable(add_pack_fn):
                        add_pack_fn(
                            item_dict,
                            component_products,
                            item_count,
                            total_items_in_order,
                            pack_product=pack_product_details,
                            pack_name=pack_name_value,
                            pack_title=pack_title_value,
                        )
                    else:
                        # Fallback: render as single slip using pack SKU details
                        fallback_item = item.to_dict()
                        _safe_add_single_page(pdf, fallback_item, pack_product_details or {}, item_count, total_items_in_order)
                else:
                    product_details = _lookup_product_details(products_df, lookup_sku, export_by_uid)
                    if product_details and linked_sku and linked_sku != sku:
                        print(f"     Found product details using linked SKU: {lookup_sku}")
                    elif not product_details:
                        print(f"     Warning: Product details not found in database for SKU '{lookup_sku}' (Original: {sku}).")

                    # Even for single items (no components), enrich with Pack Name/Title from Packs DB if available
                    normalized_pack = str(sku).split('-')[0] if sku and '-' in str(sku) else str(sku)
                    pack_name_value = pack_names_map.get(normalized_pack, '')
                    pack_title_value = pack_titles_map.get(normalized_pack, '')
                    
                    # Debug: Print what we found in packs database
                    print(f"     Looking for normalized pack: {normalized_pack}")
                    print(f"     Pack name found: {pack_name_value}")
                    print(f"     Pack title found: {pack_title_value}")

                    add_single_fn = getattr(pdf, 'add_packing_slip', None)
                    if callable(add_single_fn):
                        add_single_fn(
                            item.to_dict(),
                            product_details,
                            item_count,
                            total_items_in_order,
                            pack_product=product_details or None,
                            pack_name=pack_name_value,
                            pack_title=pack_title_value,
                        )
                    else:
                        _safe_add_single_page(pdf, item.to_dict(), product_details, item_count, total_items_in_order)

        if pdf.page <= pages_before:
            print(f"   [WARNING] No PDF pages generated for tag '{process_number}' — skipping save.")
            continue

        try:
            if output_path:
                # Use provided output path
                output_filename = Path(output_path)
                output_filename.parent.mkdir(parents=True, exist_ok=True)
            else:
                pdf_output_folder = tag_output_dir("pdf_output")
                today_str = date.today().strftime("%Y-%m-%d")
                date_folder = pdf_output_folder / today_str
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
            print(f"\n   ERROR: Could not save the PDF for tag '{tag_id}'. Is the file open elsewhere?\n   Reason: {e}")

    print(f"\n[PDF] PDF generation for tag {tag_id} completed!")
    return saved_any
