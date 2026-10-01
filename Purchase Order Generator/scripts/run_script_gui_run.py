"""PO GUI run orchestration (fetch + handoff to export)."""

from __future__ import annotations

import threading
from datetime import datetime
from tkinter import messagebox

from run_script import _stock_file_paths, download_ftp_file, get_process_no_for_tag
from shipstation_orders import ShipStationAPI, ShipStationError


class ShipStationGuiRunMixin:
    def run_script(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Script is already running!")
            return

        if not self.selected_tag_id:
            messagebox.showerror("Error", "Please select a Tag Name!")
            return

        self.is_running = True
        self.run_button.config(state="disabled")
        self.progress.start()
        self.update_status("Running...")

        thread = threading.Thread(
            target=self.run_main_script, args=(self.selected_tag_id, self.selected_tag_name)
        )
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

            process_no = get_process_no_for_tag(tag_id)
            if process_no:
                self.log_message(f"[INFO] Process No for Tag {tag_id}: {process_no}")
            else:
                self.log_message(
                    f"[WARNING] Process No not found for Tag {tag_id}. Will fallback in EDI order-id."
                )

            self.log_message("\n[SUMMARY] Order Summary:")
            self.log_message("-" * 50)
            for i, order in enumerate(filtered_orders[:10], 1):
                order_number = order.get("orderNumber", "N/A")
                customer_name = order.get("customerName", "N/A")
                amount_paid = order.get("amountPaid", 0)
                order_date = order.get("orderDate", "N/A")
                self.log_message(f"{i:2d}. Order #{order_number}")
                self.log_message(f"    Customer: {customer_name}")
                self.log_message(f"    Amount: ${amount_paid}")
                self.log_message(f"    Date: {order_date}")
                self.log_message("")

            self.log_message("[EXPORT] Exporting orders...")
            self.export_orders(filtered_orders, tag_id, tag_name, process_no, shipstation)

            self.log_message("\n🎉 Done!")
            self.update_status("Completed successfully")

        except Exception as e:
            self.log_message(f"[ERROR] Unexpected error: {e}")
            self.update_status("Error occurred")
        finally:
            self.is_running = False
            self.run_button.config(state="normal")
            self.progress.stop()
