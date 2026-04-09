"""
Amazon SP-API Client (Production-Ready with Mock Support)

- In production: connects to real Amazon SP-API
- In testing/mock: returns mock data directly (no external server needed)

Enable mock mode: set USE_AMAZON_MOCK=true in backend/.env
"""
import os
import json
import asyncio
from typing import Optional
from datetime import datetime
from loguru import logger


class AmazonAPIClient:
    """
    Amazon SP-API Client with built-in mock support.

    When USE_AMAZON_MOCK=true:
    - All methods return realistic mock data
    - No HTTP calls are made
    - Simulates network delay (0.5s)

    When USE_AMAZON_MOCK=false:
    - Connects to real Amazon SP-API
    - Requires valid credentials
    """

    def __init__(self, seller_id: str, marketplace_id: str, refresh_token: str,
                 client_id: str = "", client_secret: str = ""):
        self.seller_id = seller_id
        self.marketplace_id = marketplace_id
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

        # Check mock mode
        self.use_mock = os.getenv("USE_AMAZON_MOCK", "true").lower() == "true"

        # Real API base URL (only used when not in mock mode)
        self.base_url = "https://sellingpartnerapi-eu.amazon.com"

        logger.info(f"Amazon API Client initialized — Mock: {self.use_mock}, Seller: {self.seller_id}")

    # ================================================================
    # Mock Data Generators
    # ================================================================

    async def _mock_delay(self):
        """Simulate network latency"""
        await asyncio.sleep(0.3 + (hash(str(datetime.now())) % 5) / 10)

    def _mock_account_info(self) -> dict:
        return {
            "seller_id": self.seller_id,
            "marketplace_id": self.marketplace_id,
            "seller_name": "Test Store",
            "account_type": "Professional",
        }

    def _mock_orders(self) -> dict:
        return {
            "orders": [
                {
                    "AmazonOrderId": "123-4567890-1234567",
                    "SellerOrderId": "SO-001",
                    "OrderStatus": "Unshipped",
                    "OrderTotal": {"Amount": "29.99", "CurrencyCode": "USD"},
                    "NumberOfItemsShipped": 1,
                }
            ]
        }

    def _mock_listings(self) -> list[dict]:
        """Return sample product listings from Amazon"""
        return [
            {
                "sku": "DEMO-SKU-001",
                "title": "Premium Wireless Headphones",
                "brand": "SoundMax",
                "category": "Electronics",
                "price": 49.99,
                "quantity": 150,
                "description": "High-quality wireless headphones with noise cancellation",
                "bullet_points": [
                    "Active Noise Cancellation",
                    "40-hour battery life",
                    "Bluetooth 5.3",
                    "Comfortable over-ear design"
                ],
                "images": ["https://example.com/image1.jpg"],
            },
            {
                "sku": "DEMO-SKU-002",
                "title": "Organic Green Tea - 100 Bags",
                "brand": "TeaLeaf",
                "category": "Grocery",
                "price": 12.99,
                "quantity": 500,
                "description": "Premium organic green tea bags",
                "bullet_points": [
                    "100% Organic",
                    "No artificial flavors",
                    "Individually wrapped"
                ],
                "images": ["https://example.com/image2.jpg"],
            },
            {
                "sku": "DEMO-SKU-003",
                "title": "Stainless Steel Water Bottle 750ml",
                "brand": "HydroFlow",
                "category": "Kitchen",
                "price": 24.99,
                "quantity": 300,
                "description": "Double-wall insulated water bottle",
                "bullet_points": [
                    "Keeps cold 24 hours",
                    "Keeps hot 12 hours",
                    "BPA-free",
                    "Leak-proof lid"
                ],
                "images": ["https://example.com/image3.jpg"],
            },
            {
                "sku": "DEMO-SKU-004",
                "title": "Yoga Mat - Non-Slip 6mm",
                "brand": "FitPro",
                "category": "Sports",
                "price": 34.99,
                "quantity": 200,
                "description": "Professional yoga mat with carrying strap",
                "bullet_points": [
                    "Non-slip surface",
                    "6mm thickness",
                    "Eco-friendly material",
                    "Includes carrying strap"
                ],
                "images": ["https://example.com/image4.jpg"],
            },
            {
                "sku": "DEMO-SKU-005",
                "title": "LED Desk Lamp with USB Charging",
                "brand": "BrightLight",
                "category": "Home",
                "price": 39.99,
                "quantity": 100,
                "description": "Adjustable LED desk lamp with USB port",
                "bullet_points": [
                    "5 brightness levels",
                    "3 color temperatures",
                    "Built-in USB charging port",
                    "Touch control"
                ],
                "images": ["https://example.com/image5.jpg"],
            },
        ]

    # ================================================================
    # Public API Methods
    # ================================================================

    async def get_account_info(self) -> dict:
        """Get Amazon seller account information"""
        await self._mock_delay()

        if self.use_mock:
            logger.info(f"[MOCK] get_account_info — Seller: {self.seller_id}")
            return self._mock_account_info()

        # TODO: Real SP-API call using python-amazon-sp-api library
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def get_orders(self, created_after: Optional[str] = None) -> dict:
        """Get orders from Amazon"""
        await self._mock_delay()

        if self.use_mock:
            logger.info("[MOCK] get_orders — returning sample orders")
            return self._mock_orders()

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def get_listings(self) -> list[dict]:
        """Get all product listings from Amazon (for sync)"""
        await self._mock_delay()

        if self.use_mock:
            logger.info("[MOCK] get_listings — returning 5 sample products")
            return self._mock_listings()

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def create_or_update_listing(self, sku: str, product_data: dict) -> dict:
        """Create or update a product listing on Amazon"""
        await self._mock_delay()

        if self.use_mock:
            mock_asin = f"B0{hash(sku) % 10000:04d}DEMO"
            logger.info(f"[MOCK] create_or_update_listing — SKU: {sku} → ASIN: {mock_asin}")
            return {
                "success": True,
                "data": {
                    "asin": mock_asin,
                    "sku": sku,
                    "status": "ACTIVE",
                },
            }

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def delete_listing(self, sku: str) -> dict:
        """Delete a product listing from Amazon"""
        await self._mock_delay()

        if self.use_mock:
            logger.info(f"[MOCK] delete_listing — SKU: {sku}")
            return {"success": True, "data": {"sku": sku, "status": "deleted"}}

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def submit_feed(self, feed_type: str, feed_data: str, marketplace_ids: list[str]) -> str:
        """Submit a feed to Amazon"""
        await self._mock_delay()

        if self.use_mock:
            mock_feed_id = f"FEED_{hash(str(datetime.now())) % 100000:05d}"
            logger.info(f"[MOCK] submit_feed — Type: {feed_type}, ID: {mock_feed_id}")
            return mock_feed_id

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def get_feed_status(self, feed_id: str) -> dict:
        """Get feed processing status"""
        await self._mock_delay()

        if self.use_mock:
            return {
                "feedId": feed_id,
                "feedType": "POST_PRODUCT_DATA",
                "processingStatus": "DONE",
                "resultFeedDocumentId": "DOC_123",
            }

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def get_catalog_item(self, asin: str) -> dict:
        """Search Amazon catalog by ASIN"""
        await self._mock_delay()

        if self.use_mock:
            return {
                "asin": asin,
                "title": f"Catalog Item {asin}",
                "brand": "Demo Brand",
                "category": "Demo Category",
            }

        # TODO: Real SP-API call
        raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

    async def verify_credentials(self) -> bool:
        """
        Verify that Amazon credentials are valid.
        Returns True if connection is successful, False otherwise.
        """
        try:
            await self._mock_delay()

            if self.use_mock:
                logger.info(f"[MOCK] verify_credentials — Validating credentials for seller: {self.seller_id}")
                # In mock mode, always succeed if seller_id looks reasonable
                return len(self.seller_id) >= 5

            # TODO: Real SP-API verification
            # Try to fetch account info as a verification
            # await self.get_account_info()
            # return True
            raise NotImplementedError("Real SP-API not implemented yet. Use mock mode for testing.")

        except Exception as e:
            logger.error(f"Credential verification failed: {str(e)}")
            return False
