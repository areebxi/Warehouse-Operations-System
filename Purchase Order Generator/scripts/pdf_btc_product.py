"""BTC / Packs product lookup helpers for packing slips."""
from __future__ import annotations

import pandas as pd

from pdf_btc_images import _image_filename_from_url, _read_btc_product_data_csv
from pdf_constants import COLUMN_NAMES

def _load_btc_product_data_by_uid() -> dict[str, dict]:
    """Map BTC stock id (UID) to product fields when Database.xlsx has no row."""
    try:
        export_df, _enc = _read_btc_product_data_csv(dtype={"UID": str})
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[PDF] Warning: Could not load BTC Product Data fallback: {e}")
        return {}

    if "UID" not in export_df.columns:
        return {}

    export_df = export_df[~export_df["UID"].astype(str).str.startswith("[", na=False)]
    export_df = export_df.drop_duplicates(subset=["UID"], keep="first")

    by_uid: dict[str, dict] = {}
    for _, row in export_df.iterrows():
        uid = str(row.get("UID", "")).strip()
        if not uid:
            continue
        hi_res = row.get("image_url_high_res") or row.get("image_url_medium_res")
        by_uid[uid] = {
            COLUMN_NAMES["db_sku"]: uid,
            COLUMN_NAMES["product_code"]: str(row.get("SPC", "") or "").strip(),
            COLUMN_NAMES["brand"]: str(row.get("Brand", "") or "").strip(),
            COLUMN_NAMES["colour"]: str(row.get("Colour Name", "") or "").strip(),
            COLUMN_NAMES["size"]: str(row.get("Size", "") or "").strip(),
            COLUMN_NAMES["description"]: str(row.get("Description", "") or "").strip(),
            COLUMN_NAMES["package"]: "",
            COLUMN_NAMES["product_image_filename"]: _image_filename_from_url(hi_res),
            COLUMN_NAMES["brand_image_filename"]: _image_filename_from_url(row.get("brand image")),
        }
    return by_uid


def _row_to_product_dict(row) -> dict:
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    return row.to_dict()


def _lookup_product_details(
    products_df: pd.DataFrame,
    sku: str,
    export_by_uid: dict[str, dict] | None = None,
) -> dict:
    """Resolve product row from Database.xlsx, then BTC Product Data (UID = stock id)."""
    if not sku or (isinstance(sku, float) and pd.isna(sku)):
        return {}
    sku_str = str(sku).strip()
    if not sku_str:
        return {}

    try:
        return _row_to_product_dict(products_df.loc[sku_str])
    except KeyError:
        pass

    fallback = (export_by_uid or {}).get(sku_str)
    if fallback:
        print(f"     Using BTC Product Data fallback for SKU '{sku_str}' (not in Database.xlsx)")
        return dict(fallback)
    return {}


def _load_pack_names_map(excel_path: str) -> dict:
    """Load {normalized_pack_sku -> Pack Name} using openpyxl (B=SKU, C=Pack Name)."""
    try:
        from openpyxl import load_workbook
    except Exception:
        return {}
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        ws = wb.active
        pack_names = {}
        for row in ws.iter_rows(min_row=2, max_col=3, values_only=True):
            pack_sku = row[1]
            pack_name = row[2] if len(row) > 2 else None
            if not pack_sku:
                continue
            sku_str = str(pack_sku).strip()
            if not sku_str:
                continue
            normalized = sku_str.split('-')[0] if '-' in sku_str else sku_str
            pack_names[normalized] = str(pack_name).strip() if pack_name is not None else ''
        return pack_names
    except Exception:
        return {}

def _load_pack_titles_map(excel_path: str) -> dict:
    """Load {normalized_pack_sku -> Title} using openpyxl (B=SKU, AI=Title)."""
    try:
        from openpyxl import load_workbook
    except Exception:
        return {}
    try:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        ws = wb.active
        pack_titles = {}
        # Column AI = 35 (1-based), so index 34 (0-based)
        for row in ws.iter_rows(min_row=2, max_col=35, values_only=True):
            pack_sku = row[1]  # Column B
            pack_title = row[34] if len(row) > 34 else None  # Column AI
            if not pack_sku:
                continue
            sku_str = str(pack_sku).strip()
            if not sku_str:
                continue
            normalized = sku_str.split('-')[0] if '-' in sku_str else sku_str
            pack_titles[normalized] = str(pack_title).strip() if pack_title is not None else ''
        return pack_titles
    except Exception:
        return {}
