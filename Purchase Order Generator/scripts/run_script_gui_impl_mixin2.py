from __future__ import annotations
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
from shipstation_orders import ShipStationAPI, ShipStationError
from app_paths import DATA_DIR, asset_path, data_path, shipstation_tags_path, tag_output_dir
from pdf_generator import generate_packing_slips_for_tag
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

class ShipStationGUIMixin2:
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

            # API init (shared ShipStation credentials)
            try:
                self.log_message("[INFO] Initializing API client...")
                shipstation = ShipStationAPI()
                self.log_message("[SUCCESS] API client initialized successfully")
            except Exception as e:
                self.log_message(f"[ERROR] Error initializing API client: {e}")
                self.log_message(
                    "   Create config/ShipStation/.env with REAL_API_KEY / REAL_API_SECRET"
                )
                return

            status_display = "Awaiting Dispatch"
            self.log_message(f"[SUCCESS] Processing: {status_display} orders only")

            self.log_message(
                f"\n[FETCH] Fetching {status_display.lower()} orders with tag ID: {tag_id}..."
            )
            try:
                filtered_orders = shipstation.get_orders_by_tag(tag_id)
            except ShipStationError as e:
                self.log_message(f"[ERROR] Error fetching orders: {e}")
                return
            except Exception as e:
                self.log_message(f"[ERROR] Error fetching orders: {e}")
                return

            if not filtered_orders:
                self.log_message(
                    f"[INFO] No {status_display.lower()} orders found for tag ID {tag_id}."
                )
                return

            self.log_message(f"[SUCCESS] Total orders found: {len(filtered_orders)}")

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
            self.export_orders(filtered_orders, tag_id, tag_name, process_no, shipstation)

            self.log_message("\n🎉 Done!")
            self.update_status("Completed successfully")

        except Exception as e:
            self.log_message(f"[ERROR] Unexpected error: {e}")
            self.update_status("Error occurred")
        finally:
            self.is_running = False
            self.run_button.config(state='normal')
            self.progress.stop()

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

    def update_status(self, status: str):
        self.status_label.config(text=status)
