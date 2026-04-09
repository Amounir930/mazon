"""
Amazon SP-API Verification Service
"""
from loguru import logger
from app.services.amazon_api import AmazonAPIClient


class AmazonConnectionService:
    async def verify_connection(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        seller_id: str,
    ) -> bool:
        try:
            client = AmazonAPIClient(
                seller_id=seller_id,
                marketplace_id="ARBP9OOSHTCHU",
                refresh_token=refresh_token,
            )
            # Quick health check — get orders with no filter
            result = await client.get_orders()
            if result is not None:
                logger.info("Amazon connection verified")
                return True
            return False
        except Exception as e:
            logger.error(f"Amazon connection failed: {str(e)}")
            return False


amazon_service = AmazonConnectionService()
