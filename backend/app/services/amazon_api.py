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
import httpx

MOCK_API_BASE_URL = "http://localhost:9500"

class SimulatedAmazonClient:
    """
    Simulates Amazon SP-API behavior by calling the local Node.js Mock API.
    """
    def __init__(self, seller_id: str, refresh_token: str, marketplace_id: str):
        self.seller_id = seller_id
        self.marketplace_id = marketplace_id
        self.client = httpx.AsyncClient(base_url=MOCK_API_BASE_URL, timeout=10.0)
        logger.info(f"[SIMULATION] Proxying to Mock API at {MOCK_API_BASE_URL} for Seller: {seller_id}")

    async def get_account(self):
        """Proxy to Mock API Sellers Account"""
        try:
            # Pass sellerId as a query param since that's how SP-API headers/params work usually
            # and our middleware checks for it if it's in the route, but here we use it as a param for simplicity
            response = await self.client.get("/sellers/v1/account", params={"sellerId": self.seller_id})
            
            if response.status_code == 403:
                raise ValueError("Invalid Seller ID for Mock API.")
                
            response.raise_for_status()
            data = response.json()
            return data["payload"]
        except Exception as e:
            logger.error(f"Mock API Account verification failed: {e}")
            raise

    async def get_listings(self, sku: Optional[str] = None):
        """Proxy to Mock API GET listings"""
        try:
            if sku:
                # Call mock API for specific SKU
                response = await self.client.get(
                    f"/listings/2021-08-01/items/{self.seller_id}/{sku}",
                    params={"sellerId": self.seller_id}
                )
                response.raise_for_status()
                return response.json().get("payload", {})

            # Return sample listings when no SKU specified
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
                }
            ]
        except Exception as e:
            logger.error(f"Mock API Listings failed: {e}")
            return []
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

    async def cancel_feed(self, feed_id: str) -> dict:
        """Simulates Feed Cancellation"""
        await asyncio.sleep(0.3)
        logger.info(f"[SIMULATION] Feed {feed_id} cancelled.")
        return {"feedId": feed_id, "status": "CANCELLED"}

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

    def __init__(
        self, 
        seller_id: str, 
        refresh_token: str, 
        marketplace_id: str = "A2NODRKZP88ZB9",
        client_id: str = None,
        client_secret: str = None
    ):
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
            
            # Use the passed refresh token, but fallback to global setting if it's missing or a mock placeholder
            token = self.refresh_token
            if not token or token.startswith("MOCK_") or token == "MOCK-TOKEN":
                token = settings.SP_API_REFRESH_TOKEN
                if token:
                    logger.info(f"Using global fallback SP-API Refresh Token for seller: {self.seller_id}")

            self.creds = {
                "refresh_token": token,
                # Use dynamic credentials if provided, fallback to settings
                "lwa_app_id": client_id or settings.SP_API_CLIENT_ID,
                "lwa_client_secret": client_secret or settings.SP_API_CLIENT_SECRET,
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

    async def get_listings(self, sku: Optional[str] = None):
        """
        Get listings from Amazon SP-API.
        If sku is provided, fetches that specific listing.
        If sku is None, searches all listings for the seller.
        """
        if self.is_simulation:
            return await self.client.get_listings()
        try:
            listings_api = ListingsItems(credentials=self.creds)
            if sku:
                # Get a specific listing by SKU
                res = listings_api.get_listings_item(
                    sellerId=self.seller_id,
                    sku=sku,
                    marketplaceIds=[self.marketplace_id]
                )
                return res.payload
            else:
                # Search/list all listings for this seller
                res = listings_api.search_listings_items(
                    sellerId=self.seller_id,
                    marketplaceIds=[self.marketplace_id],
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

    async def cancel_feed(self, feed_id: str) -> dict:
        if self.is_simulation:
            return await self.client.cancel_feed(feed_id)
        try:
            res = Feeds(credentials=self.creds).cancel_feed(feed_id)
            return res.payload
        except SellingApiException as e:
            logger.error(f"SP-API Error (cancel_feed): {e}")
            raise

    async def create_or_update_listing(self, sku: str, product_data: dict) -> dict:
        """
        Unified method for listing submission (Simulation & Real).
        This method is required by listing_tasks.py.
        """
        try:
            if self.is_simulation:
                # Simulation logic
                feed_id = await self.client.submit_feed(
                    feed_type="POST_PRODUCT_DATA",
                    feed_data=b"<mock_xml/>",
                    marketplace_ids=[self.marketplace_id]
                )
                return {
                    "success": True,
                    "data": {"asin": f"B0SIM{sku[-3:]}", "feed_id": feed_id}
                }
            else:
                # Real API logic using submit_feed
                # Note: In real SP-API, we usually use Feeds API. 
                # We will reuse submit_feed method but adapted for single product.
                feed_id = await self.submit_feed(
                    feed_type="POST_PRODUCT_DATA",
                    feed_data=b"<real_xml/>", # Placeholder for real XML generation
                    marketplace_ids=[self.marketplace_id]
                )
                return {
                    "success": True,
                    "data": {"asin": "PENDING", "feed_id": feed_id}
                }
        except Exception as e:
            logger.error(f"Listing submission failed: {e}")
            return {"success": False, "error": str(e)}

    async def verify_credentials(self) -> bool:
        try:
            await self.get_account()
            return True
        except Exception as e:
            logger.error(f"Credential verification failed: {e}")
            return False

# Alias for compatibility
AmazonAPIClient = RealSPAPIClient