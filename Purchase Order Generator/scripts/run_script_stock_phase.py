"""Stock validation + packing/EDI/PDF export phase for run_script."""

from __future__ import annotations

import os

from pdf_generator import generate_packing_slips_for_tag
from run_stock_validate import validate_orders_stock
from run_script_impl3 import write_edi_orders_csv, write_stock_issues_csv
from run_script_impl4 import load_pack_names, load_packs_database
from run_script_impl5 import (
    format_run_summary,
    get_process_no_for_tag,
    load_stock_levels,
    rows_for_pdf_slips,
)
from run_script_impl6 import pdf_filename_for_tag, write_packing_list_csv
from stock_resolver import load_custom_label_stock_map


def run_stock_and_export_phase(
    *,
    filtered_orders: list,
    tag_id: str,
    output_folder: str,
    timestamp: str,
    packing_list_filename: str,
    json_filename: str,
    detailed_csv_file: str,
) -> None:
    print("[STOCK] Loading stock levels (see config.py FTP_LOCAL_FILE)...")
    stock_levels = load_stock_levels()

    print("[PACKS] Loading Packs Database for component mapping...")
    packs_map = load_packs_database()
    pack_names_map = load_pack_names()
    print(f"[PACKS] Packs map entries: {len(packs_map)}; Pack Names: {len(pack_names_map)}")

    custom_label_map, labels_missing_stock_id = load_custom_label_stock_map(log=print)

    process_no = get_process_no_for_tag(tag_id)
    if process_no:
        print(f"[INFO] Process No for Tag {tag_id}: {process_no}")
    else:
        print(f"[WARNING] Process No not found for Tag {tag_id}. Will fallback in EDI order-id.")

    print("[PACKING] Creating packing list with stock validation (pack-aware)...")
    in_stock_items, out_of_stock_items, not_found_items = validate_orders_stock(
        filtered_orders,
        tag_id,
        process_no,
        stock_levels,
        packs_map,
        pack_names_map,
        custom_label_map,
        labels_missing_stock_id=labels_missing_stock_id,
    )

    write_packing_list_csv(packing_list_filename, in_stock_items)

    issues_filename = None
    if out_of_stock_items or not_found_items:
        issues_filename = os.path.join(
            output_folder, f"stock_issues_tag_{tag_id}_{timestamp}.csv"
        )
        print(f"[ISSUES] Creating stock issues list: {issues_filename}")
        write_stock_issues_csv(issues_filename, out_of_stock_items, not_found_items)
        print(
            f"[WARNING] {len(not_found_items)} not found, "
            f"{len(out_of_stock_items)} out of stock -> {issues_filename}"
        )

    print(f"[SUCCESS] Packing list created with {len(in_stock_items)} in-stock items")

    print("[EDI] Creating EDI orders file...")
    edi_orders_filename = os.path.join(output_folder, f"edi_orders_tag_{tag_id}_{timestamp}.csv")
    write_edi_orders_csv(edi_orders_filename, in_stock_items, process_no)
    print(f"[SUCCESS] EDI orders file created: {edi_orders_filename}")

    print("\n[SUCCESS] Export completed!")
    print(f"[FOLDER] All files saved in folder: {os.path.abspath(output_folder)}")
    print(f"[JSON] JSON: {os.path.basename(json_filename)}")
    print(f"[CSV] Detailed CSV: {os.path.basename(detailed_csv_file)}")
    print(f"[PACKING] Packing List (In Stock): {os.path.basename(packing_list_filename)}")
    print(f"[EDI] EDI Orders File: {os.path.basename(edi_orders_filename)}")
    if issues_filename:
        print(f"[ISSUES] Stock Issues: {os.path.basename(issues_filename)}")
    print(f"[TOTAL] Total orders: {len(filtered_orders)}")

    print("\n[PDF] Generating PDF packing slips (EDI / in-stock orders only)...")
    if not in_stock_items:
        print("[PDF] Skipped — no in-stock (EDI) orders to generate packing slips for.")
    else:
        try:
            pdf_source_filename = os.path.join(
                output_folder, f"pdf_packing_tag_{tag_id}_awaiting_{timestamp}.csv"
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
                print(
                    f"[SUCCESS] PDF generation completed! Saved to: {os.path.abspath(pdf_output_path)}"
                )
            else:
                print(
                    "[WARNING] PDF was not created (no packing-slip rows). "
                    "Check that EDI orders have line items."
                )
        except Exception as e:
            print(f"[WARNING] PDF generation failed: {e}")
            print("   The CSV files were created successfully, but PDF generation encountered an issue.")

    print()
    print(
        format_run_summary(
            tag_label=str(tag_id),
            orders_processed=len(filtered_orders),
            in_stock_items=in_stock_items,
            out_of_stock_items=out_of_stock_items,
            not_found_items=not_found_items,
            issues_filename=issues_filename,
        )
    )
