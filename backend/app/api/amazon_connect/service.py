"""
Amazon SP-API Verification Service
Handles credential verification and connection testing
"""
from loguru import logger
from app.services.amazon_api import AmazonAPIClient


class AmazonConnectionService:
    """Service for verifying Amazon SP-API connections"""

    async def verify_connection(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        seller_id: str,
        marketplace_id: str = "ARBP9OOSHTCHU",
    ) -> bool:
        """
        Test Amazon SP-API connection with provided credentials.

        Returns True if credentials are valid and connection works.
        Returns False if connection fails for any reason.
        """
        try:
            client = AmazonAPIClient(
                seller_id=seller_id,
                marketplace_id=marketplace_id,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
            )

            # Verify credentials
            is_valid = await client.verify_credentials()

            if is_valid:
                logger.info(f"Amazon connection verified for seller: {seller_id}")
            else:
                logger.warning(f"Amazon credential verification failed for seller: {seller_id}")

            return is_valid

        except Exception as e:
            logger.error(f"Amazon connection verification failed: {str(e)}")
            return False

    async def test_sync(self, seller_id: str, marketplace_id: str, refresh_token: str) -> dict:
        """
        Test the sync functionality by fetching a small sample of products.
        Returns a dict with test results.
        """
        try:
            client = AmazonAPIClient(
                seller_id=seller_id,
                marketplace_id=marketplace_id,
                refresh_token=refresh_token,
            )

            listings = await client.get_listings()
            return {
                "success": True,
                "sample_count": len(listings),
                "first_sku": listings[0]["sku"] if listings else None,
            }
        except Exception as e:
            logger.error(f"Sync test failed: {str(e)}")
            return {"success": False, "error": str(e)}


amazon_service = AmazonConnectionService()
