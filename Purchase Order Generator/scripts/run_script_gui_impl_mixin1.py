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

class ShipStationGUIMixin1:
    def export_orders(
        self,
        filtered_orders,
        tag_id: str,
        tag_name: str,
        process_no: str | None,
        shipstation: ShipStationAPI,
    ):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_tag_name = tag_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
            output_folder = str(tag_output_dir(f"Tag_{safe_tag_name}_Orders_{timestamp}"))
            self.log_message(f"[FOLDER] Created output folder: {output_folder}")

            json_filename = os.path.join(output_folder, f"tag_{safe_tag_name}_awaiting_orders_{timestamp}.json")
            detailed_csv_filename = os.path.join(output_folder, f"tag_{safe_tag_name}_awaiting_detailed_{timestamp}.csv")
            packing_list_filename = os.path.join(output_folder, f"packing_list_tag_{safe_tag_name}_awaiting_{timestamp}.csv")

            self.log_message("[JSON] Creating JSON file...")
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(filtered_orders, jsonfile, indent=2, ensure_ascii=False, default=str)

            self.log_message("[CSV] Creating detailed CSV...")
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
