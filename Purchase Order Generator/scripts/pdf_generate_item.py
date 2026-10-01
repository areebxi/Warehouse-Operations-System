"""Render one packing-list CSV row onto a PDF (single or pack)."""
from __future__ import annotations

import pandas as pd

from pdf_btc_product import _lookup_product_details
from pdf_constants import COLUMN_NAMES
from pdf_generate_helpers import _safe_add_single_page


def render_slip_item(
    pdf,
    item,
    *,
    products_df,
    export_by_uid,
    packs_components_map,
    pack_names_map,
    pack_titles_map,
    item_count: int,
    total_items_in_order: int,
) -> None:
    sku = item.get(COLUMN_NAMES["sku"])
    linked_sku = item.get("Linked SKU", "") if "Linked SKU" in item else ""
    components_str = (
        item.get(COLUMN_NAMES["components"], "")
        if COLUMN_NAMES["components"] in item
        else ""
    )
    colours_str = (
        item.get(COLUMN_NAMES["component_colours"], "")
        if COLUMN_NAMES["component_colours"] in item
        else ""
    )
    lookup_sku = linked_sku if linked_sku else sku

    print(f"     - Item {item_count}/{total_items_in_order}, SKU: {sku}")
    if linked_sku and linked_sku != sku:
        print(f"       Using linked SKU for product lookup: {linked_sku}")
    if not sku or pd.isna(sku):
        return

    components = []
    if isinstance(components_str, str) and components_str.strip():
        components = [c.strip() for c in components_str.split(",") if c.strip()]

    if not components:
        normalized_pack_lookup = str(sku).split("-")[0] if sku and "-" in str(sku) else str(sku)
        pack_entries = packs_components_map.get(str(normalized_pack_lookup).strip(), [])
        if pack_entries:
            components = [str(e.get("sku", "")).strip() for e in pack_entries if e.get("sku")]
            if not (isinstance(colours_str, str) and colours_str.strip()):
                colours_str = ",".join(str(e.get("colour", "") or "") for e in pack_entries)

    normalized_pack = str(sku).split("-")[0] if sku and "-" in str(sku) else str(sku)
    pack_name_value = pack_names_map.get(normalized_pack, "")
    pack_title_value = pack_titles_map.get(normalized_pack, "")

    if components:
        component_products = []
        for comp_sku in components:
            comp_details = _lookup_product_details(products_df, comp_sku, export_by_uid)
            if not comp_details:
                print(f"       Warning: Product details not found for component SKU '{comp_sku}'.")
            component_products.append({**comp_details, COLUMN_NAMES["db_sku"]: comp_sku})

        item_dict = item.to_dict()
        item_dict[COLUMN_NAMES["component_colours"]] = colours_str
        pack_product_details = _lookup_product_details(products_df, sku, export_by_uid) or None
        add_pack_fn = getattr(pdf, "add_pack_slip", None)
        if callable(add_pack_fn):
            add_pack_fn(
                item_dict,
                component_products,
                item_count,
                total_items_in_order,
                pack_product=pack_product_details,
                pack_name=pack_name_value,
                pack_title=pack_title_value,
            )
        else:
            _safe_add_single_page(
                pdf, item.to_dict(), pack_product_details or {}, item_count, total_items_in_order
            )
        return

    product_details = _lookup_product_details(products_df, lookup_sku, export_by_uid)
    if product_details and linked_sku and linked_sku != sku:
        print(f"     Found product details using linked SKU: {lookup_sku}")
    elif not product_details:
        print(
            f"     Warning: Product details not found in database for SKU "
            f"'{lookup_sku}' (Original: {sku})."
        )
    print(f"     Looking for normalized pack: {normalized_pack}")
    print(f"     Pack name found: {pack_name_value}")
    print(f"     Pack title found: {pack_title_value}")

    add_single_fn = getattr(pdf, "add_packing_slip", None)
    if callable(add_single_fn):
        add_single_fn(
            item.to_dict(),
            product_details,
            item_count,
            total_items_in_order,
            pack_product=product_details or None,
            pack_name=pack_name_value,
            pack_title=pack_title_value,
        )
    else:
        _safe_add_single_page(pdf, item.to_dict(), product_details, item_count, total_items_in_order)
