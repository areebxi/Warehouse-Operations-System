import requests
import json
import csv
from datetime import datetime
import os
from typing import List, Dict, Optional


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
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize ShipStation API client
        
        Args:
            api_key: Your ShipStation API key
            api_secret: Your ShipStation API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://ssapi.shipstation.com"
        self.session = requests.Session()
        self.session.auth = (api_key, api_secret)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_awaiting_dispatch_orders(self, page: int = 1, page_size: int = 500, order_date: str = None) -> List[Dict]:
        """
        Fetch all awaiting dispatch orders from ShipStation
        
        Args:
            page: Page number to fetch (default: 1)
            page_size: Number of orders per page (default: 500, max: 500)
            order_date: Filter orders by specific date (YYYY-MM-DD format, optional)
            
        Returns:
            List of order dictionaries
        """
        all_orders = []
        current_page = page
        
        while True:
            try:
                # ShipStation API endpoint for orders
                url = f"{self.base_url}/orders"
                
                # Parameters for awaiting dispatch orders
                params = {
                    'orderStatus': 'awaiting_shipment',  # This is the status for awaiting dispatch
                    'page': current_page,
                    'pageSize': page_size,
                    'sortBy': 'OrderDate',
                    'sortDir': 'DESC'
                }
                
                # Add date filter if provided
                if order_date:
                    params['orderDate'] = order_date
                
                print(f"Fetching page {current_page}...")
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                orders = data.get('orders', [])
                
                if not orders:
                    print(f"No more orders found on page {current_page}")
                    break
                
                all_orders.extend(orders)
                print(f"Found {len(orders)} orders on page {current_page}")
                
                # Check if there are more pages
                if len(orders) < page_size:
                    break
                    
                current_page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching orders: {e}")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
        
        return all_orders
    
    def get_shipped_orders(self, page: int = 1, page_size: int = 500, order_date: str = None) -> List[Dict]:
        """
        Fetch all shipped orders from ShipStation
        
        Args:
            page: Page number to fetch (default: 1)
            page_size: Number of orders per page (default: 500, max: 500)
            order_date: Filter orders by specific date (YYYY-MM-DD format, optional)
            
        Returns:
            List of order dictionaries
        """
        all_orders = []
        current_page = page
        
        while True:
            try:
                # ShipStation API endpoint for orders
                url = f"{self.base_url}/orders"
                
                # Parameters for shipped orders
                params = {
                    'orderStatus': 'shipped',  # This is the status for shipped orders
                    'page': current_page,
                    'pageSize': page_size,
                    'sortBy': 'OrderDate',
                    'sortDir': 'DESC'
                }
                
                # Add date filter if provided
                if order_date:
                    params['orderDate'] = order_date
                
                print(f"Fetching page {current_page}...")
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                orders = data.get('orders', [])
                
                if not orders:
                    print(f"No more orders found on page {current_page}")
                    break
                
                all_orders.extend(orders)
                print(f"Found {len(orders)} orders on page {current_page}")
                
                # Check if there are more pages
                if len(orders) < page_size:
                    break
                    
                current_page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching orders: {e}")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
        
        return all_orders
    
    def get_order_details(self, order_id: int) -> Optional[Dict]:
        """
        Get detailed information for a specific order
        
        Args:
            order_id: The order ID to fetch details for
            
        Returns:
            Order details dictionary or None if error
        """
        try:
            url = f"{self.base_url}/orders/{order_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching order {order_id}: {e}")
            return None
    
    def export_orders_to_csv(self, orders: List[Dict], filename: str = None) -> str:
        """
        Export orders to CSV in the detailed format matching csv1.csv.

        Multi-SKU orders write one row per line item (order columns repeated).
        
        Args:
            orders: List of order dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to the created CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"awaiting_dispatch_orders_{timestamp}.csv"
        
        if not orders:
            print("No orders to export")
            return None
        
        # Define CSV columns matching the format from csv1.csv
        fieldnames = [
            'orderNumber',
            'advancedOptions billToAccount',
            'advancedOptions billToCountryCode', 
            'advancedOptions billToMyOtherAccount',
            'advancedOptions billToParty',
            'advancedOptions billToPostalCode',
            'advancedOptions containsAlcohol',
            'advancedOptions customField1',
            'advancedOptions customField2',
            'advancedOptions customField3',
            'advancedOptions mergedOrSplit',
            'advancedOptions nonMachinable',
            'advancedOptions parentId',
            'advancedOptions saturdayDelivery',
            'advancedOptions source',
            'advancedOptions storeId',
            'advancedOptions warehouseId',
            'amountPaid',
            'basic sku',
            'billTo addressVerified',
            'billTo city',
            'billTo company',
            'billTo country',
            'billTo name',
            'billTo phone',
            'billTo postalCode',
            'billTo residential',
            'billTo state',
            'billTo street1',
            'billTo street2',
            'billTo street3',
            'carrierCode',
            'confirmation',
            'createDate',
            'customerEmail',
            'customerId',
            'customerNotes',
            'customerUsername',
            'dimensions',
            'dimensions height',
            'dimensions length',
            'dimensions units',
            'dimensions width',
            'externallyFulfilled',
            'externallyFulfilledBy',
            'externallyFulfilledById',
            'externallyFulfilledByName',
            'gift',
            'giftMessage',
            'holdUntilDate',
            'insuranceOptions insureShipment',
            'insuranceOptions insuredValue',
            'insuranceOptions provider',
            'internalNotes',
            'internationalOptions contents',
            'internationalOptions customsItems',
            'internationalOptions nonDelivery',
            'item 0 option 0 name',
            'item 0 option 0 value',
            'item 0 option 1 name',
            'item 0 option 1 value',
            'item 0 option 2 name',
            'item 0 option 2 value',
            'items 0 adjustment',
            'items 0 createDate',
            'items 0 fulfillmentSku',
            'items 0 imageUrl',
            'items 0 lineItemKey',
            'items 0 modifyDate',
            'items 0 name',
            'items 0 orderItemId',
            'items 0 productId',
            'items 0 quantity',
            'items 0 shippingAmount',
            'items 0 sku',
            'items 0 taxAmount',
            'items 0 unitPrice',
            'items 0 upc',
            'items 0 warehouseLocation',
            'items 0 weight',
            'labelMessages',
            'modifyDate',
            'orderDate',
            'orderId',
            'orderKey',
            'orderStatus',
            'orderTotal',
            'packageCode',
            'paymentDate',
            'paymentMethod',
            'requestedShippingService',
            'serviceCode',
            'shipByDate',
            'shipDate',
            'shipTo addressVerified',
            'shipTo city',
            'shipTo company',
            'shipTo country',
            'shipTo name',
            'shipTo phone',
            'shipTo postalCode',
            'shipTo residential',
            'shipTo state',
            'shipTo street1',
            'shipTo street2',
            'shipTo street3',
            'shippingAmount',
            'tagIds',
            'taxAmount',
            'userId',
            'weight WeightUnits',
            'weight units',
            'weight value'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for order in orders:
                # Flatten nested dictionaries for CSV
                flattened_order = {}
                
                # Basic order fields
                flattened_order['orderNumber'] = order.get('orderNumber', '')
                flattened_order['orderId'] = order.get('orderId', '')
                flattened_order['orderKey'] = order.get('orderKey', '')
                flattened_order['orderStatus'] = order.get('orderStatus', '')
                flattened_order['orderDate'] = order.get('orderDate', '')
                flattened_order['createDate'] = order.get('createDate', '')
                flattened_order['modifyDate'] = order.get('modifyDate', '')
                flattened_order['orderTotal'] = order.get('orderTotal', '')
                flattened_order['amountPaid'] = order.get('amountPaid', '')
                flattened_order['taxAmount'] = order.get('taxAmount', '')
                flattened_order['shippingAmount'] = order.get('shippingAmount', '')
                flattened_order['customerEmail'] = order.get('customerEmail', '')
                flattened_order['customerId'] = order.get('customerId', '')
                flattened_order['customerNotes'] = order.get('customerNotes', '')
                flattened_order['customerUsername'] = order.get('customerUsername', '')
                flattened_order['internalNotes'] = order.get('internalNotes', '')
                flattened_order['gift'] = order.get('gift', '')
                flattened_order['giftMessage'] = order.get('giftMessage', '')
                flattened_order['paymentMethod'] = order.get('paymentMethod', '')
                flattened_order['paymentDate'] = order.get('paymentDate', '')
                flattened_order['requestedShippingService'] = order.get('requestedShippingService', '')
                flattened_order['carrierCode'] = order.get('carrierCode', '')
                flattened_order['serviceCode'] = order.get('serviceCode', '')
                flattened_order['packageCode'] = order.get('packageCode', '')
                flattened_order['confirmation'] = order.get('confirmation', '')
                flattened_order['shipDate'] = order.get('shipDate', '')
                flattened_order['shipByDate'] = order.get('shipByDate', '')
                flattened_order['holdUntilDate'] = order.get('holdUntilDate', '')
                flattened_order['userId'] = order.get('userId', '')
                flattened_order['externallyFulfilled'] = order.get('externallyFulfilled', '')
                flattened_order['externallyFulfilledBy'] = order.get('externallyFulfilledBy', '')
                flattened_order['externallyFulfilledById'] = order.get('externallyFulfilledById', '')
                flattened_order['externallyFulfilledByName'] = order.get('externallyFulfilledByName', '')
                flattened_order['labelMessages'] = order.get('labelMessages', '')
                flattened_order['tagIds'] = order.get('tagIds', '')
                
                # Bill To address
                bill_to = order.get('billTo') or {}
                flattened_order['billTo addressVerified'] = bill_to.get('addressVerified', '')
                flattened_order['billTo city'] = bill_to.get('city', '')
                flattened_order['billTo company'] = bill_to.get('company', '')
                flattened_order['billTo country'] = bill_to.get('country', '')
                flattened_order['billTo name'] = bill_to.get('name', '')
                flattened_order['billTo phone'] = bill_to.get('phone', '')
                flattened_order['billTo postalCode'] = bill_to.get('postalCode', '')
                flattened_order['billTo residential'] = bill_to.get('residential', '')
                flattened_order['billTo state'] = bill_to.get('state', '')
                flattened_order['billTo street1'] = bill_to.get('street1', '')
                flattened_order['billTo street2'] = bill_to.get('street2', '')
                flattened_order['billTo street3'] = bill_to.get('street3', '')
                
                # Ship To address
                ship_to = order.get('shipTo') or {}
                flattened_order['shipTo addressVerified'] = ship_to.get('addressVerified', '')
                flattened_order['shipTo city'] = ship_to.get('city', '')
                flattened_order['shipTo company'] = ship_to.get('company', '')
                flattened_order['shipTo country'] = ship_to.get('country', '')
                flattened_order['shipTo name'] = ship_to.get('name', '')
                flattened_order['shipTo phone'] = ship_to.get('phone', '')
                flattened_order['shipTo postalCode'] = ship_to.get('postalCode', '')
                flattened_order['shipTo residential'] = ship_to.get('residential', '')
                flattened_order['shipTo state'] = ship_to.get('state', '')
                flattened_order['shipTo street1'] = ship_to.get('street1', '')
                flattened_order['shipTo street2'] = ship_to.get('street2', '')
                flattened_order['shipTo street3'] = ship_to.get('street3', '')
                
                # Weight
                weight = order.get('weight') or {}
                flattened_order['weight WeightUnits'] = weight.get('WeightUnits', '')
                flattened_order['weight units'] = weight.get('units', '')
                flattened_order['weight value'] = weight.get('value', '')
                
                # Dimensions
                dimensions = order.get('dimensions') or {}
                flattened_order['dimensions'] = json.dumps(dimensions) if dimensions else ''
                flattened_order['dimensions height'] = dimensions.get('height', '')
                flattened_order['dimensions length'] = dimensions.get('length', '')
                flattened_order['dimensions units'] = dimensions.get('units', '')
                flattened_order['dimensions width'] = dimensions.get('width', '')
                
                # Advanced Options
                advanced_options = order.get('advancedOptions') or {}
                flattened_order['advancedOptions billToAccount'] = advanced_options.get('billToAccount', '')
                flattened_order['advancedOptions billToCountryCode'] = advanced_options.get('billToCountryCode', '')
                flattened_order['advancedOptions billToMyOtherAccount'] = advanced_options.get('billToMyOtherAccount', '')
                flattened_order['advancedOptions billToParty'] = advanced_options.get('billToParty', '')
                flattened_order['advancedOptions billToPostalCode'] = advanced_options.get('billToPostalCode', '')
                flattened_order['advancedOptions containsAlcohol'] = advanced_options.get('containsAlcohol', '')
                flattened_order['advancedOptions customField1'] = advanced_options.get('customField1', '')
                flattened_order['advancedOptions customField2'] = advanced_options.get('customField2', '')
                flattened_order['advancedOptions customField3'] = advanced_options.get('customField3', '')
                flattened_order['advancedOptions mergedOrSplit'] = advanced_options.get('mergedOrSplit', '')
                flattened_order['advancedOptions nonMachinable'] = advanced_options.get('nonMachinable', '')
                flattened_order['advancedOptions parentId'] = advanced_options.get('parentId', '')
                flattened_order['advancedOptions saturdayDelivery'] = advanced_options.get('saturdayDelivery', '')
                flattened_order['advancedOptions source'] = advanced_options.get('source', '')
                flattened_order['advancedOptions storeId'] = advanced_options.get('storeId', '')
                flattened_order['advancedOptions warehouseId'] = advanced_options.get('warehouseId', '')
                
                # Insurance Options
                insurance_options = order.get('insuranceOptions') or {}
                flattened_order['insuranceOptions insureShipment'] = insurance_options.get('insureShipment', '')
                flattened_order['insuranceOptions insuredValue'] = insurance_options.get('insuredValue', '')
                flattened_order['insuranceOptions provider'] = insurance_options.get('provider', '')
                
                # International Options
                international_options = order.get('internationalOptions') or {}
                flattened_order['internationalOptions contents'] = international_options.get('contents', '')
                flattened_order['internationalOptions customsItems'] = json.dumps(international_options.get('customsItems', [])) if international_options.get('customsItems') else ''
                flattened_order['internationalOptions nonDelivery'] = international_options.get('nonDelivery', '')
                
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
        """
        Export orders to JSON file
        
        Args:
            orders: List of order dictionaries
            filename: Output filename (optional)
            
        Returns:
            Path to the created JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"awaiting_dispatch_orders_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(orders, jsonfile, indent=2, ensure_ascii=False, default=str)
        
        print(f"Orders exported to {filename}")
        return filename

def main():
    """
    Main function to fetch and export awaiting dispatch orders
    """
    print("ShipStation Awaiting Dispatch Orders Fetcher")
    print("=" * 50)
    
    # Get API credentials
    api_key = input("Enter your ShipStation API Key: ").strip()
    api_secret = input("Enter your ShipStation API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("API credentials are required!")
        return
    
    # Initialize API client
    shipstation = ShipStationAPI(api_key, api_secret)
    
    print("\nFetching awaiting dispatch orders...")
    orders = shipstation.get_awaiting_dispatch_orders()
    
    if not orders:
        print("No awaiting dispatch orders found.")
        return
    
    print(f"\nTotal orders found: {len(orders)}")
    
    # Display summary
    print("\nOrder Summary:")
    print("-" * 30)
    for i, order in enumerate(orders[:10], 1):  # Show first 10 orders
        print(f"{i}. Order #{order.get('orderNumber', 'N/A')} - "
              f"{order.get('customerName', 'N/A')} - "
              f"${order.get('amountPaid', 0)}")
    
    if len(orders) > 10:
        print(f"... and {len(orders) - 10} more orders")
    
    # Export options
    print("\nExport Options:")
    print("1. Export to CSV")
    print("2. Export to JSON")
    print("3. Export to both")
    print("4. No export")
    
    choice = input("\nSelect export option (1-4): ").strip()
    
    if choice == "1":
        shipstation.export_orders_to_csv(orders)
    elif choice == "2":
        shipstation.export_orders_to_json(orders)
    elif choice == "3":
        shipstation.export_orders_to_csv(orders)
        shipstation.export_orders_to_json(orders)
    elif choice == "4":
        print("No export performed.")
    else:
        print("Invalid choice. No export performed.")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
