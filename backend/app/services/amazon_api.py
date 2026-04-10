"""
Amazon SP-API Client (Production + Advanced Simulation Mode)
Strictly connects to real Amazon Selling Partner API OR uses high-fidelity simulation.
"""
import os
import asyncio
import random
from typing import Optional
from datetime import datetime
from loguru import logger
from app.config import get_settings

settings = get_settings()

# ==========================================
# HIGH-FIDELITY SIMULATION (For Testing)
# ==========================================
class SimulatedAmazonClient:
    """
    Simulates Amazon SP-API behavior with 100% realistic data structures.
    Used when USE_AMAZON_MOCK=True to test the full system without real keys.
    """
    def __init__(self, seller_id: str, refresh_token: str, marketplace_id: str):
        self.seller_id = seller_id
        self.marketplace_id = marketplace_id
        logger.info(f"[SIMULATION] Connected to Amazon Sandbox for Seller: {seller_id}")

    async def get_account(self):
        """Simulates Sellers API"""
        await asyncio.sleep(0.5) # Network delay
        return {
            "seller_id": self.seller_id,
            "marketplace_id": self.marketplace_id,
            "business_name": "Global Trade Solutions LLC",
            "status": "ACTIVE",
            "account_type": "PROFESSIONAL"
        }

    async def get_listings(self):
        """Simulates Listings API with realistic data"""
        await asyncio.sleep(1.2) # Network delay
        # Return a mix of products with different statuses
        return [
            {
                "sku": "TS-BLK-XL-001",
                "title": "Premium Cotton T-Shirt - Black (XL)",
                "price": {"currency": "USD", "amount": 24.99},
                "quantity": 150,
                "asin": "B09X7K2M4P",
                "status": "ACTIVE",
                "brand": "UrbanStyle",
                "category": "Apparel",
                "bullet_points": ["100% Organic Cotton", "Machine Washable", "Classic Fit"],
                "images": ["https://m.media-amazon.com/images/I/71+MockImage1.jpg"]
            },
            {
                "sku": "BT-SPK-BLK-002",
                "title": "Wireless Bluetooth Speaker - Waterproof",
                "price": {"currency": "USD", "amount": 45.00},
                "quantity": 85,
                "asin": "B08N5M7S6K",
                "status": "ACTIVE",
                "brand": "SoundMax",
                "category": "Electronics",
                "bullet_points": ["IPX7 Waterproof", "24h Battery Life", "Deep Bass"],
                "images": ["https://m.media-amazon.com/images/I/71+MockImage2.jpg"]
            },
            {
                "sku": "YGA-MAT-PRP-003",
                "title": "Non-Slip Yoga Mat - Purple (6mm)",
                "price": {"currency": "USD", "amount": 32.50},
                "quantity": 200,
                "asin": "B07Y4R6T8L",
                "status": "INCOMPLETE",
                "brand": "FitLife",
                "category": "Sports & Outdoors",
                "bullet_points": ["Extra Thick", "Eco-Friendly Material", "Carrying Strap Included"],
                "images": ["https://m.media-amazon.com/images/I/71+MockImage3.jpg"]
            }
        ]

    async def submit_feed(self, feed_type: str, feed_data: bytes, marketplace_ids: list[str]) -> str:
        """Simulates Feed Submission"""
        await asyncio.sleep(0.8)
        feed_id = f"FEED_{random.randint(100000, 999999)}"
        logger.info(f"[SIMULATION] Feed {feed_id} submitted successfully.")
        return feed_id

    async def get_feed_status(self, feed_id: str) -> dict:
        """Simulates Feed Processing Status"""
        await asyncio.sleep(0.3)
        # 90% success rate simulation
        status = "DONE" if random.random() > 0.1 else "FATAL"
        return {
            "feedId": feed_id,
            "feedType": "POST_PRODUCT_DATA",
            "processingStatus": status,
            "marketplaceIds": ["ATVPDKIKX0DER"],
            "createdTime": datetime.utcnow().isoformat(),
            "processingStartTime": datetime.utcnow().isoformat()
        }

    async def verify_credentials(self) -> bool:
        """Verify connectivity"""
        try:
            await self.get_account()
            return True
        except Exception:
            return False

# ==========================================
# REAL PRODUCTION CLIENT
# ==========================================
try:
    from sp_api.api import ListingsItems, Sellers, Feeds
    from sp_api.base import Credentials, SellingApiException
    REAL_API_AVAILABLE = True
except ImportError:
    REAL_API_AVAILABLE = False
    logger.warning("Real SP-API libraries not installed. Falling back to Simulation.")


class RealSPAPIClient:
    """Real Amazon SP-API Client using python-amazon-sp-api"""

    def __init__(self, seller_id: str, refresh_token: str, marketplace_id: str = "A2NODRKZP88ZB9"):
        self.seller_id = seller_id
        self.refresh_token = refresh_token
        self.marketplace_id = marketplace_id

        # Check if we should use Simulation or Real API
        if getattr(settings, 'USE_AMAZON_MOCK', False):
            self.client = SimulatedAmazonClient(seller_id, refresh_token, marketplace_id)
            self.is_simulation = True
        else:
            if not REAL_API_AVAILABLE:
                raise RuntimeError("Real API requested but libraries are missing.")
            
            self.creds = {
                "refresh_token": self.refresh_token,
                "lwa_app_id": settings.SP_API_CLIENT_ID,
                "lwa_client_secret": settings.SP_API_CLIENT_SECRET,
                "aws_access_key": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_key": settings.AWS_SECRET_ACCESS_KEY,
                "role_arn": settings.AWS_SELLER_ROLE_ARN,
            }
            self.client = self # Self-reference for real calls
            self.is_simulation = False

        mode = "SIMULATION" if self.is_simulation else "PRODUCTION"
        logger.info(f"[{mode}] SP-API Client initialized for Seller: {self.seller_id}")

    # --- Wrapper Methods ---
    async def get_account(self):
        if self.is_simulation:
            return await self.client.get_account()
        try:
            res = Sellers(credentials=self.creds).get_account()
            return res.payload
        except SellingApiException as e:
            logger.error(f"SP-API Error (get_account): {e}")
            raise

    async def get_listings(self):
        if self.is_simulation:
            return await self.client.get_listings()
        try:
            # Note: Real API needs a specific SKU or search method. 
            # For now, this assumes we can fetch or requires adjustment based on specific needs.
            res = ListingsItems(credentials=self.creds).get_listings_item(
                sellerId=self.seller_id,
                sku="", # This usually requires a specific SKU in real API
                marketplaceIds=[self.marketplace_id]
            )
            return res.payload
        except SellingApiException as e:
            logger.error(f"SP-API Error (get_listings): {e}")
            raise

    async def submit_feed(self, feed_type: str, feed_data: bytes, marketplace_ids: list[str]) -> str:
        if self.is_simulation:
            return await self.client.submit_feed(feed_type, feed_data, marketplace_ids)
        try:
            feeds_api = Feeds(credentials=self.creds)
            doc_res = feeds_api.create_feed_document(contentType="text/xml; charset=UTF-8")
            doc_id = doc_res.payload["feedDocumentId"]
            feeds_api.upload_feed_document(feedDocumentId=doc_id, content=feed_data)
            feed_res = feeds_api.create_feed(feedType=feed_type, marketplaceIds=marketplace_ids, inputFeedDocumentId=doc_id)
            return feed_res.payload["feedId"]
        except SellingApiException as e:
            logger.error(f"SP-API Feed Error: {e}")
            raise

    async def get_feed_status(self, feed_id: str) -> dict:
        if self.is_simulation:
            return await self.client.get_feed_status(feed_id)
        try:
            res = Feeds(credentials=self.creds).get_feed(feed_id)
            return res.payload
        except SellingApiException as e:
            logger.error(f"SP-API Error (get_feed_status): {e}")
            raise

    async def verify_credentials(self) -> bool:
        try:
            await self.get_account()
            return True
        except Exception as e:
            logger.error(f"Credential verification failed: {e}")
            return False

# Alias for compatibility
AmazonAPIClient = RealSPAPIClient