"""CSV item-column helpers for PO ShipStation export."""

from __future__ import annotations

from typing import Dict, Optional


def _empty_item_csv_fields() -> Dict:
    fields = {
        "basic sku": "",
        "items 0 adjustment": "",
        "items 0 createDate": "",
        "items 0 fulfillmentSku": "",
        "items 0 imageUrl": "",
        "items 0 lineItemKey": "",
        "items 0 modifyDate": "",
        "items 0 name": "",
        "items 0 orderItemId": "",
        "items 0 productId": "",
        "items 0 quantity": "",
        "items 0 shippingAmount": "",
        "items 0 sku": "",
        "items 0 taxAmount": "",
        "items 0 unitPrice": "",
        "items 0 upc": "",
        "items 0 warehouseLocation": "",
        "items 0 weight": "",
    }
    for i in range(3):
        fields[f"item 0 option {i} name"] = ""
        fields[f"item 0 option {i} value"] = ""
    return fields


def item_fields_for_csv(item: Optional[Dict] = None) -> Dict:
    """CSV columns for one line item (same header names as the legacy item-0 format)."""
    if not item:
        return _empty_item_csv_fields()

    fields = {
        "basic sku": item.get("sku", ""),
        "items 0 adjustment": item.get("adjustment", ""),
        "items 0 createDate": item.get("createDate", ""),
        "items 0 fulfillmentSku": item.get("fulfillmentSku", ""),
        "items 0 imageUrl": item.get("imageUrl", ""),
        "items 0 lineItemKey": item.get("lineItemKey", ""),
        "items 0 modifyDate": item.get("modifyDate", ""),
        "items 0 name": item.get("name", ""),
        "items 0 orderItemId": item.get("orderItemId", ""),
        "items 0 productId": item.get("productId", ""),
        "items 0 quantity": item.get("quantity", ""),
        "items 0 shippingAmount": item.get("shippingAmount", ""),
        "items 0 sku": item.get("sku", ""),
        "items 0 taxAmount": item.get("taxAmount", ""),
        "items 0 unitPrice": item.get("unitPrice", ""),
        "items 0 upc": item.get("upc", ""),
        "items 0 warehouseLocation": item.get("warehouseLocation", ""),
        "items 0 weight": item.get("weight", ""),
    }
    options = item.get("options") or []
    for i in range(3):
        if i < len(options):
            option = options[i] or {}
            fields[f"item 0 option {i} name"] = option.get("name", "")
            fields[f"item 0 option {i} value"] = option.get("value", "")
        else:
            fields[f"item 0 option {i} name"] = ""
            fields[f"item 0 option {i} value"] = ""
    return fields
