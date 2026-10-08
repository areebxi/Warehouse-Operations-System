"""PO GUI PDF packing-slip generation."""

from __future__ import annotations

import os

from app_paths import asset_path
from pdf_generator import generate_packing_slips_for_tag
from run_script import pdf_filename_for_tag, rows_for_pdf_slips, write_packing_list_csv


class ShipStationGuiPdfMixin:
    def _export_pdf_slips(
        self,
        *,
        output_folder: str,
        safe_tag_name: str,
        timestamp: str,
        tag_id: str,
        process_no: str | None,
        in_stock_items,
        packs_map,
        pack_names_map,
        plain_database_path: str | None = None,
        packs_database_path: str | None = None,
    ) -> None:
        self.log_message("\n[PDF] Generating PDF packing slips (EDI / in-stock orders only)...")
        if not in_stock_items:
            self.log_message(
                "[PDF] Skipped — no in-stock (EDI) orders to generate packing slips for."
            )
            return
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
            if generate_packing_slips_for_tag(
                pdf_source_filename,
                tag_id,
                pdf_output_path,
                plain_database_path=plain_database_path,
                packs_database_path=packs_database_path,
            ):
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
