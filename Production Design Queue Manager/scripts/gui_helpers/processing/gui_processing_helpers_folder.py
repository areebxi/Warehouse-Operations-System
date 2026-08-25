"""Folder processing utility helpers."""

import os
from typing import List, Tuple, Dict, Optional
import pandas as pd


def find_dtf_des_files(folder_path: str) -> List[str]:
    excel_files = []
    if not os.path.exists(folder_path):
        return excel_files
    for file in os.listdir(folder_path):
        if (('DTF Des' in file or 'dtf des' in file.lower()) and file.endswith(('.xlsx', '.xls', '.csv')) and not file.startswith('~$')):
            excel_files.append(os.path.join(folder_path, file))
    return excel_files


def auto_detect_sku_column(df) -> Optional[str]:
    columns = [col for col in df.columns if pd.notna(col)]
    sku_columns = [col for col in columns if 'sku' in col.lower() and 'item' in col.lower()]
    if not sku_columns:
        sku_columns = [col for col in columns if 'sku' in col.lower()]
    return sku_columns[0] if sku_columns else None


def auto_detect_order_column(df) -> Optional[str]:
    columns = [col for col in df.columns if pd.notna(col)]
    order_columns = [col for col in columns if 'order' in col.lower() and 'number' in col.lower()]
    if not order_columns:
        order_columns = [col for col in columns if 'order' in col.lower()]
    return order_columns[0] if order_columns else None


def auto_detect_customise_column(df) -> Optional[str]:
    columns = [col for col in df.columns if pd.notna(col)]
    for col in columns:
        if str(col).strip().lower() in ("customise", "customize"):
            return col
    return None


def build_processing_summary_message(success_count: int, total_designs: int, batches_count: int, failed_files: List[str]) -> str:
    message = f"Processed {success_count} file(s) successfully!"
    if total_designs > 0:
        message += f"\n\nTotal designs: {total_designs}"
        if batches_count > 1:
            message += f"\nArranged in {batches_count} batches"
    if failed_files:
        message += "\n\nFailed files:\n" + "\n".join(failed_files[:10])
        if len(failed_files) > 10:
            message += f"\n... and {len(failed_files) - 10} more"
    return message


def load_dataframe_from_file(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)


def process_file_in_folder_standard(gui, file_path: str, df: pd.DataFrame, processing_func) -> Tuple[List[Dict], List[List[Dict]], List[int], Optional[str]]:
    try:
        column = auto_detect_sku_column(df)
        if not column:
            return [], [], [], f"{os.path.basename(file_path)}: No SKU column found"
        file_designs, file_batches, missing_row_indices = processing_func(gui, df, column, file_path)
        return file_designs, file_batches, missing_row_indices, None
    except Exception as e:
        return [], [], [], f"{os.path.basename(file_path)}: {str(e)}"


def process_file_in_folder_personalised(gui, file_path: str, df: pd.DataFrame, processing_func) -> Tuple[List[Dict], List[List[Dict]], List[int], Optional[str]]:
    try:
        order_column = auto_detect_order_column(df)
        if not order_column:
            return [], [], [], f"{os.path.basename(file_path)}: No Order Number column found"
        sku_column = auto_detect_sku_column(df)
        if not sku_column:
            return [], [], [], f"{os.path.basename(file_path)}: No Item SKU column found"
        file_designs, file_batches, missing_row_indices = processing_func(gui, df, order_column, sku_column, file_path)
        return file_designs, file_batches, missing_row_indices, None
    except Exception as e:
        return [], [], [], f"{os.path.basename(file_path)}: {str(e)}"


def process_file_in_folder_missing_logo(gui, file_path: str, df: pd.DataFrame, processing_func) -> Tuple[List[Dict], List[List[Dict]], List[int], Optional[str]]:
    try:
        order_column = auto_detect_order_column(df)
        if not order_column:
            return [], [], [], f"{os.path.basename(file_path)}: No Order Number column found"
        sku_column = auto_detect_sku_column(df)
        if not sku_column:
            return [], [], [], f"{os.path.basename(file_path)}: No Item SKU column found"
        file_designs, file_batches, missing_row_indices = processing_func(gui, df, order_column, sku_column, file_path)
        return file_designs, file_batches, missing_row_indices, None
    except Exception as e:
        return [], [], [], f"{os.path.basename(file_path)}: {str(e)}"
