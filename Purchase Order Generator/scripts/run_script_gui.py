"""
GUI for the updated run_script.py flow (Awaiting Dispatch + Specific Tag)
Reuses helpers from run_script.py and matches pack/process-no logic and outputs.
"""

import app_paths  # noqa: F401 — configures import paths before other local imports

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import sys
import csv
import json
import shutil
from datetime import datetime
import openpyxl

from ftplib import FTP, error_perm, error_temp, error_reply  # noqa: F401 (for parity logging)

# Reuse original modules and helpers
from shipstation_orders import ShipStationAPI
from config import SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET
from app_paths import DATA_DIR, asset_path, data_path, shipstation_tags_path, tag_output_dir
from pdf_generator import generate_packing_slips_for_tag

GUI_SETTINGS_PATH = DATA_DIR / "gui_settings.json"

# Import helpers from run_script.py
from run_script import (
    get_process_no_for_tag,
    pdf_filename_for_tag,
    load_packs_database,
    load_pack_names,
    download_ftp_file,
    load_stock_levels,
    _stock_file_paths,
    load_custom_label_stock_map,
    validate_orders_stock,
    write_packing_list_csv,
    write_edi_orders_csv,
    write_stock_issues_csv,
    format_run_summary,
    rows_for_pdf_slips,
)


def load_gui_settings() -> dict:
    """Load remembered GUI settings (e.g. PDF copy folder)."""
    try:
        if GUI_SETTINGS_PATH.exists():
            with open(GUI_SETTINGS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"[WARNING] Could not load GUI settings: {e}")
    return {}


def save_gui_settings(settings: dict) -> None:
    """Persist GUI settings to data/gui_settings.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(GUI_SETTINGS_PATH, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
    except Exception as e:
        print(f"[WARNING] Could not save GUI settings: {e}")


def load_tag_mapping():
    """
    Load Tag Name → Tag ID from ShipStation Tags.xlsx.
    Column B: Tag Name, Column C: Tag ID
    """
    tag_mapping = {}
    try:
        xlsx_path = str(shipstation_tags_path())
        if not os.path.exists(xlsx_path):
            print(f"[WARNING] ShipStation Tags.xlsx not found at: {xlsx_path}")
            return tag_mapping

        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2):  # Skip header row
            tag_name_cell = row[1]  # Column B (0-based index 1)
            tag_id_cell = row[2]    # Column C (0-based index 2)
            
            tag_name = "" if tag_name_cell.value is None else str(tag_name_cell.value).strip()
            tag_id = "" if tag_id_cell.value is None else str(tag_id_cell.value).strip()
            
            if tag_name and tag_id:
                tag_mapping[tag_name] = tag_id
                
        return tag_mapping
    except Exception as e:
        print(f"[ERROR] Error loading tag mapping: {e}")
        return tag_mapping


class ShipStationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Purchase Order App")
        self.root.geometry("800x640")
        self.root.resizable(True, True)

        self.tag_name_var = tk.StringVar()
        self.pdf_copy_folder_var = tk.StringVar()
        self.selected_tag_id = None
        self.selected_tag_name = None
        self.is_running = False
        self.gui_settings = load_gui_settings()
        remembered = str(self.gui_settings.get("pdf_copy_folder") or "").strip()
        if remembered:
            self.pdf_copy_folder_var.set(remembered)

        # Load tag mapping
        self.tag_mapping = load_tag_mapping()
        if not self.tag_mapping:
            messagebox.showerror("Error", "ShipStation Tags.xlsx file not found or could not be loaded!")

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        title_label = ttk.Label(main_frame, text="Purchase Order App", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        ttk.Label(main_frame, text="Tag Name:").grid(row=1, column=0, sticky=tk.W, pady=5)

        # Tag Name combobox
        self.tag_combobox = ttk.Combobox(main_frame, textvariable=self.tag_name_var, width=30, state="readonly")
        self.tag_combobox.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        # Populate combobox with tag names
        tag_names = list(self.tag_mapping.keys())
        self.tag_combobox['values'] = sorted(tag_names)

        # Bind selection event
        self.tag_combobox.bind('<<ComboboxSelected>>', self.on_tag_selected)

        self.run_button = ttk.Button(main_frame, text="Run", command=self.run_script)
        self.run_button.grid(row=1, column=2, sticky=(tk.W, tk.E), padx=(20, 0))

        ttk.Label(main_frame, text="PDF copy folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pdf_copy_entry = ttk.Entry(
            main_frame, textvariable=self.pdf_copy_folder_var, state="readonly"
        )
        self.pdf_copy_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        pdf_folder_btns = ttk.Frame(main_frame)
        pdf_folder_btns.grid(row=2, column=2, sticky=(tk.W, tk.E), padx=(20, 0))
        self.browse_button = ttk.Button(
            pdf_folder_btns, text="Browse...", command=self.browse_pdf_copy_folder
        )
        self.browse_button.pack(side=tk.LEFT)
        self.clear_pdf_folder_button = ttk.Button(
            pdf_folder_btns, text="Remove", command=self.clear_pdf_copy_folder
        )
        self.clear_pdf_folder_button.pack(side=tk.LEFT, padx=(6, 0))

        self.logs_text = scrolledtext.ScrolledText(main_frame, height=20, width=80, font=("Consolas", 9))
        self.logs_text.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_label = ttk.Label(main_frame, text="Ready", font=("Arial", 9))
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(5, 0))

    def browse_pdf_copy_folder(self):
        """Let the user pick a folder; remember it for later runs."""
        initial = self.pdf_copy_folder_var.get().strip()
        if not initial or not os.path.isdir(initial):
            initial = None
        chosen = filedialog.askdirectory(
            title="Select PDF copy folder",
            initialdir=initial or None,
            mustexist=True,
        )
        if not chosen:
            return
        self.pdf_copy_folder_var.set(chosen)
        self.gui_settings["pdf_copy_folder"] = chosen
        save_gui_settings(self.gui_settings)
        self.log_message(f"[SETTINGS] PDF copy folder set to: {chosen}")

    def clear_pdf_copy_folder(self):
        """Clear the remembered PDF copy folder."""
        if not self.pdf_copy_folder_var.get().strip() and not self.gui_settings.get("pdf_copy_folder"):
            self.log_message("[SETTINGS] No PDF copy folder to remove.")
            return
        self.pdf_copy_folder_var.set("")
        self.gui_settings.pop("pdf_copy_folder", None)
        save_gui_settings(self.gui_settings)
        self.log_message("[SETTINGS] PDF copy folder removed.")

    def log_message(self, message: str):
        self.logs_text.insert(tk.END, f"{message}\n")
        self.logs_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, status: str):
        self.status_label.config(text=status)

    def on_tag_selected(self, event):
        """Tag Name select hone par corresponding Tag ID set karta hai"""
        selected_tag_name = self.tag_name_var.get()
        if selected_tag_name in self.tag_mapping:
            self.selected_tag_id = self.tag_mapping[selected_tag_name]
            self.selected_tag_name = selected_tag_name
            self.log_message(f"Selected Tag: {selected_tag_name} (ID: {self.selected_tag_id})")
        else:
            self.selected_tag_id = None
            self.selected_tag_name = None

    def copy_pdf_to_selected_folder(self, pdf_output_path: str) -> None:
        """Copy a generated PDF into the remembered folder, if configured."""
        dest_folder = self.pdf_copy_folder_var.get().strip()
        if not dest_folder:
            self.log_message("[PDF] Copy skipped — no PDF copy folder selected (use Browse).")
            return
        if not os.path.isdir(dest_folder):
            self.log_message(
                f"[WARNING] PDF copy skipped — folder does not exist: {dest_folder} "
                "(use Browse to pick a new folder)."
            )
            return
        try:
            dest_path = shutil.copy2(pdf_output_path, dest_folder)
            self.log_message(f"[SUCCESS] PDF copied to: {os.path.abspath(dest_path)}")
        except Exception as e:
            self.log_message(f"[WARNING] PDF copy failed: {e}")

    def run_script(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Script is already running!")
            return

        if not self.selected_tag_id:
            messagebox.showerror("Error", "Please select a Tag Name!")
            return

        self.is_running = True
        self.run_button.config(state='disabled')
        self.progress.start()
        self.update_status("Running...")

        thread = threading.Thread(target=self.run_main_script, args=(self.selected_tag_id, self.selected_tag_name))
        thread.daemon = True
        thread.start()

    def run_main_script(self, tag_id: str, tag_name: str):
        try:
            self.log_message("=" * 50)
            self.log_message("Purchase Order App")
            self.log_message("Tag Filtering for Awaiting Dispatch Orders Only")
            self.log_message("=" * 50)
            self.log_message(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_message("")

            # Step 1: FTP download
            remote_file, local_path, _ = _stock_file_paths()
            self.log_message("[STEP 1] Downloading stock levels from BTC...")
            self.log_message(
                f"[INFO] Stock file: remote={remote_file} → local={local_path} "
                f"(change FTP_REMOTE_FILE / FTP_LOCAL_FILE in config.py)"
            )
            try:
                download_ftp_file(log=self.log_message)
            except Exception as e:
                self.log_message(f"[WARNING] FTP step raised an exception: {e}")
            self.log_message("")

            # Credentials check
            if not SHIPSTATION_API_KEY or not SHIPSTATION_API_SECRET or SHIPSTATION_API_KEY == "your_api_key_here" or SHIPSTATION_API_SECRET == "your_api_secret_here":
                self.log_message("[ERROR] Please configure your API credentials in config.py")
                self.log_message("   Copy config_example.py to config.py and update with your actual credentials")
                return

            # API init
            try:
                self.log_message("[INFO] Initializing API client...")
                shipstation = ShipStationAPI(SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET)
                self.log_message("[SUCCESS] API client initialized successfully")
            except Exception as e:
                self.log_message(f"[ERROR] Error initializing API client: {e}")
                return

            status_display = "Awaiting Dispatch"
            self.log_message(f"[SUCCESS] Processing: {status_display} orders only")

            self.log_message(f"\n[FETCH] Fetching {status_display.lower()} orders with tag ID: {tag_id}...")
            try:
                orders = shipstation.get_awaiting_dispatch_orders()
            except Exception as e:
                self.log_message(f"[ERROR] Error fetching orders: {e}")
                return

            if not orders:
                self.log_message(f"[INFO] No {status_display.lower()} orders found.")
                return

            # Filter by tag
            self.log_message("[FILTER] Filtering orders by tag ID...")
            original_count = len(orders)
            filtered_orders = []
            for order in orders:
                order_tags = order.get('tagIds') or []
                if str(tag_id) in [str(t) for t in order_tags]:
                    filtered_orders.append(order)
                    self.log_message(f"[FOUND] Found order {order.get('orderNumber', 'N/A')} with tag ID {tag_id}")

            self.log_message(f"[FILTER] Filtered {original_count} orders down to {len(filtered_orders)} orders")
            if not filtered_orders:
                self.log_message("[INFO] No orders found with the specified tag ID.")
                return

            # Process No lookup
            process_no = get_process_no_for_tag(tag_id)
            if process_no:
                self.log_message(f"[INFO] Process No for Tag {tag_id}: {process_no}")
            else:
                self.log_message(f"[WARNING] Process No not found for Tag {tag_id}. Will fallback in EDI order-id.")

            # Summary
            self.log_message("\n[SUMMARY] Order Summary:")
            self.log_message("-" * 50)
            for i, order in enumerate(filtered_orders[:10], 1):
                order_number = order.get('orderNumber', 'N/A')
                customer_name = order.get('customerName', 'N/A')
                amount_paid = order.get('amountPaid', 0)
                order_date = order.get('orderDate', 'N/A')
                self.log_message(f"{i:2d}. Order #{order_number}")
                self.log_message(f"    Customer: {customer_name}")
                self.log_message(f"    Amount: ${amount_paid}")
                self.log_message(f"    Date: {order_date}")
                self.log_message("")

            # Export
            self.log_message("[EXPORT] Exporting orders...")
            self.export_orders(filtered_orders, tag_id, tag_name, process_no)

            self.log_message("\n🎉 Done!")
            self.update_status("Completed successfully")

        except Exception as e:
            self.log_message(f"[ERROR] Unexpected error: {e}")
            self.update_status("Error occurred")
        finally:
            self.is_running = False
            self.run_button.config(state='normal')
            self.progress.stop()

    def export_orders(self, filtered_orders, tag_id: str, tag_name: str, process_no: str | None):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Tag name mein spaces aur special characters replace karte hain
            safe_tag_name = tag_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
            output_folder = str(tag_output_dir(f"Tag_{safe_tag_name}_Orders_{timestamp}"))
            self.log_message(f"[FOLDER] Created output folder: {output_folder}")

            json_filename = os.path.join(output_folder, f"tag_{safe_tag_name}_awaiting_orders_{timestamp}.json")
            detailed_csv_filename = os.path.join(output_folder, f"tag_{safe_tag_name}_awaiting_detailed_{timestamp}.csv")
            packing_list_filename = os.path.join(output_folder, f"packing_list_tag_{safe_tag_name}_awaiting_{timestamp}.csv")

            # JSON
            self.log_message("[JSON] Creating JSON file...")
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(filtered_orders, jsonfile, indent=2, ensure_ascii=False, default=str)

            # Detailed CSV
            self.log_message("[CSV] Creating detailed CSV...")
            shipstation = ShipStationAPI(SHIPSTATION_API_KEY, SHIPSTATION_API_SECRET)
            detailed_csv_file = shipstation.export_orders_to_csv(filtered_orders, detailed_csv_filename)

            self.log_message("[STOCK] Loading stock levels (config FTP_LOCAL_FILE)...")
            stock_levels = load_stock_levels(log=self.log_message)

            self.log_message("[PACKS] Loading Packs Database for component mapping...")
            packs_map = load_packs_database()
            pack_names_map = load_pack_names()
            self.log_message(f"[PACKS] Packs map entries: {len(packs_map)}; Pack Names: {len(pack_names_map)}")

            custom_label_map, labels_missing_stock_id = load_custom_label_stock_map(
                log=self.log_message
            )

            self.log_message("[PACKING] Creating packing list with stock validation (pack-aware)...")
            in_stock_items, out_of_stock_items, not_found_items = validate_orders_stock(
                filtered_orders,
                tag_id,
                process_no,
                stock_levels,
                packs_map,
                pack_names_map,
                custom_label_map,
                log=self.log_message,
                labels_missing_stock_id=labels_missing_stock_id,
            )

            write_packing_list_csv(packing_list_filename, in_stock_items)

            issues_filename = None
            if out_of_stock_items or not_found_items:
                issues_filename = os.path.join(
                    output_folder, f"stock_issues_tag_{safe_tag_name}_{timestamp}.csv"
                )
                self.log_message(f"[ISSUES] Creating stock issues list: {issues_filename}")
                write_stock_issues_csv(issues_filename, out_of_stock_items, not_found_items)
                self.log_message(
                    f"[WARNING] {len(not_found_items)} not found, "
                    f"{len(out_of_stock_items)} out of stock -> {issues_filename}"
                )

            self.log_message(f"[SUCCESS] Packing list created with {len(in_stock_items)} in-stock items")

            self.log_message("[EDI] Creating EDI orders file...")
            edi_orders_filename = os.path.join(output_folder, f"edi_orders_tag_{safe_tag_name}_{timestamp}.csv")
            write_edi_orders_csv(edi_orders_filename, in_stock_items, process_no)
            self.log_message(f"[SUCCESS] EDI orders file created: {edi_orders_filename}")

            # PDF for EDI orders only (fully in-stock)
            self.log_message("\n[PDF] Generating PDF packing slips (EDI / in-stock orders only)...")
            if not in_stock_items:
                self.log_message(
                    "[PDF] Skipped — no in-stock (EDI) orders to generate packing slips for."
                )
            else:
                try:
                    product_images_dir = str(asset_path("product_images"))
                    brand_logos_dir = str(asset_path("brand_logos"))
                    if not os.path.exists(product_images_dir):
                        self.log_message(f"[WARNING] Product images folder not found: {product_images_dir}")
                    if not os.path.exists(brand_logos_dir):
                        self.log_message(f"[WARNING] Brand logos folder not found: {brand_logos_dir}")

                    pdf_source_filename = os.path.join(
                        output_folder, f"pdf_packing_tag_{safe_tag_name}_awaiting_{timestamp}.csv"
                    )
                    write_packing_list_csv(
                        pdf_source_filename,
                        rows_for_pdf_slips(
                            in_stock_items,
                            [],
                            [],
                            packs_map=packs_map,
                            pack_names_map=pack_names_map,
                        ),
                    )
                    pdf_output_path = os.path.join(output_folder, pdf_filename_for_tag(tag_id, process_no))
                    if generate_packing_slips_for_tag(pdf_source_filename, tag_id, pdf_output_path):
                        self.log_message(
                            f"[SUCCESS] PDF generation completed! Saved to: {os.path.abspath(pdf_output_path)}"
                        )
                        self.copy_pdf_to_selected_folder(pdf_output_path)
                    else:
                        self.log_message(
                            "[WARNING] PDF was not created (no packing-slip rows). "
                            "Check that EDI orders have line items."
                        )
                except Exception as e:
                    self.log_message(f"[WARNING] PDF generation failed: {e}")

            # Final summary
            self.log_message("\n[SUCCESS] Export completed!")
            self.log_message(f"[FOLDER] All files saved in folder: {os.path.abspath(output_folder)}")
            self.log_message(f"[JSON] JSON: {os.path.basename(json_filename)}")
            self.log_message(f"[CSV] Detailed CSV: {os.path.basename(detailed_csv_file)}")
            self.log_message(f"[PACKING] Packing List (In Stock): {os.path.basename(packing_list_filename)}")
            self.log_message(f"[EDI] EDI Orders File: {os.path.basename(edi_orders_filename)}")
            if issues_filename:
                self.log_message(f"[ISSUES] Stock Issues: {os.path.basename(issues_filename)}")
            self.log_message("")
            self.log_message(
                format_run_summary(
                    tag_label=tag_name,
                    orders_processed=len(filtered_orders),
                    in_stock_items=in_stock_items,
                    out_of_stock_items=out_of_stock_items,
                    not_found_items=not_found_items,
                    issues_filename=issues_filename,
                )
            )

        except Exception as e:
            self.log_message(f"[ERROR] Error exporting orders: {e}")


def main():
    root = tk.Tk()
    ShipStationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


