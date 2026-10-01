from __future__ import annotations
import pandas as pd
from fpdf import FPDF
from pathlib import Path
from datetime import date
from app_paths import APP_ROOT, asset_path, data_path, packs_database_path, product_database_path, tag_output_dir

def generate_packing_slips():
    """Main function to load data and generate PDFs based on Process Number."""
    print("\n🚀 Starting packing slip generation...")

    try:
        orders_df = pd.read_csv(PLAIN_ITEMS_CSV, dtype={COLUMN_NAMES['sku']: str, COLUMN_NAMES['process']: str})
        products_df = pd.read_excel(PRODUCT_DATABASE_FILE, dtype={COLUMN_NAMES['db_sku']: str, COLUMN_NAMES['product_code']: str})
        # Load Pack Names and Titles maps via openpyxl
        pack_names_map = _load_pack_names_map(PACKS_DATABASE_FILE)
        pack_titles_map = _load_pack_titles_map(PACKS_DATABASE_FILE)
        export_by_uid = _load_btc_product_data_by_uid()
        
        products_df = products_df.drop_duplicates(subset=[COLUMN_NAMES['db_sku']], keep='first')
        products_df = products_df.set_index(COLUMN_NAMES['db_sku'])
        
        print(f"✅ Loaded {len(orders_df)} order items and {len(products_df)} products.")
    except FileNotFoundError as e:
        print(f"\n❌ FATAL ERROR: Required file not found. Please check paths.\n    Details: {e}")
        return
    except KeyError as e:
        print(f"\n❌ FATAL ERROR: A required column is missing from a file.\n    Column Name: {e}")
        return
    except Exception as e:
        print(f"\n❌ FATAL ERROR: An unexpected error occurred during file loading: {e}")
        return
    
    orders_df = orders_df.sort_values(by=COLUMN_NAMES['process'])
    
    grouped_by_process = orders_df.groupby(COLUMN_NAMES['process'])

    for process_number, process_df in grouped_by_process:
        print(f"\n--- 🏭 Processing Group: {process_number} ---")
        
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=MARGIN)

        grouped_orders = process_df.groupby(COLUMN_NAMES['order_id'], sort=False)

        for order_id, items_in_order in grouped_orders:
            total_items_in_order = len(items_in_order)
            print(f"   📦 Processing Order {order_id} ({total_items_in_order} item(s))...")

            for item_count, (_, item) in enumerate(items_in_order.iterrows(), 1):
                sku = item.get(COLUMN_NAMES['sku'])
                print(f"     - Item {item_count}/{total_items_in_order}, SKU: {sku}")

                if not sku or pd.isna(sku):
                    continue

                product_details = _lookup_product_details(products_df, sku, export_by_uid)
                if not product_details:
                    print(f"     ⚠️ Warning: Product details not found in database for SKU '{sku}'.")
                
                normalized_pack = str(sku).split('-')[0] if sku and '-' in str(sku) else str(sku)
                pack_name_value = pack_names_map.get(normalized_pack, '')
                pack_title_value = pack_titles_map.get(normalized_pack, '')
                pdf.add_packing_slip(item.to_dict(), product_details, item_count, total_items_in_order, pack_product=product_details, pack_name=pack_name_value, pack_title=pack_title_value)

        try:
            pdf_output_folder = tag_output_dir("pdf_output")
            today_str = date.today().strftime("%Y-%m-%d")
            date_folder = pdf_output_folder / today_str
            date_folder.mkdir(parents=True, exist_ok=True)
            
            actual_process_id = str(process_number).split()[-1]
            output_filename = date_folder / f"{actual_process_id}.pdf"
            
            pdf.output(str(output_filename))
            print(f"   🎉 Success! PDF for process '{process_number}' generated at: {output_filename.resolve()}")
        except Exception as e:
            print(f"\n   ❌ FATAL ERROR: Could not save the PDF for process '{process_number}'. Is the file open elsewhere?\n   Reason: {e}")

    print("\n\n✅ All PDF files have been generated successfully!")
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
def _resolve_product_image_path(
    product_filename: object,
    sku_value: object,
    *,
    colour_img_by_uid: dict[str, str] | None = None,
) -> tuple[Path | None, str, str]:
    """Prefer colour-specific BTC Product Data shot, then Database product image, then SKU.ext."""
    sku_str = str(sku_value or "").strip()
    colour_map = (
        colour_img_by_uid
        if colour_img_by_uid is not None
        else _load_colour_image_basenames_by_uid()
    )
    colour01 = colour_map.get(sku_str, "") if sku_str else ""
    if colour01:
        colour_path = PRODUCT_IMAGE_FOLDER / colour01
        if colour_path.exists():
            return colour_path, "colour_image_01", colour01
    if product_filename:
        pf = PRODUCT_IMAGE_FOLDER / str(product_filename)
        if pf.exists():
            return pf, "product_image", str(product_filename)
    if sku_str:
        for ext in (".jpg", ".png", ".jpeg", ".webp"):
            candidate = PRODUCT_IMAGE_FOLDER / f"{sku_str}{ext}"
            if candidate.exists():
                return candidate, "sku_fallback", candidate.name
    return None, "none", ""
def _load_colour_image_basenames_by_uid() -> dict[str, str]:
    """UID -> colour image 01 basename from BTC Product Data (colour-specific product shot)."""
    global _COLOUR_IMAGE_BY_UID_CACHE
    if _COLOUR_IMAGE_BY_UID_CACHE is not None:
        return _COLOUR_IMAGE_BY_UID_CACHE
    out: dict[str, str] = {}
    try:
        export_df, _encoding = _read_btc_product_data_csv(
            usecols=["UID", "colour image 01"],
            dtype={"UID": str},
        )
    except Exception:
        _COLOUR_IMAGE_BY_UID_CACHE = out
        return out
    if "UID" not in export_df.columns or "colour image 01" not in export_df.columns:
        _COLOUR_IMAGE_BY_UID_CACHE = out
        return out
    export_df = export_df[~export_df["UID"].astype(str).str.startswith("[", na=False)]
    export_df = export_df.drop_duplicates(subset=["UID"], keep="first")
    for _, row in export_df.iterrows():
        uid = str(row.get("UID", "")).strip()
        name = _image_filename_from_url(row.get("colour image 01"))
        if uid and name:
            out[uid] = name
    _COLOUR_IMAGE_BY_UID_CACHE = out
    return out
def _image_filename_from_url(url: object) -> str:
    """Extract image filename from a BTC Product Data URL for assets/product_images lookup."""
    if url is None or (isinstance(url, float) and pd.isna(url)):
        return ""
    s = str(url).strip()
    if not s or s.startswith("["):
        return ""
    return Path(s.replace("\\", "/")).name
