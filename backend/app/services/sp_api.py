"""
Amazon SP-API Client Wrapper
Wrapper around python-amazon-sp-api for easier integration
"""
from sp_api.api import ListingsItems, Feeds
from sp_api.base import SellingApiException, Marketplaces
from sp_api.base.credentials import Credentials
from app.config import get_settings
from loguru import logger

settings = get_settings()


class SPAPIClient:
    """Amazon Selling Partner API Client Wrapper"""
    
    def __init__(self, seller_id: str, refresh_token: str):
        """
        Initialize SP-API client
        
        Args:
            seller_id: Amazon Seller ID (Merchant ID)
            refresh_token: LWA refresh token for this seller
        """
        self.seller_id = seller_id
        self.refresh_token = refresh_token
        
        # Note: In production, implement a credential manager that handles
        # token refresh automatically
        try:
            self.credentials = Credentials(
                lwa_app_id=settings.SP_API_CLIENT_ID,
                lwa_client_secret=settings.SP_API_CLIENT_SECRET,
            )
        except Exception as e:
            logger.error(f"Failed to initialize SP-API credentials: {str(e)}")
            raise
    
    def create_or_update_listing(self, sku: str, product_data: dict, marketplace_id: str) -> dict:
        """
        Create or update a product listing on Amazon
        
        Args:
            sku: Stock Keeping Unit
            product_data: Product attributes dictionary
            marketplace_id: Amazon marketplace ID
            
        Returns:
            API response dictionary
        """
        try:
            listings_api = ListingsItems(credentials=self.credentials)
            
            # Build listing payload
            body = {
                "productType": "PRODUCT",
                "requirements": "LISTING",
                "attributes": {
                    "item_name": [{"value": product_data.get("name", ""), "language_tag": "en_US"}],
                    "brand": [{"value": product_data.get("brand", ""), "language_tag": "en_US"}],
                    "product_description": [{"value": product_data.get("description", ""), "language_tag": "en_US"}],
                },
            }
            
            # Add bullet points if available
            if product_data.get("bullet_points"):
                body["attributes"]["bullet_point"] = [
                    {"value": bp, "language_tag": "en_US"}
                    for bp in product_data["bullet_points"]
                ]
            
            response = listings_api.put_listings_item(
                sellerId=self.seller_id,
                sku=sku,
                marketplaceId=marketplace_id,
                body=body,
            )
            
            logger.info(f"Listing created/updated: {sku}")
            return response.payload
            
        except SellingApiException as e:
            logger.error(f"SP-API error for SKU {sku}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating listing: {str(e)}")
            raise
    
    def submit_feed(self, feed_type: str, feed_data: bytes, marketplace_ids: list[str]) -> str:
        """
        Submit a feed to Amazon (for bulk operations)
        
        Args:
            feed_type: Type of feed (e.g., '_POST_PRODUCT_DATA_')
            feed_data: Feed content as bytes
            marketplace_ids: List of marketplace IDs
            
        Returns:
            Feed submission ID
        """
        try:
            feeds_api = Feeds(credentials=self.credentials)
            
            # Step 1: Create feed document
            doc_response = feeds_api.create_feed_document(
                contentType="text/xml; charset=UTF-8"
            )
            
            document_id = doc_response.payload["documentId"]
            
            # Step 2: Upload feed content to the document
            feeds_api.upload_feed_document(
                document_id=document_id,
                content=feed_data,
            )
            
            # Step 3: Create the feed
            feed_response = feeds_api.create_feed(
                feedType=feed_type,
                marketplaceIds=marketplace_ids,
                inputFeedDocumentId=document_id,
            )
            
            feed_id = feed_response.payload["feedId"]
            logger.info(f"Feed submitted: {feed_id}")
            return feed_id
            
        except SellingApiException as e:
            logger.error(f"Feed submission error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error submitting feed: {str(e)}")
            raise
    
    def get_feed_status(self, feed_id: str) -> dict:
        """
        Check feed processing status
        
        Args:
            feed_id: Amazon feed submission ID
            
        Returns:
            Feed status payload
        """
        try:
            feeds_api = Feeds(credentials=self.credentials)
            response = feeds_api.get_feed(feed_id)
            return response.payload
        except SellingApiException as e:
            logger.error(f"Feed status check error for {feed_id}: {str(e)}")
            raise
    
    def get_feed_document(self, document_id: str) -> bytes:
        """
        Download feed processing report document
        
        Args:
            document_id: Document ID from feed status
            
        Returns:
            Document content as bytes
        """
        try:
            feeds_api = Feeds(credentials=self.credentials)
            response = feeds_api.get_feed_document(document_id)
            return response.payload
        except SellingApiException as e:
            logger.error(f"Feed document download error: {str(e)}")
            raise
    
    def get_inventory_summary(self, sku: str, marketplace_id: str) -> dict:
        """
        Get inventory summary for a SKU
        
        Args:
            sku: Stock Keeping Unit
            marketplace_id: Amazon marketplace ID
            
        Returns:
            Inventory summary payload
        """
        try:
            listings_api = ListingsItems(credentials=self.credentials)
            response = listings_api.get_listings_item(
                sellerId=self.seller_id,
                sku=sku,
                marketplaceId=marketplace_id,
            )
            return response.payload
        except SellingApiException as e:
            logger.error(f"Inventory check error for SKU {sku}: {str(e)}")
            raise
    
    def delete_listing(self, sku: str, marketplace_id: str) -> dict:
        """
        Delete a product listing
        
        Args:
            sku: Stock Keeping Unit
            marketplace_id: Amazon marketplace ID
            
        Returns:
            Deletion response
        """
        try:
            listings_api = ListingsItems(credentials=self.credentials)
            response = listings_api.delete_listings_item(
                sellerId=self.seller_id,
                sku=sku,
                marketplaceId=marketplace_id,
            )
            logger.info(f"Listing deleted: {sku}")
            return response.payload
        except SellingApiException as e:
            logger.error(f"SP-API error deleting SKU {sku}: {str(e)}")
            raise
