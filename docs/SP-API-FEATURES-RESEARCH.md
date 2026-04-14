# SP-API Features Research Report

> **Source:** Amazon Selling Partner API (SP-API) Documentation  
> **Date:** 2026-04-14  
> **Scope:** 18 practical features across 8 categories

---

## Feature #1: Search & Retrieve Product Listings
- **Level:** Simple
- **Description:** Search and retrieve all active product listings for a seller with filtering by SKU, status, and marketplace.
- **Endpoint:** `GET /listings/2021-08-01/items`
- **Method:** GET
- **Required Roles:** `Product Listing`
- **Implementation Steps:**
  1. Obtain SP-API credentials (LWA token + AWS SigV4)
  2. Call `searchListingsItems` with `sellerId`, `marketplaceIds`, and optional `skus` filter
  3. Parse response for listing details (SKU, status, attributes)
  4. Handle pagination with `nextToken` if results exceed page size
- **Code Example:**
```python
from sp_api.api import Listings

listings = Listings()
response = listings.get_listings_item(
    sellerId="A1EXAMPLE",
    marketplaceIds=["ATVPDKIKX0DER"],
    skus=["SKU-001", "SKU-002"],
    pageSize=10
)
for item in response.payload.get("items", []):
    print(f"SKU: {item['sku']}, Status: {item['status']}")
```
- **Use Case:** A seller wants to view all their current listings to audit product information, pricing, and inventory status.

---

## Feature #2: Create or Update a Product Listing
- **Level:** Simple
- **Description:** Create a new product listing or fully update an existing one with title, description, images, and attributes.
- **Endpoint:** `PUT /listings/2021-08-01/items/{sellerId}/{sku}`
- **Method:** PUT
- **Required Roles:** `Product Listing`
- **Implementation Steps:**
  1. Validate listing data against Amazon's schema
  2. Call `putListingsItem` with `sellerId`, `sku`, `marketplaceIds`, and `attributes`
  3. Include required attributes: `item_name`, `description`, `brand`, `product_type`
  4. Handle response to confirm creation/update success
- **Code Example:**
```python
from sp_api.api import Listings

listings = Listings()
response = listings.put_listings_item(
    sellerId="A1EXAMPLE",
    sku="NEW-SKU-001",
    marketplaceIds=["ATVPDKIKX0DER"],
    body={
        "productType": "LUGGAGE",
        "attributes": {
            "item_name": [{"value": "Premium Travel Bag", "language_tag": "en_US"}],
            "description": [{"value": "Durable travel bag with multiple compartments", "language_tag": "en_US"}],
            "brand": [{"value": "MyBrand"}]
        }
    }
)
print(f"Status: {response.payload['status']}")
```
- **Use Case:** A seller adds a new product to their catalog or updates an existing listing with new images/description.

---

## Feature #3: Partial Update of Product Listing
- **Level:** Simple
- **Description:** Partially update specific attributes of a product listing without replacing the entire listing.
- **Endpoint:** `PATCH /listings/2021-08-01/items/{sellerId}/{sku}`
- **Method:** PATCH
- **Required Roles:** `Product Listing`
- **Implementation Steps:**
  1. Identify which attributes need updating (e.g., price, quantity)
  2. Call `patchListingsItem` with only the fields to update
  3. Use `issues` array in response to check for validation errors
- **Code Example:**
```python
from sp_api.api import Listings

listings = Listings()
response = listings.patch_listings_item(
    sellerId="A1EXAMPLE",
    sku="SKU-001",
    marketplaceIds=["ATVPDKIKX0DER"],
    body={
        "patches": [
            {"op": "replace", "path": "/attributes/price", "value": [{"value": "29.99", "currency": "USD"}]}
        ]
    }
)
```
- **Use Case:** A seller wants to update only the price or quantity of a product without touching other attributes.

---

## Feature #4: Delete a Product Listing
- **Level:** Simple
- **Description:** Remove a product listing from Amazon's marketplace.
- **Endpoint:** `DELETE /listings/2021-08-01/items/{sellerId}/{sku}`
- **Method:** DELETE
- **Required Roles:** `Product Listing`
- **Implementation Steps:**
  1. Verify the SKU exists and is safe to delete
  2. Call `deleteListingsItem` with `sellerId`, `sku`, and `marketplaceIds`
  3. Confirm deletion via response status
- **Code Example:**
```python
from sp_api.api import Listings

listings = Listings()
response = listings.delete_listings_item(
    sellerId="A1EXAMPLE",
    sku="OLD-SKU-001",
    marketplaceIds=["ATVPDKIKX0DER"]
)
print(f"Deletion status: {response.payload['status']}")
```
- **Use Case:** A seller discontinues a product and wants to remove it from their Amazon store.

---

## Feature #5: Search Amazon Catalog by Keyword or Identifier
- **Level:** Simple
- **Description:** Search the Amazon catalog for products by keyword, ASIN, UPC, EAN, or ISBN.
- **Endpoint:** `GET /catalog/2022-04-01/items`
- **Method:** GET
- **Required Roles:** `Product Listing`
- **Implementation Steps:**
  1. Choose search method: keyword, identifiers (ASIN/UPC/EAN/ISBN), or both
  2. Call `searchCatalogItems` with `marketplaceIds` and search parameters
  3. Parse returned items for ASIN, title, brand, and images
  4. Use pagination token if more results exist
- **Code Example:**
```python
from sp_api.api import CatalogItems

catalog = CatalogItems()
response = catalog.search_catalog_items(
    marketplaceIds=["ATVPDKIKX0DER"],
    keywords="wireless headphones",
    includedData=["summaries", "images"]
)
for item in response.payload.get("items", []):
    print(f"ASIN: {item['asin']}, Title: {item['summaries'][0]['title']}")
```
- **Use Case:** A seller wants to find existing Amazon catalog products before creating a new listing or to check competitor products.

---

## Feature #6: Get Catalog Item Details by ASIN
- **Level:** Simple
- **Description:** Retrieve detailed information about a specific product in the Amazon catalog using its ASIN.
- **Endpoint:** `GET /catalog/2022-04-01/items/{asin}`
- **Method:** GET
- **Required Roles:** `Product Listing`
- **Implementation Steps:**
  1. Obtain the ASIN of the product
  2. Call `getCatalogItem` with `asin`, `marketplaceIds`, and `includedData`
  3. Request desired data: `summaries`, `images`, `dimensions`, `identifiers`
- **Code Example:**
```python
from sp_api.api import CatalogItems

catalog = CatalogItems()
response = catalog.get_catalog_item(
    asin="B08N5WRWNW",
    marketplaceIds=["ATVPDKIKX0DER"],
    includedData=["summaries", "images", "dimensions", "identifiers"]
)
item = response.payload
print(f"Title: {item['summaries'][0]['title']}")
print(f"Brand: {item['summaries'][0]['brand']}")
```
- **Use Case:** A seller looks up a competitor's product to understand its attributes, dimensions, and branding.

---

## Feature #7: Get Competitive Pricing for a Product
- **Level:** Medium
- **Description:** Retrieve competitive pricing data for a product, including buy box price, list price, and competitor offers.
- **Endpoint:** `GET /products/pricing/v0/competitivePrice`
- **Method:** GET
- **Required Roles:** `Pricing`
- **Implementation Steps:**
  1. Identify products by ASIN or SKU
  2. Call `getCompetitivePricing` with `MarketplaceId` and `Asins` or `Skus`
  3. Parse response for competitive prices, number of offers, and buy box eligibility
  4. Compare your price against competitors
- **Code Example:**
```python
from sp_api.api import ProductPricing

pricing = ProductPricing()
response = pricing.get_competitive_pricing(
    MarketplaceId="ATVPDKIKX0DER",
    Asins=["B08N5WRWNW", "B07XJ8C8F5"]
)
for product in response.payload:
    comp_price = product.get("CompetitivePricing", {})
    print(f"ASIN: {product['ASIN']}")
    print(f"Buy Box Price: ${comp_price.get('CompetitivePrice', {}).get('Price', {}).get('Amount')}")
    print(f"Total Offers: {comp_price.get('NumberOfOfferListings', {}).get('OfferCount', 0)}")
```
- **Use Case:** A seller wants to adjust their pricing to be competitive and win the buy box.

---

## Feature #8: Batch Get Offers for Multiple Products
- **Level:** Medium
- **Description:** Retrieve offers for multiple ASINs or listings in a single batch request to reduce API calls.
- **Endpoint:** `POST /products/pricing/v0/itemsOffers/batch` or `POST /products/pricing/v0/listings/items/offers/batch`
- **Method:** POST
- **Required Roles:** `Pricing`
- **Implementation Steps:**
  1. Build batch request with up to 20 ASINs/SKUs per call
  2. Call `getItemOffersBatch` or `getListingOffersBatch`
  3. Parse batched responses for each product's offers
  4. Handle individual request errors within the batch
- **Code Example:**
```python
from sp_api.api import ProductPricing

pricing = ProductPricing()
response = pricing.get_item_offers_batch(
    body={
        "requests": [
            {
                "uri": "/products/pricing/v0/items/B08N5WRWNW/offers",
                "method": "GET",
                "headers": {"MarketplaceId": "ATVPDKIKX0DER"},
                "queryParams": {"ItemCondition": "New", "CustomerType": "Consumer"}
            },
            {
                "uri": "/products/pricing/v0/items/B07XJ8C8F5/offers",
                "method": "GET",
                "headers": {"MarketplaceId": "ATVPDKIKX0DER"},
                "queryParams": {"ItemCondition": "New"}
            }
        ]
    }
)
for result in response.payload.get("responses", []):
    print(f"Status: {result.get('status')}, Offers: {result.get('body', {}).get('Offers', [])}")
```
- **Use Case:** A seller with many products wants to check all their offers in one call instead of making individual requests.

---

## Feature #9: Get Estimated Fees for a Product
- **Level:** Simple
- **Description:** Estimate the fees Amazon will charge for selling a specific product (referral fees, FBA fees, closing fees).
- **Endpoint:** `POST /products/fees/v0/listings/{sellerSku}/feesEstimate` or `POST /products/fees/v0/items/{asin}/feesEstimate`
- **Method:** POST
- **Required Roles:** `Pricing`
- **Implementation Steps:**
  1. Build fee estimate request with `PriceToEstimateFees`, `Identifier`, and `FeesEstimateRequest`
  2. Call `getMyFeesEstimateForSKU` or `getMyFeesEstimateForASIN`
  3. Parse response for `ReferralFee`, `FBAFee`, `ClosingFee`, and total fees
- **Code Example:**
```python
from sp_api.api import ProductFees

fees = ProductFees()
response = fees.get_my_fees_estimate_for_asin(
    Asin="B08N5WRWNW",
    body={
        "FeesEstimateRequest": {
            "Identifier": "request-001",
            "PriceToEstimateFees": {
                "ListingPrice": {"CurrencyCode": "USD", "Amount": 29.99},
                "Shipping": {"CurrencyCode": "USD", "Amount": 0},
                "Points": {"PointsNumber": 0}
            },
            "IsAmazonFulfilled": True
        }
    }
)
estimate = response.payload.get("FeesEstimateResult", {}).get("FeesEstimate", {})
print(f"Total Fees: ${estimate.get('TotalFeesEstimate', {}).get('Amount')}")
print(f"Referral Fee: ${estimate.get('FeeBreakdown', {}).get('ReferralFee', {}).get('Amount')}")
```
- **Use Case:** A seller wants to calculate profit margins before setting a product price.

---

## Feature #10: Get FBA Inventory Summaries
- **Level:** Simple
- **Description:** Retrieve inventory summaries for products stored in Amazon's fulfillment centers (FBA).
- **Endpoint:** `GET /fba/inventory/v1/summaries`
- **Method:** GET
- **Required Roles:** `Inventory and Order Tracking`
- **Implementation Steps:**
  1. Call `getInventorySummaries` with `marketplaceIds`
  2. Optionally filter by `sellerSkus` (up to 50 SKUs) or `startDateTime` for changes since a date
  3. Parse response for `fulfillableQuantity`, `inboundWorkingQuantity`, `reservedQuantity`
- **Code Example:**
```python
from sp_api.api import FbaInventory

inventory = FbaInventory()
response = inventory.get_inventory_summaries(
    marketplaceIds=["ATVPDKIKX0DER"],
    sellerSkus=["SKU-001", "SKU-002"],
    granularityType="Marketplace",
    granularityId="ATVPDKIKX0DER"
)
for item in response.payload.get("inventorySummaries", []):
    print(f"SKU: {item['sku']}")
    print(f"Fulfillable: {item['quantitySummary']['fulfillableQuantity']}")
    print(f"Reserved: {item['quantitySummary']['reservedQuantity']}")
```
- **Use Case:** A seller using FBA wants to check stock levels across fulfillment centers to plan reorders.

---

## Feature #11: Retrieve Orders with Filters
- **Level:** Simple
- **Description:** Get a list of orders filtered by date, status, or marketplace.
- **Endpoint:** `GET /orders/v0/orders`
- **Method:** GET
- **Required Roles:** `Amazon Shipping`
- **Implementation Steps:**
  1. Call `getOrders` with `MarketplaceIds` and optional filters: `CreatedAfter`, `OrderStatuses`, `LastUpdatedAfter`
  2. Parse response for order details: `OrderId`, `OrderStatus`, `PurchaseDate`, `Total`
  3. Handle pagination with `NextToken`
- **Code Example:**
```python
from sp_api.api import Orders

orders_api = Orders()
response = orders_api.get_orders(
    MarketplaceIds=["ATVPDKIKX0DER"],
    CreatedAfter="2026-04-01T00:00:00Z",
    OrderStatuses=["Unshipped", "PartiallyShipped"]
)
for order in response.payload.get("Orders", []):
    print(f"Order ID: {order['AmazonOrderId']}")
    print(f"Status: {order['OrderStatus']}, Total: ${order['OrderTotal']['Amount']}")
```
- **Use Case:** A seller wants to see all unshipped orders from the past week to prepare shipments.

---

## Feature #12: Get Order Details and Buyer Info
- **Level:** Simple
- **Description:** Retrieve detailed information for a specific order including buyer info and shipping address.
- **Endpoint:** `GET /orders/v0/orders/{orderId}`, `GET /orders/v0/orders/{orderId}/buyerInfo`, `GET /orders/v0/orders/{orderId}/address`
- **Method:** GET
- **Required Roles:** `Amazon Shipping`
- **Implementation Steps:**
  1. Call `getOrder` with `orderId` for basic order details
  2. Call `getOrderBuyerInfo` for buyer email and name
  3. Call `getOrderAddress` for shipping address
  4. Call `getOrderItems` for line items in the order
- **Code Example:**
```python
from sp_api.api import Orders

orders_api = Orders()
order_id = "123-4567890-1234567"

# Get order details
order = orders_api.get_order(order_id)
print(f"Status: {order.payload['OrderStatus']}")

# Get buyer info
buyer = orders_api.get_order_buyer_info(order_id)
print(f"Buyer: {buyer.payload['BuyerName']}")

# Get order items
items = orders_api.get_order_items(order_id)
for item in items.payload.get("OrderItems", []):
    print(f"  SKU: {item['SellerSKU']}, Qty: {item['QuantityOrdered']}")
```
- **Use Case:** A seller needs to review an order's details, buyer contact, and items before packing and shipping.

---

## Feature #13: Confirm Shipment for an Order
- **Level:** Medium
- **Description:** Confirm that an order has been shipped with carrier details and tracking number.
- **Endpoint:** `POST /orders/v0/orders/{orderId}/shipmentConfirmation`
- **Method:** POST
- **Required Roles:** `Amazon Shipping`
- **Implementation Steps:**
  1. Gather shipment details: carrier code, tracking number, ship date
  2. Call `confirmShipment` with `orderId` and shipment body
  3. Include `packageDetail` with tracking info for each package
  4. Verify confirmation response
- **Code Example:**
```python
from sp_api.api import Orders

orders_api = Orders()
order_id = "123-4567890-1234567"

response = orders_api.confirm_shipment(
    order_id,
    body={
        "packageDetail": {
            "packageReferenceId": "PKG001",
            "carrierCode": "UPS",
            "trackingNumber": "1Z999AA10123456784",
            "shipDate": "2026-04-14T10:00:00Z"
        },
        "marketplaceId": "ATVPDKIKX0DER"
    }
)
print(f"Shipment confirmed: {response.payload}")
```
- **Use Case:** A seller ships an order and wants to update Amazon with tracking info so the buyer receives notification.

---

## Feature #14: Update Shipment Status
- **Level:** Simple
- **Description:** Update the shipment status of an order (e.g., from unshipped to shipped).
- **Endpoint:** `POST /orders/v0/orders/{orderId}/shipment`
- **Method:** POST
- **Required Roles:** `Amazon Shipping`
- **Implementation Steps:**
  1. Determine new shipment status: `SHIPPED`, `CANCELLED`, etc.
  2. Call `updateShipmentStatus` with `orderId` and `marketplaceId`
  3. Status transitions follow Amazon's defined state machine
- **Code Example:**
```python
from sp_api.api import Orders

orders_api = Orders()
order_id = "123-4567890-1234567"

response = orders_api.update_shipment_status(
    order_id,
    marketplaceId="ATVPDKIKX0DER",
    marketplaceId="ATVPDKIKX0DER"
)
# Note: Status is inferred by the API based on previous state
print(f"Status updated")
```
- **Use Case:** A seller marks an order as shipped in their system and wants to sync the status with Amazon.

---

## Feature #15: Create a Sales Report
- **Level:** Medium
- **Description:** Request a report (e.g., sales, inventory, orders) to be generated by Amazon.
- **Endpoint:** `POST /reports/2021-06-30/reports`
- **Method:** POST
- **Required Roles:** `Brand Analytics` or `Inventory and Order Tracking`
- **Implementation Steps:**
  1. Choose report type (e.g., `GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL`, `GET_SALES_AND_TRAFFIC_REPORT_1`)
  2. Call `createReport` with `reportType`, `marketplaceIds`, and optional `dataStartTime`/`dataEndTime`
  3. Poll `getReport` to check status until `DONE`
  4. Call `getReportDocument` to download the report file
- **Code Example:**
```python
from sp_api.api import Reports
import time

reports_api = Reports()

# Create report
response = reports_api.create_report(
    body={
        "reportType": "GET_SALES_AND_TRAFFIC_REPORT_1",
        "marketplaceIds": ["ATVPDKIKX0DER"],
        "dataStartTime": "2026-04-01T00:00:00Z",
        "dataEndTime": "2026-04-14T00:00:00Z"
    }
)
report_id = response.payload["reportId"]

# Poll until done
while True:
    status = reports_api.get_report(report_id)
    if status.payload["processingStatus"] == "DONE":
        doc_id = status.payload["reportDocumentId"]
        document = reports_api.get_report_document(doc_id)
        download_url = document.payload["url"]
        print(f"Report ready: {download_url}")
        break
    elif status.payload["processingStatus"] == "FATAL":
        print("Report generation failed")
        break
    time.sleep(30)
```
- **Use Case:** A seller wants to generate a weekly sales and traffic report to analyze performance.

---

## Feature #16: Schedule Recurring Reports
- **Level:** Medium
- **Description:** Set up automated recurring reports (daily, weekly, monthly) so reports are generated on a schedule.
- **Endpoint:** `POST /reports/2021-06-30/schedules`
- **Method:** POST
- **Required Roles:** `Brand Analytics` or `Inventory and Order Tracking`
- **Implementation Steps:**
  1. Choose report type and schedule frequency (e.g., `PT24H` for every 24 hours)
  2. Call `createReportSchedule` with `reportType`, `marketplaceIds`, and `period`
  3. Amazon generates reports automatically per schedule
  4. Use `getReportSchedules` to list active schedules
- **Code Example:**
```python
from sp_api.api import Reports

reports_api = Reports()
response = reports_api.create_report_schedule(
    body={
        "reportType": "GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL",
        "marketplaceIds": ["ATVPDKIKX0DER"],
        "period": "P7D",  # Every 7 days
        "nextReportCreationTime": "2026-04-21T00:00:00Z"
    }
)
schedule_id = response.payload["reportScheduleId"]
print(f"Scheduled report created: {schedule_id}")
```
- **Use Case:** A seller wants weekly inventory reports generated automatically without manual requests.

---

## Feature #17: Subscribe to Order Notifications
- **Level:** Advanced
- **Description:** Set up real-time notifications when orders are created, canceled, or updated.
- **Endpoint:** `POST /notifications/v1/subscriptions/{notificationType}`, `POST /notifications/v1/destinations`
- **Method:** POST
- **Required Roles:** `Amazon Shipping` (for `ANY_OFFER_CHANGED`, `ORDER_CHANGE`, etc.)
- **Implementation Steps:**
  1. Create a destination (SQS queue or EventBridge) to receive notifications
  2. Call `createDestination` with destination details
  3. Call `createSubscription` with `notificationType` (e.g., `ORDER_CHANGE`) and `destinationId`
  4. Handle incoming notifications at your endpoint
- **Code Example:**
```python
from sp_api.api import Notifications

notifications = Notifications()

# Step 1: Create destination (SQS)
dest_response = notifications.create_destination(
    body={
        "name": "OrderNotifications",
        "resourceSpecification": {
            "sqs": {
                "arn": "arn:aws:sqs:us-east-1:123456789012:order-notifications"
            }
        }
    }
)
destination_id = dest_response.payload["destinationId"]

# Step 2: Subscribe to order change notifications
sub_response = notifications.create_subscription(
    notificationType="ORDER_CHANGE",
    body={
        "payloadVersion": "1.0",
        "destinationId": destination_id
    }
)
print(f"Subscription ID: {sub_response.payload['subscriptionId']}")
```
- **Use Case:** A seller wants real-time alerts when new orders arrive or order status changes, enabling faster fulfillment.

---

## Feature #18: Get Sales Performance Metrics
- **Level:** Medium
- **Description:** Retrieve order metrics for sales performance analysis (units ordered, revenue) filtered by date and marketplace.
- **Endpoint:** `GET /sales/v1/orderMetrics`
- **Method:** GET
- **Required Roles:** `Brand Analytics`
- **Implementation Steps:**
  1. Call `getOrderMetrics` with `marketplaceIds`, `interval` (date range), and `granularity` (day/week/month)
  2. Optionally filter by `asin`, `sku`, or `orderStatus`
  3. Parse response for `unitCount`, `orderItemCount`, `totalSales`
- **Code Example:**
```python
from sp_api.api import Sales

sales = Sales()
response = sales.get_order_metrics(
    marketplaceIds=["ATVPDKIKX0DER"],
    interval="2026-04-01T00:00:00Z--2026-04-14T00:00:00Z",
    granularity="Day",
    orderStatus="Shipped"
)
for metric in response.payload:
    print(f"Date: {metric['interval']}")
    print(f"  Units: {metric['unitCount']}")
    print(f"  Orders: {metric['orderItemCount']}")
    print(f"  Revenue: ${metric['totalSales']['Amount']}")
```
- **Use Case:** A seller wants to track daily sales performance over the past two weeks to identify trends.

---

## Feature #19: Send Product Review Solicitation to Buyer
- **Level:** Simple
- **Description:** Automatically send a product review and seller feedback solicitation to a buyer after their order is delivered.
- **Endpoint:** `POST /solicitations/v1/orders/{amazonOrderId}/solicitations/productReviewAndSellerFeedback`
- **Method:** POST
- **Required Roles:** `Customer Support` (Messaging)
- **Implementation Steps:**
  1. Verify order is eligible for solicitation
  2. Call `createProductReviewAndSellerFeedbackSolicitation` with `amazonOrderId` and `marketplaceIds`
  3. Amazon sends the solicitation email to the buyer
  4. Check response for success or errors
- **Code Example:**
```python
from sp_api.api import Solicitations

solicitations = Solicitations()
response = solicitations.create_product_review_and_seller_feedback_solicitation(
    amazon_order_id="123-4567890-1234567",
    marketplaceIds=["ATVPDKIKX0DER"]
)
print(f"Solicitation sent: {response.payload}")
```
- **Use Case:** A seller wants to automatically request reviews from buyers to improve their product ratings.

---

## Feature #20: Purchase Shipping Labels via Buy Shipping
- **Level:** Advanced
- **Description:** Purchase shipping labels for orders using Amazon's Buy Shipping Services with eligible carriers and rates.
- **Endpoint:** `POST /mfn/v0/shipmentServices`, `POST /mfn/v0/shipments`
- **Method:** POST
- **Required Roles:** `Shipping`
- **Implementation Steps:**
  1. Call `getEligibleShipmentServices` with order details to get available carriers and rates
  2. Select a shipping service offer ID
  3. Call `createShipment` with the selected offer ID and shipment details
  4. Receive shipping label (PDF) and tracking number
  5. Print label and attach to package
- **Code Example:**
```python
from sp_api.api import MerchantFulfillment

mfn = MerchantFulfillment()

# Step 1: Get eligible shipping services
eligible = mfn.get_eligible_shipment_services(
    body={
        "ShipFromAddress": {
            "Name": "My Store",
            "AddressLine1": "123 Main St",
            "City": "Seattle",
            "StateOrProvinceCode": "WA",
            "PostalCode": "98101",
            "CountryCode": "US",
            "Email": "store@example.com",
            "Phone": "206-555-0100"
        },
        "PackageDimensions": {"Length": 10, "Width": 8, "Height": 6, "Unit": "inches"},
        "Weight": {"Value": 2, "Unit": "lb"},
        "ShippingServiceOptions": {"DeliveryExperience": "NoTracking"}
    }
)

# Step 2: Create shipment with selected offer
offer_id = eligible.payload["ShippingServiceList"][0]["ShippingServiceOfferId"]
shipment = mfn.create_shipment(
    body={
        "ShippingServiceOfferId": offer_id,
        "ShipFromAddress": {...}  # Same as above
    }
)
label_url = shipment.payload["Shipment"]["ShipmentItems"][0]["LabelDownloadURL"]
tracking = shipment.payload["Shipment"]["TrackingId"]
print(f"Label: {label_url}, Tracking: {tracking}")
```
- **Use Case:** A seller wants to purchase and print shipping labels directly from their application instead of using Seller Central.

---

## Summary Table

| # | Feature | Level | Category | Endpoint |
|---|---------|-------|----------|----------|
| 1 | Search Product Listings | Simple | Listings | `GET /listings/2021-08-01/items` |
| 2 | Create/Update Listing | Simple | Listings | `PUT /listings/2021-08-01/items/{sellerId}/{sku}` |
| 3 | Partial Update Listing | Simple | Listings | `PATCH /listings/2021-08-01/items/{sellerId}/{sku}` |
| 4 | Delete Listing | Simple | Listings | `DELETE /listings/2021-08-01/items/{sellerId}/{sku}` |
| 5 | Search Catalog | Simple | Catalog | `GET /catalog/2022-04-01/items` |
| 6 | Get Catalog Item by ASIN | Simple | Catalog | `GET /catalog/2022-04-01/items/{asin}` |
| 7 | Get Competitive Pricing | Medium | Pricing | `GET /products/pricing/v0/competitivePrice` |
| 8 | Batch Get Offers | Medium | Pricing | `POST /products/pricing/v0/itemsOffers/batch` |
| 9 | Get Estimated Fees | Simple | Pricing | `POST /products/fees/v0/items/{asin}/feesEstimate` |
| 10 | Get FBA Inventory | Simple | Inventory | `GET /fba/inventory/v1/summaries` |
| 11 | Retrieve Orders | Simple | Orders | `GET /orders/v0/orders` |
| 12 | Get Order Details | Simple | Orders | `GET /orders/v0/orders/{orderId}` |
| 13 | Confirm Shipment | Medium | Orders | `POST /orders/v0/orders/{orderId}/shipmentConfirmation` |
| 14 | Update Shipment Status | Simple | Orders | `POST /orders/v0/orders/{orderId}/shipment` |
| 15 | Create Sales Report | Medium | Reports | `POST /reports/2021-06-30/reports` |
| 16 | Schedule Recurring Reports | Medium | Reports | `POST /reports/2021-06-30/schedules` |
| 17 | Subscribe to Notifications | Advanced | Notifications | `POST /notifications/v1/subscriptions/{type}` |
| 18 | Get Sales Metrics | Medium | Sales | `GET /sales/v1/orderMetrics` |
| 19 | Send Review Solicitation | Simple | Messaging | `POST /solicitations/v1/orders/{orderId}/...` |
| 20 | Purchase Shipping Labels | Advanced | Shipping | `POST /mfn/v0/shipments` |

---

## Required SP-API Roles Summary

| Role | Features Using It |
|------|-------------------|
| `Product Listing` | Features 1-6 (Listings, Catalog) |
| `Pricing` | Features 7-9 (Pricing, Fees) |
| `Inventory and Order Tracking` | Features 10, 15-16 (Inventory, Reports) |
| `Amazon Shipping` | Features 11-14, 17 (Orders, Notifications) |
| `Brand Analytics` | Features 15-16, 18 (Reports, Sales) |
| `Customer Support` (Messaging) | Feature 19 (Solicitations) |
| `Shipping` | Feature 20 (Merchant Fulfillment) |

---

## Implementation Notes

1. **Authentication:** All SP-API calls require LWA (Login with Amazon) access tokens and AWS Signature Version 4 signing.
2. **Rate Limits:** Each endpoint has throttling limits (requests per second and burst capacity). Implement retry logic with exponential backoff.
3. **Marketplace IDs:** Each marketplace has a unique ID (e.g., `ATVPDKIKX0DER` for US). Always include the correct marketplace ID.
4. **Pagination:** Many endpoints return `nextToken` for paginated results. Loop through all pages for complete data.
5. **Error Handling:** Handle common errors: `400` (bad request), `403` (unauthorized), `429` (rate limited), `500` (server error).
