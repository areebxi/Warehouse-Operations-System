"""
ShipStation order helpers for Purchase Order Generator.

HTTP reads go through ``shared.shipstation.ShipStationClient``.
CSV/JSON export stays here (PO-specific column schema).
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

_WAREHOUSE = Path(__file__).resolve().parents[2]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))

from shared.shipstation import (  # noqa: E402
    ShipStationClient,
    ShipStationCredentials,
    ShipStationError,
    load_shipstation_credentials,
)


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


class ShipStationAPI:
    """PO façade over shared ShipStationClient + local CSV/JSON export."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        *,
        base_url: str | None = None,
        client: ShipStationClient | None = None,
    ):
        if client is not None:
            self._client = client
        elif api_key and api_secret:
            creds = ShipStationCredentials(
                base_url=(base_url or "https://ssapi.shipstation.com").rstrip("/"),
                api_key=api_key,
                api_secret=api_secret,
            )
            self._client = ShipStationClient(creds)
        else:
            self._client = ShipStationClient(load_shipstation_credentials())
        self.api_key = self._client.credentials.api_key
        self.api_secret = self._client.credentials.api_secret
        self.base_url = self._client.credentials.base_url

    def get_orders_by_tag(
        self,
        tag_id: int | str,
        *,
        order_status: str = "awaiting_shipment",
        page_size: int = 500,
    ) -> List[Dict]:
        """Server-side tag filter via orders/listbytag (preferred)."""
        return self._client.list_orders_by_tag(
            int(tag_id),
            order_status=order_status,
            page_size=page_size,
        )

    def get_awaiting_dispatch_orders(
        self,
        page: int = 1,
        page_size: int = 500,
        order_date: str = None,
    ) -> List[Dict]:
        """Bulk awaiting_shipment list (prefer get_orders_by_tag when you have a tag)."""
        _ = page  # pagination handled inside client
        return self._client.list_orders(
            order_status="awaiting_shipment",
            page_size=page_size,
            order_date=order_date,
        )

    def get_shipped_orders(
        self,
        page: int = 1,
        page_size: int = 500,
        order_date: str = None,
    ) -> List[Dict]:
        _ = page
        return self._client.list_orders(
            order_status="shipped",
            page_size=page_size,
            order_date=order_date,
        )

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        try:
            return self._client.get_order(int(order_id))
        except ShipStationError as e:
            print(f"Error fetching order {order_id}: {e}")
            return None

    def export_orders_to_csv(self, orders: List[Dict], filename: str = None) -> str:
        """
        Export orders to CSV in the detailed format matching csv1.csv.

        Multi-SKU orders write one row per line item (order columns repeated).
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"awaiting_dispatch_orders_{timestamp}.csv"

        if not orders:
            print("No orders to export")
            return None

        fieldnames = [
            "orderNumber",
            "advancedOptions billToAccount",
            "advancedOptions billToCountryCode",
            "advancedOptions billToMyOtherAccount",
            "advancedOptions billToParty",
            "advancedOptions billToPostalCode",
            "advancedOptions containsAlcohol",
            "advancedOptions customField1",
            "advancedOptions customField2",
            "advancedOptions customField3",
            "advancedOptions mergedOrSplit",
            "advancedOptions nonMachinable",
            "advancedOptions parentId",
            "advancedOptions saturdayDelivery",
            "advancedOptions source",
            "advancedOptions storeId",
            "advancedOptions warehouseId",
            "amountPaid",
            "basic sku",
            "billTo addressVerified",
            "billTo city",
            "billTo company",
            "billTo country",
            "billTo name",
            "billTo phone",
            "billTo postalCode",
            "billTo residential",
            "billTo state",
            "billTo street1",
            "billTo street2",
            "billTo street3",
            "carrierCode",
            "confirmation",
            "createDate",
            "customerEmail",
            "customerId",
            "customerNotes",
            "customerUsername",
            "dimensions",
            "dimensions height",
            "dimensions length",
            "dimensions units",
            "dimensions width",
            "externallyFulfilled",
            "externallyFulfilledBy",
            "externallyFulfilledById",
            "externallyFulfilledByName",
            "gift",
            "giftMessage",
            "holdUntilDate",
            "insuranceOptions insureShipment",
            "insuranceOptions insuredValue",
            "insuranceOptions provider",
            "internalNotes",
            "internationalOptions contents",
            "internationalOptions customsItems",
            "internationalOptions nonDelivery",
            "item 0 option 0 name",
            "item 0 option 0 value",
            "item 0 option 1 name",
            "item 0 option 1 value",
            "item 0 option 2 name",
            "item 0 option 2 value",
            "items 0 adjustment",
            "items 0 createDate",
            "items 0 fulfillmentSku",
            "items 0 imageUrl",
            "items 0 lineItemKey",
            "items 0 modifyDate",
            "items 0 name",
            "items 0 orderItemId",
            "items 0 productId",
            "items 0 quantity",
            "items 0 shippingAmount",
            "items 0 sku",
            "items 0 taxAmount",
            "items 0 unitPrice",
            "items 0 upc",
            "items 0 warehouseLocation",
            "items 0 weight",
            "labelMessages",
            "modifyDate",
            "orderDate",
            "orderId",
            "orderKey",
            "orderStatus",
            "orderTotal",
            "packageCode",
            "paymentDate",
            "paymentMethod",
            "requestedShippingService",
            "serviceCode",
            "shipByDate",
            "shipDate",
            "shipTo addressVerified",
            "shipTo city",
            "shipTo company",
            "shipTo country",
            "shipTo name",
            "shipTo phone",
            "shipTo postalCode",
            "shipTo residential",
            "shipTo state",
            "shipTo street1",
            "shipTo street2",
            "shipTo street3",
            "shippingAmount",
            "tagIds",
            "taxAmount",
            "userId",
            "weight WeightUnits",
            "weight units",
            "weight value",
        ]

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for order in orders:
                flattened_order = {}

                flattened_order["orderNumber"] = order.get("orderNumber", "")
                flattened_order["orderId"] = order.get("orderId", "")
                flattened_order["orderKey"] = order.get("orderKey", "")
                flattened_order["orderStatus"] = order.get("orderStatus", "")
                flattened_order["orderDate"] = order.get("orderDate", "")
                flattened_order["createDate"] = order.get("createDate", "")
                flattened_order["modifyDate"] = order.get("modifyDate", "")
                flattened_order["orderTotal"] = order.get("orderTotal", "")
                flattened_order["amountPaid"] = order.get("amountPaid", "")
                flattened_order["taxAmount"] = order.get("taxAmount", "")
                flattened_order["shippingAmount"] = order.get("shippingAmount", "")
                flattened_order["customerEmail"] = order.get("customerEmail", "")
                flattened_order["customerId"] = order.get("customerId", "")
                flattened_order["customerNotes"] = order.get("customerNotes", "")
                flattened_order["customerUsername"] = order.get("customerUsername", "")
                flattened_order["internalNotes"] = order.get("internalNotes", "")
                flattened_order["gift"] = order.get("gift", "")
                flattened_order["giftMessage"] = order.get("giftMessage", "")
                flattened_order["paymentMethod"] = order.get("paymentMethod", "")
                flattened_order["paymentDate"] = order.get("paymentDate", "")
                flattened_order["requestedShippingService"] = order.get(
                    "requestedShippingService", ""
                )
                flattened_order["carrierCode"] = order.get("carrierCode", "")
                flattened_order["serviceCode"] = order.get("serviceCode", "")
                flattened_order["packageCode"] = order.get("packageCode", "")
                flattened_order["confirmation"] = order.get("confirmation", "")
                flattened_order["shipDate"] = order.get("shipDate", "")
                flattened_order["shipByDate"] = order.get("shipByDate", "")
                flattened_order["holdUntilDate"] = order.get("holdUntilDate", "")
                flattened_order["userId"] = order.get("userId", "")
                flattened_order["externallyFulfilled"] = order.get("externallyFulfilled", "")
                flattened_order["externallyFulfilledBy"] = order.get(
                    "externallyFulfilledBy", ""
                )
                flattened_order["externallyFulfilledById"] = order.get(
                    "externallyFulfilledById", ""
                )
                flattened_order["externallyFulfilledByName"] = order.get(
                    "externallyFulfilledByName", ""
                )
                flattened_order["labelMessages"] = order.get("labelMessages", "")
                flattened_order["tagIds"] = order.get("tagIds", "")

                bill_to = order.get("billTo") or {}
                flattened_order["billTo addressVerified"] = bill_to.get(
                    "addressVerified", ""
                )
                flattened_order["billTo city"] = bill_to.get("city", "")
                flattened_order["billTo company"] = bill_to.get("company", "")
                flattened_order["billTo country"] = bill_to.get("country", "")
                flattened_order["billTo name"] = bill_to.get("name", "")
                flattened_order["billTo phone"] = bill_to.get("phone", "")
                flattened_order["billTo postalCode"] = bill_to.get("postalCode", "")
                flattened_order["billTo residential"] = bill_to.get("residential", "")
                flattened_order["billTo state"] = bill_to.get("state", "")
                flattened_order["billTo street1"] = bill_to.get("street1", "")
                flattened_order["billTo street2"] = bill_to.get("street2", "")
                flattened_order["billTo street3"] = bill_to.get("street3", "")

                ship_to = order.get("shipTo") or {}
                flattened_order["shipTo addressVerified"] = ship_to.get(
                    "addressVerified", ""
                )
                flattened_order["shipTo city"] = ship_to.get("city", "")
                flattened_order["shipTo company"] = ship_to.get("company", "")
                flattened_order["shipTo country"] = ship_to.get("country", "")
                flattened_order["shipTo name"] = ship_to.get("name", "")
                flattened_order["shipTo phone"] = ship_to.get("phone", "")
                flattened_order["shipTo postalCode"] = ship_to.get("postalCode", "")
                flattened_order["shipTo residential"] = ship_to.get("residential", "")
                flattened_order["shipTo state"] = ship_to.get("state", "")
                flattened_order["shipTo street1"] = ship_to.get("street1", "")
                flattened_order["shipTo street2"] = ship_to.get("street2", "")
                flattened_order["shipTo street3"] = ship_to.get("street3", "")

                weight = order.get("weight") or {}
                flattened_order["weight WeightUnits"] = weight.get("WeightUnits", "")
                flattened_order["weight units"] = weight.get("units", "")
                flattened_order["weight value"] = weight.get("value", "")

                dimensions = order.get("dimensions") or {}
                flattened_order["dimensions"] = (
                    json.dumps(dimensions) if dimensions else ""
                )
                flattened_order["dimensions height"] = dimensions.get("height", "")
                flattened_order["dimensions length"] = dimensions.get("length", "")
                flattened_order["dimensions units"] = dimensions.get("units", "")
                flattened_order["dimensions width"] = dimensions.get("width", "")

                advanced_options = order.get("advancedOptions") or {}
                flattened_order["advancedOptions billToAccount"] = advanced_options.get(
                    "billToAccount", ""
                )
                flattened_order["advancedOptions billToCountryCode"] = (
                    advanced_options.get("billToCountryCode", "")
                )
                flattened_order["advancedOptions billToMyOtherAccount"] = (
                    advanced_options.get("billToMyOtherAccount", "")
                )
                flattened_order["advancedOptions billToParty"] = advanced_options.get(
                    "billToParty", ""
                )
                flattened_order["advancedOptions billToPostalCode"] = (
                    advanced_options.get("billToPostalCode", "")
                )
                flattened_order["advancedOptions containsAlcohol"] = (
                    advanced_options.get("containsAlcohol", "")
                )
                flattened_order["advancedOptions customField1"] = advanced_options.get(
                    "customField1", ""
                )
                flattened_order["advancedOptions customField2"] = advanced_options.get(
                    "customField2", ""
                )
                flattened_order["advancedOptions customField3"] = advanced_options.get(
                    "customField3", ""
                )
                flattened_order["advancedOptions mergedOrSplit"] = advanced_options.get(
                    "mergedOrSplit", ""
                )
                flattened_order["advancedOptions nonMachinable"] = advanced_options.get(
                    "nonMachinable", ""
                )
                flattened_order["advancedOptions parentId"] = advanced_options.get(
                    "parentId", ""
                )
                flattened_order["advancedOptions saturdayDelivery"] = (
                    advanced_options.get("saturdayDelivery", "")
                )
                flattened_order["advancedOptions source"] = advanced_options.get(
                    "source", ""
                )
                flattened_order["advancedOptions storeId"] = advanced_options.get(
                    "storeId", ""
                )
                flattened_order["advancedOptions warehouseId"] = advanced_options.get(
                    "warehouseId", ""
                )

                insurance_options = order.get("insuranceOptions") or {}
                flattened_order["insuranceOptions insureShipment"] = (
                    insurance_options.get("insureShipment", "")
                )
                flattened_order["insuranceOptions insuredValue"] = insurance_options.get(
                    "insuredValue", ""
                )
                flattened_order["insuranceOptions provider"] = insurance_options.get(
                    "provider", ""
                )

                international_options = order.get("internationalOptions") or {}
                flattened_order["internationalOptions contents"] = (
                    international_options.get("contents", "")
                )
                flattened_order["internationalOptions customsItems"] = (
                    json.dumps(international_options.get("customsItems", []))
                    if international_options.get("customsItems")
                    else ""
                )
                flattened_order["internationalOptions nonDelivery"] = (
                    international_options.get("nonDelivery", "")
                )

                items = order.get("items") or []
                if not items:
                    flattened_order.update(item_fields_for_csv(None))
                    writer.writerow(flattened_order)
                    continue

                for item in items:
                    row = dict(flattened_order)
                    row.update(item_fields_for_csv(item or {}))
                    writer.writerow(row)

        print(f"Orders exported to {filename}")
        return filename

    def export_orders_to_json(self, orders: List[Dict], filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"awaiting_dispatch_orders_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as jsonfile:
            json.dump(orders, jsonfile, indent=2, ensure_ascii=False, default=str)

        print(f"Orders exported to {filename}")
        return filename


def main():
    print("ShipStation Awaiting Dispatch Orders Fetcher")
    print("=" * 50)

    try:
        shipstation = ShipStationAPI()
    except Exception as e:
        print(f"Credentials error: {e}")
        print("Create config/ShipStation/.env with REAL_API_KEY / REAL_API_SECRET")
        return

    print("\nFetching awaiting dispatch orders...")
    try:
        orders = shipstation.get_awaiting_dispatch_orders()
    except ShipStationError as e:
        print(f"API error: {e}")
        return

    if not orders:
        print("No awaiting dispatch orders found.")
        return

    print(f"\nTotal orders found: {len(orders)}")
    shipstation.export_orders_to_csv(orders)
    print("\nDone!")


if __name__ == "__main__":
    main()
