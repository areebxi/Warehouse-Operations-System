import app_paths  # noqa: F401 — configures import paths before other local imports
from shipstation_orders import ShipStationAPI, ShipStationError
from pdf_generator import generate_packing_slips_for_tag
import sys
import os
import csv
import json
import socket
from datetime import datetime
from ftplib import FTP, error_perm, error_temp, error_reply
from app_paths import data_path, packs_database_path, shipstation_tags_path, tag_output_dir
from stock_resolver import (
    NOT_FOUND_STATUSES,
    STATUS_NOT_FOUND,
    load_custom_label_stock_map,
    not_found_status,
    resolve_stock_level,
)
from run_script_impl2 import download_ftp_file
from run_script_impl5 import _stock_file_paths
from run_script_stock_phase import run_stock_and_export_phase

STATUS_OUT_OF_STOCK = "Out of Stock"


def main():
    """
    Main function using config file for credentials
    """
    print("ShipStation Awaiting Dispatch Orders Fetcher")
    print("Tag Filtering for Awaiting Dispatch Orders Only")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Download stock levels CSV from FTP/SFTP
    remote_file, local_path, _ = _stock_file_paths()
    print("[STEP 1] Downloading stock levels from BTC...")
    print(f"[INFO] Stock file: remote={remote_file} → local={local_path}")
    if not download_ftp_file():
        print("[WARNING] FTP download failed. Continuing with cached/missing stock data if available.")
    print()
    
    # Initialize API client (shared credentials)
    try:
        print("[INFO] Initializing API client...")
        shipstation = ShipStationAPI()
        print("[SUCCESS] API client initialized successfully")
    except Exception as e:
        print(f"[ERROR] Error initializing API client: {e}")
        print("   Create config/ShipStation/.env with REAL_API_KEY / REAL_API_SECRET")
        sys.exit(1)

    status_display = "Awaiting Dispatch"
    print(f"[SUCCESS] Processing: {status_display} orders only")

    print("\n[TAG SEARCH] Tag ID Search")
    tag_id = input("Enter TAG ID: ").strip()
    if not tag_id:
        print("[ERROR] Tag ID cannot be empty!")
        sys.exit(1)

    print(f"\n[FETCH] Fetching {status_display.lower()} orders with tag ID: {tag_id}...")
    try:
        filtered_orders = shipstation.get_orders_by_tag(tag_id)
    except ShipStationError as e:
        print(f"[ERROR] Error fetching orders: {e}")
        print("   This could be due to:")
        print("   - Invalid API credentials")
        print("   - Network connectivity issues")
        print("   - ShipStation API rate limiting")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error fetching orders: {e}")
        sys.exit(1)

    if not filtered_orders:
        print(f"[INFO] No {status_display.lower()} orders found for tag ID {tag_id}.")
        return

    print(f"[SUCCESS] Total orders found: {len(filtered_orders)}")

    if filtered_orders:
        first_order = filtered_orders[0]
        print("\n[DEBUG] Debug - First order structure:")
        print(f"   Order Number: {first_order.get('orderNumber', 'N/A')}")
        print(f"   Has 'items' field: {'items' in first_order}")
        print(f"   Has 'lineItems' field: {'lineItems' in first_order}")
        if 'items' in first_order:
            items = first_order.get('items', [])
            print(f"   Items count: {len(items)}")
            if items:
                print(f"   First item: {items[0]}")
        if 'lineItems' in first_order:
            line_items = first_order.get('lineItems', [])
            print(f"   LineItems count: {len(line_items)}")
            if line_items:
                print(f"   First lineItem: {line_items[0]}")
        print()
    
    # Display summary
    print("\n[SUMMARY] Order Summary:")
    print("-" * 50)
    for i, order in enumerate(filtered_orders[:10], 1):  # Show first 10 orders
        order_number = order.get('orderNumber', 'N/A')
        customer_name = order.get('customerName', 'N/A')
        amount_paid = order.get('amountPaid', 0)
        order_date = order.get('orderDate', 'N/A')
        
        print(f"{i:2d}. Order #{order_number}")
        print(f"    Customer: {customer_name}")
        print(f"    Amount: ${amount_paid}")
        print(f"    Date: {order_date}")
        print()
    
    if len(filtered_orders) > 10:
        print(f"    ... and {len(filtered_orders) - 10} more orders")
        print()
    
    # Export to all formats
    print("[EXPORT] Exporting orders...")
    try:
        # Create output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = str(tag_output_dir(f"Tag_{tag_id}_Orders_{timestamp}"))
        print(f"[FOLDER] Created output folder: {output_folder}")
        
        # Create files in the folder
        json_filename = os.path.join(output_folder, f"tag_{tag_id}_awaiting_orders_{timestamp}.json")
        detailed_csv_filename = os.path.join(output_folder, f"tag_{tag_id}_awaiting_detailed_{timestamp}.csv")
        packing_list_filename = os.path.join(output_folder, f"packing_list_tag_{tag_id}_awaiting_{timestamp}.csv")
        
        # Export JSON
        print("[JSON] Creating JSON file...")
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(filtered_orders, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        # Export detailed CSV
        print("[CSV] Creating detailed CSV...")
        detailed_csv_file = shipstation.export_orders_to_csv(filtered_orders, detailed_csv_filename)
        
        run_stock_and_export_phase(
            filtered_orders=filtered_orders,
            tag_id=tag_id,
            output_folder=output_folder,
            timestamp=timestamp,
            packing_list_filename=packing_list_filename,
            json_filename=json_filename,
            detailed_csv_file=detailed_csv_file,
        )
    except Exception as e:
        print(f"[ERROR] Error exporting orders: {e}")
        print("   Please check if you have write permissions in the current directory")
        sys.exit(1)
    
    print("\n[SUCCESS] Done!")

