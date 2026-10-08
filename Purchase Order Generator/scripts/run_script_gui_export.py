"""PO GUI export: stock validate, CSV/EDI outputs."""

from __future__ import annotations

import json
import os
from datetime import datetime

from app_paths import tag_output_dir
from run_script import (
    format_run_summary,
    load_custom_label_stock_map,
    load_pack_names,
    load_packs_database,
    load_stock_levels,
    validate_orders_stock,
    write_edi_orders_csv,
    write_packing_list_csv,
    write_stock_issues_csv,
)
from run_script_gui_settings import (
    effective_cl_csv_path,
    effective_packs_database_path,
    effective_plain_database_path,
)
from shipstation_orders import ShipStationAPI


class ShipStationGuiExportMixin:
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
            safe_tag_name = (
                tag_name.replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace(":", "_")
                .replace("*", "_")
                .replace("?", "_")
                .replace('"', "_")
                .replace("<", "_")
                .replace(">", "_")
                .replace("|", "_")
            )
            output_folder = str(tag_output_dir(f"Tag_{safe_tag_name}_Orders_{timestamp}"))
            self.log_message(f"[FOLDER] Created output folder: {output_folder}")

            json_filename = os.path.join(
                output_folder, f"tag_{safe_tag_name}_awaiting_orders_{timestamp}.json"
            )
            detailed_csv_filename = os.path.join(
                output_folder, f"tag_{safe_tag_name}_awaiting_detailed_{timestamp}.csv"
            )
            packing_list_filename = os.path.join(
                output_folder, f"packing_list_tag_{safe_tag_name}_awaiting_{timestamp}.csv"
            )

            self.log_message("[JSON] Creating JSON file...")
            with open(json_filename, "w", encoding="utf-8") as jsonfile:
                json.dump(filtered_orders, jsonfile, indent=2, ensure_ascii=False, default=str)

            self.log_message("[CSV] Creating detailed CSV...")
            detailed_csv_file = shipstation.export_orders_to_csv(
                filtered_orders, detailed_csv_filename
            )

            self.log_message("[STOCK] Loading stock levels (config FTP_LOCAL_FILE)...")
            stock_levels = load_stock_levels(log=self.log_message)

            cl_path = effective_cl_csv_path(self.gui_settings)
            plain_path = effective_plain_database_path(self.gui_settings)
            packs_path = effective_packs_database_path(self.gui_settings)
            self.log_message(f"[SETTINGS] Custom Label CSV: {cl_path}")
            self.log_message(f"[SETTINGS] Plain Database: {plain_path}")
            self.log_message(f"[SETTINGS] Packs Database: {packs_path}")

            self.log_message("[PACKS] Loading Packs Database for component mapping...")
            packs_map = load_packs_database(excel_path=str(packs_path))
            pack_names_map = load_pack_names(excel_path=str(packs_path))
            self.log_message(
                f"[PACKS] Packs map entries: {len(packs_map)}; Pack Names: {len(pack_names_map)}"
            )

            custom_label_map, labels_missing_stock_id = load_custom_label_stock_map(
                path=cl_path, log=self.log_message
            )

            self.log_message(
                "[PACKING] Creating packing list with stock validation (pack-aware)..."
            )
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

            self.log_message(
                f"[SUCCESS] Packing list created with {len(in_stock_items)} in-stock items"
            )

            self.log_message("[EDI] Creating EDI orders file...")
            edi_orders_filename = os.path.join(
                output_folder, f"edi_orders_tag_{safe_tag_name}_{timestamp}.csv"
            )
            write_edi_orders_csv(edi_orders_filename, in_stock_items, process_no)
            self.log_message(f"[SUCCESS] EDI orders file created: {edi_orders_filename}")

            self._export_pdf_slips(
                output_folder=output_folder,
                safe_tag_name=safe_tag_name,
                timestamp=timestamp,
                tag_id=tag_id,
                process_no=process_no,
                in_stock_items=in_stock_items,
                packs_map=packs_map,
                pack_names_map=pack_names_map,
                plain_database_path=str(plain_path),
                packs_database_path=str(packs_path),
            )

            self.log_message("\n[SUCCESS] Export completed!")
            self.log_message(
                f"[FOLDER] All files saved in folder: {os.path.abspath(output_folder)}"
            )
            self.log_message(f"[JSON] JSON: {os.path.basename(json_filename)}")
            self.log_message(f"[CSV] Detailed CSV: {os.path.basename(detailed_csv_file)}")
            self.log_message(
                f"[PACKING] Packing List (In Stock): {os.path.basename(packing_list_filename)}"
            )
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
