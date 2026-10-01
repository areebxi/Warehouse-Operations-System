"""Packs Database loaders for PO stock / packing flows."""
from __future__ import annotations

import os

from app_paths import packs_database_path


def load_packs_database(excel_path=None):
    """
    Load packs mapping from Excel.
    - Column B: pack SKU to search by
    - Columns E, H, K, N, Q: component SKUs to try

    Returns dict: { pack_sku -> [component_sku, ...] }
    """
    packs_map = {}
    try:
        try:
            from openpyxl import load_workbook
        except ImportError:
            print("[WARNING] openpyxl not installed. Skipping Packs Database lookup.")
            return packs_map

        if excel_path is None:
            excel_path = str(packs_database_path())
        if not os.path.exists(excel_path):
            print(f"[WARNING] Packs Database not found at: {excel_path}")
            return packs_map

        wb = load_workbook(excel_path, data_only=True, read_only=True)
        ws = wb.active

        # Column indices (1-based):
        #   Pack SKU in B=2
        #   Component SKUs in E=5, H=8, K=11, N=14, Q=17
        #   Their Colours in     F=6, I=9, L=12, O=15, R=18 (next column)
        pack_col_idx = 2
        component_col_indices = [5, 8, 11, 14, 17]
        colour_col_indices =   [6, 9, 12, 15, 18]

        # Iterate efficiently with values_only
        for row in ws.iter_rows(min_row=2, max_col=18, values_only=True):
            pack_sku = row[pack_col_idx - 1]
            if not pack_sku:
                continue
            pack_sku = str(pack_sku).strip()
            if not pack_sku:
                continue

            component_entries = []
            for comp_col_idx, colour_col_idx in zip(component_col_indices, colour_col_indices):
                val = row[comp_col_idx - 1] if comp_col_idx - 1 < len(row) else None
                if val is None:
                    continue
                sku_str = str(val).strip()
                if not sku_str:
                    continue
                if '-' in sku_str:
                    sku_str = sku_str.split('-')[0]
                colour_val = row[colour_col_idx - 1] if colour_col_idx - 1 < len(row) else None
                colour_str = str(colour_val).strip() if colour_val is not None else ''
                component_entries.append({"sku": sku_str, "colour": colour_str})

            if component_entries:
                normalized_pack = pack_sku.split('-')[0] if '-' in pack_sku else pack_sku
                packs_map[normalized_pack] = component_entries

        print(f"[INFO] Packs Database loaded: {len(packs_map)} pack SKUs mapped")
        return packs_map
    except Exception as e:
        print(f"[WARNING] Failed to load Packs Database: {e}")
        return {}

def load_pack_names(excel_path=None):
    """
    Load Pack Name mapping from Excel.
    - Column B: pack SKU to search by
    - Column C: Pack Name

    Returns dict: { normalized_pack_sku -> pack_name }
    """
    pack_names = {}
    try:
        try:
            from openpyxl import load_workbook
        except ImportError:
            print("[WARNING] openpyxl not installed. Skipping Pack Name lookup.")
            return pack_names

        if excel_path is None:
            excel_path = str(packs_database_path())
        if not os.path.exists(excel_path):
            print(f"[WARNING] Packs Database not found at: {excel_path}")
            return pack_names

        wb = load_workbook(excel_path, data_only=True, read_only=True)
        ws = wb.active

        # Column indices (1-based): Pack SKU in B=2, Pack Name in C=3
        for row in ws.iter_rows(min_row=2, max_col=3, values_only=True):
            pack_sku = row[1]
            pack_name = row[2] if len(row) > 2 else None
            if not pack_sku:
                continue
            sku_str = str(pack_sku).strip()
            if not sku_str:
                continue
            normalized_pack = sku_str.split('-')[0] if '-' in sku_str else sku_str
            pack_names[normalized_pack] = str(pack_name).strip() if pack_name is not None else ''

        print(f"[INFO] Pack Names loaded: {len(pack_names)} entries")
        return pack_names
    except Exception as e:
        print(f"[WARNING] Failed to load Pack Names: {e}")
        return {}


def _pack_key(sku: str) -> str:
    sku = (sku or "").strip()
    return sku.split("-", 1)[0] if "-" in sku else sku


def basic_sku(original_sku: str) -> str:
    """Marketplace prefix: part before the first dash."""
    return _pack_key(original_sku)
