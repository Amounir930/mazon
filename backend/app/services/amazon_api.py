"""
Amazon SP-API Client (Production-Ready with Mock Support)
يدعم الاتصال بـ Amazon الحقيقي أو الـ Mock Server للاختبار
"""
import httpx
import os
from typing import Optional
from datetime import datetime
from loguru import logger
from app.config import get_settings

settings = get_settings()

class AmazonAPIClient:
    """
    Amazon SP-API Client
    - في الإنتاج: يتصل بـ Amazon SP-API الحقيقي
    - في الاختبار: يتصل بالـ Mock Server على localhost:9000
    """

    def __init__(self, seller_id: str, marketplace_id: str, refresh_token: str):
        self.seller_id = seller_id
        self.marketplace_id = marketplace_id
        self.refresh_token = refresh_token

        # تحديد إذا كنا هنستخدم Mock ولا الحقيقي
        self.use_mock = os.getenv("USE_AMAZON_MOCK", "true").lower() == "true"
        self.base_url = (
            "http://localhost:9500" if self.use_mock
            else f"https://sellingpartnerapi-eu.amazon.com"
        )

        logger.info(f"Amazon API Client initialized - Mock: {self.use_mock}")

    async def create_or_update_listing(self, sku: str, product_data: dict) -> dict:
        """إنشاء أو تحديث منتج على Amazon"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.base_url}/listings/2021-08-01/items/{self.seller_id}/{sku}",
                    json={
                        "productType": "PRODUCT",
                        "attributes": {
                            "item_name": [{"value": product_data.get("name", ""), "language_tag": "en_US"}],
                            "brand": [{"value": product_data.get("brand", ""), "language_tag": "en_US"}],
                            "product_description": [{"value": product_data.get("description", ""), "language_tag": "en_US"}],
                            "bullet_point": [{"value": bp, "language_tag": "en_US"} for bp in product_data.get("bullet_points", [])],
                        },
                    },
                    headers=self._get_headers(),
                )

                if response.status_code in [200, 201]:
                    logger.info(f"Listing created/updated: {sku}")
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(f"Failed to create listing {sku}: {response.text}")
                    return {"success": False, "error": response.json()}

        except httpx.TimeoutException:
            logger.error(f"Timeout creating listing: {sku}")
            return {"success": False, "error": {"code": "Timeout", "message": "Request timed out"}}
        except Exception as e:
            logger.error(f"Error creating listing {sku}: {str(e)}")
            return {"success": False, "error": {"code": "Unknown", "message": str(e)}}

    async def delete_listing(self, sku: str) -> dict:
        """حذف منتج من Amazon"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/listings/2021-08-01/items/{self.seller_id}/{sku}",
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    logger.info(f"Listing deleted: {sku}")
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.json()}

        except Exception as e:
            logger.error(f"Error deleting listing {sku}: {str(e)}")
            return {"success": False, "error": {"code": "Unknown", "message": str(e)}}

    async def submit_feed(self, feed_type: str, feed_data: str, marketplace_ids: list[str]) -> str:
        """إرسال Feed إلى Amazon"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Create feed document
                doc_response = await client.post(
                    f"{self.base_url}/feeds/2021-06-30/documents",
                    json={"contentType": "text/xml; charset=UTF-8"},
                    headers=self._get_headers(),
                )

                if doc_response.status_code not in [200, 201]:
                    raise Exception(f"Failed to create feed document: {doc_response.text}")

                document_id = doc_response.json()["feedDocumentId"]

                # Step 2: Submit feed
                feed_response = await client.post(
                    f"{self.base_url}/feeds/2021-06-30/feeds",
                    json={
                        "feedType": feed_type,
                        "marketplaceIds": marketplace_ids,
                        "inputFeedDocumentId": document_id,
                    },
                    headers=self._get_headers(),
                )

                if feed_response.status_code in [200, 201, 202]:
                    feed_id = feed_response.json()["feedId"]
                    logger.info(f"Feed submitted: {feed_id}")
                    return feed_id
                else:
                    raise Exception(f"Failed to submit feed: {feed_response.text}")

        except Exception as e:
            logger.error(f"Error submitting feed: {str(e)}")
            raise

    async def get_feed_status(self, feed_id: str) -> dict:
        """جلب حالة Feed"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/feeds/2021-06-30/feeds/{feed_id}",
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to get feed status: {response.text}")

        except Exception as e:
            logger.error(f"Error getting feed status: {str(e)}")
            raise

    async def get_catalog_item(self, asin: str) -> dict:
        """البحث في كتالوج Amazon"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/catalog/2022-04-01/items/{asin}",
                    params={"marketplaceId": self.marketplace_id},
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to get catalog item: {response.text}")

        except Exception as e:
            logger.error(f"Error getting catalog item: {str(e)}")
            raise

    async def get_orders(self, created_after: Optional[str] = None) -> dict:
        """جلب الطلبات"""
        try:
            params = {}
            if created_after:
                params["createdAfter"] = created_after

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/seller/orders/v1/orders",
                    params=params,
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    return response.json().get("payload", {})
                else:
                    raise Exception(f"Failed to get orders: {response.text}")

        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            raise

    def _get_headers(self) -> dict:
        """HTTP Headers للتوثيق"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # في حالة الـ Mock، مش محتاجين توكينات
        if not self.use_mock:
            # TODO: إضافة AWS SigV4 signing هنا
            headers["x-amz-access-token"] = self.refresh_token

        return headers
