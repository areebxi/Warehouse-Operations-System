"""Flatten a ShipStation order dict into CSV row columns (without line items)."""

from __future__ import annotations

import json
from typing import Dict


def flatten_order_for_csv(order: Dict) -> Dict:
    flattened_order: Dict = {}

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
    flattened_order["requestedShippingService"] = order.get("requestedShippingService", "")
    flattened_order["carrierCode"] = order.get("carrierCode", "")
    flattened_order["serviceCode"] = order.get("serviceCode", "")
    flattened_order["packageCode"] = order.get("packageCode", "")
    flattened_order["confirmation"] = order.get("confirmation", "")
    flattened_order["shipDate"] = order.get("shipDate", "")
    flattened_order["shipByDate"] = order.get("shipByDate", "")
    flattened_order["holdUntilDate"] = order.get("holdUntilDate", "")
    flattened_order["userId"] = order.get("userId", "")
    flattened_order["externallyFulfilled"] = order.get("externallyFulfilled", "")
    flattened_order["externallyFulfilledBy"] = order.get("externallyFulfilledBy", "")
    flattened_order["externallyFulfilledById"] = order.get("externallyFulfilledById", "")
    flattened_order["externallyFulfilledByName"] = order.get("externallyFulfilledByName", "")
    flattened_order["labelMessages"] = order.get("labelMessages", "")
    flattened_order["tagIds"] = order.get("tagIds", "")

    bill_to = order.get("billTo") or {}
    flattened_order["billTo addressVerified"] = bill_to.get("addressVerified", "")
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
    flattened_order["shipTo addressVerified"] = ship_to.get("addressVerified", "")
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
    flattened_order["dimensions"] = json.dumps(dimensions) if dimensions else ""
    flattened_order["dimensions height"] = dimensions.get("height", "")
    flattened_order["dimensions length"] = dimensions.get("length", "")
    flattened_order["dimensions units"] = dimensions.get("units", "")
    flattened_order["dimensions width"] = dimensions.get("width", "")

    advanced_options = order.get("advancedOptions") or {}
    flattened_order["advancedOptions billToAccount"] = advanced_options.get("billToAccount", "")
    flattened_order["advancedOptions billToCountryCode"] = advanced_options.get(
        "billToCountryCode", ""
    )
    flattened_order["advancedOptions billToMyOtherAccount"] = advanced_options.get(
        "billToMyOtherAccount", ""
    )
    flattened_order["advancedOptions billToParty"] = advanced_options.get("billToParty", "")
    flattened_order["advancedOptions billToPostalCode"] = advanced_options.get(
        "billToPostalCode", ""
    )
    flattened_order["advancedOptions containsAlcohol"] = advanced_options.get(
        "containsAlcohol", ""
    )
    flattened_order["advancedOptions customField1"] = advanced_options.get("customField1", "")
    flattened_order["advancedOptions customField2"] = advanced_options.get("customField2", "")
    flattened_order["advancedOptions customField3"] = advanced_options.get("customField3", "")
    flattened_order["advancedOptions mergedOrSplit"] = advanced_options.get("mergedOrSplit", "")
    flattened_order["advancedOptions nonMachinable"] = advanced_options.get("nonMachinable", "")
    flattened_order["advancedOptions parentId"] = advanced_options.get("parentId", "")
    flattened_order["advancedOptions saturdayDelivery"] = advanced_options.get(
        "saturdayDelivery", ""
    )
    flattened_order["advancedOptions source"] = advanced_options.get("source", "")
    flattened_order["advancedOptions storeId"] = advanced_options.get("storeId", "")
    flattened_order["advancedOptions warehouseId"] = advanced_options.get("warehouseId", "")

    insurance_options = order.get("insuranceOptions") or {}
    flattened_order["insuranceOptions insureShipment"] = insurance_options.get(
        "insureShipment", ""
    )
    flattened_order["insuranceOptions insuredValue"] = insurance_options.get("insuredValue", "")
    flattened_order["insuranceOptions provider"] = insurance_options.get("provider", "")

    international_options = order.get("internationalOptions") or {}
    flattened_order["internationalOptions contents"] = international_options.get("contents", "")
    flattened_order["internationalOptions customsItems"] = (
        json.dumps(international_options.get("customsItems", []))
        if international_options.get("customsItems")
        else ""
    )
    flattened_order["internationalOptions nonDelivery"] = international_options.get(
        "nonDelivery", ""
    )

    return flattened_order
