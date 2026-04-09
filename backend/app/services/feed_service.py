"""
Feed Service
Handles Amazon feed XML generation and submission
"""
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.models.listing import Listing
from app.models.seller import Seller
from app.models.product import Product
from app.services.sp_api import SPAPIClient
from app.config import get_settings
from loguru import logger

settings = get_settings()


class FeedService:
    """Handle Amazon feed generation and submission"""
    
    @staticmethod
    def generate_product_xml(product: dict, seller_id: str) -> bytes:
        """
        Generate Amazon MWS/SP-API compliant XML for product listing
        
        Args:
            product: Product data dictionary
            seller_id: Amazon Seller ID
            
        Returns:
            XML content as bytes
        """
        envelope = ET.Element("AmazonEnvelope", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "amzn-envelope.xsd",
        })
        
        # Header
        header = ET.SubElement(envelope, "Header")
        ET.SubElement(header, "DocumentVersion").text = "1.01"
        ET.SubElement(header, "MerchantIdentifier").text = seller_id
        
        ET.SubElement(envelope, "MessageType").text = "Product"
        ET.SubElement(envelope, "PurgeAndReplace").text = "false"
        
        # Message
        message = ET.SubElement(envelope, "Message")
        ET.SubElement(message, "MessageID").text = "1"
        ET.SubElement(message, "OperationType").text = "Update"
        
        product_elem = ET.SubElement(message, "Product")
        ET.SubElement(product_elem, "SKU").text = product.get("sku", "")
        
        # Standard Product ID (UPC/EAN)
        standard_id = ET.SubElement(product_elem, "StandardProductID")
        if product.get("upc"):
            ET.SubElement(standard_id, "Type").text = "UPC"
            ET.SubElement(standard_id, "Value").text = product["upc"]
        elif product.get("ean"):
            ET.SubElement(standard_id, "Type").text = "EAN"
            ET.SubElement(standard_id, "Value").text = product["ean"]
        
        # Description Data
        desc_data = ET.SubElement(product_elem, "DescriptionData")
        ET.SubElement(desc_data, "Title").text = product.get("name", "")
        
        if product.get("brand"):
            ET.SubElement(desc_data, "Brand").text = product["brand"]
        
        if product.get("description"):
            ET.SubElement(desc_data, "Description").text = product["description"]
        
        # Bullet Points
        for bullet in product.get("bullet_points", []):
            ET.SubElement(desc_data, "BulletPoint").text = bullet
        
        # Pricing
        if product.get("price"):
            pricing_data = ET.SubElement(product_elem, "PricingData")
            standard_price = ET.SubElement(pricing_data, "StandardPrice")
            standard_price.set("currency", "EGP")  # TODO: Make dynamic based on marketplace
            standard_price.text = str(product["price"])
        
        # Quantity
        if product.get("quantity") is not None:
            ET.SubElement(product_elem, "Quantity").text = str(product["quantity"])
        
        # Convert to XML string
        xml_string = ET.tostring(envelope, encoding="UTF-8", xml_declaration=True)
        return xml_string
    
    @staticmethod
    def submit_listing_to_amazon(db: Session, listing: Listing, seller: Seller) -> bool:
        """
        Submit a single listing to Amazon via SP-API
        
        Args:
            db: Database session
            listing: Listing model instance
            seller: Seller model instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get product data
            product = listing.product
            
            # Convert product to dict
            product_data = {
                "sku": product.sku,
                "name": product.name,
                "brand": product.brand,
                "description": product.description,
                "bullet_points": product.bullet_points or [],
                "price": float(product.price) if product.price else 0,
                "quantity": product.quantity or 0,
                "upc": product.upc,
                "ean": product.ean,
            }
            
            # Generate XML
            xml_data = FeedService.generate_product_xml(product_data, seller.seller_id)
            
            # Initialize SP-API client
            sp_client = SPAPIClient(
                seller_id=seller.seller_id,
                refresh_token=seller.lwa_refresh_token,
            )
            
            # Submit feed
            feed_id = sp_client.submit_feed(
                feed_type="_POST_PRODUCT_DATA_",
                feed_data=xml_data,
                marketplace_ids=[seller.marketplace_id],
            )
            
            # Update listing with feed ID
            listing.feed_submission_id = feed_id
            listing.status = "submitted"
            listing.submitted_at = __import__("datetime").datetime.utcnow()
            
            db.commit()
            logger.info(f"Listing submitted to Amazon: {listing.id}, Feed: {feed_id}")
            return True
            
        except Exception as e:
            listing.status = "failed"
            listing.error_message = str(e)
            db.commit()
            logger.error(f"Listing submission failed: {listing.id}: {str(e)}")
            return False
    
    @staticmethod
    def check_feed_status(db: Session, seller_id: UUID, feed_id: str) -> dict:
        """
        Check the processing status of a feed
        
        Args:
            db: Database session
            seller_id: Seller UUID
            feed_id: Amazon feed submission ID
            
        Returns:
            Feed status dictionary
        """
        try:
            seller = db.query(Seller).filter(Seller.id == seller_id).first()
            if not seller:
                raise ValueError(f"Seller not found: {seller_id}")
            
            sp_client = SPAPIClient(
                seller_id=seller.seller_id,
                refresh_token=seller.lwa_refresh_token,
            )
            
            status = sp_client.get_feed_status(feed_id)
            
            # Update listings with this feed ID
            listings = db.query(Listing).filter(Listing.feed_submission_id == feed_id).all()
            for listing in listings:
                processing_status = status.get("processingStatus", "")
                
                if processing_status == "DONE":
                    listing.status = "success"
                    listing.completed_at = __import__("datetime").datetime.utcnow()
                elif processing_status == "FATAL":
                    listing.status = "failed"
                    listing.error_message = "Feed processing failed with fatal errors"
                elif processing_status == "CANCELLED":
                    listing.status = "failed"
                    listing.error_message = "Feed processing was cancelled"
            
            db.commit()
            return status
            
        except Exception as e:
            logger.error(f"Error checking feed status {feed_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_feed_results(db: Session, seller_id: UUID, feed_id: str) -> dict:
        """
        Get detailed results of a processed feed
        
        Args:
            db: Database session
            seller_id: Seller UUID
            feed_id: Amazon feed submission ID
            
        Returns:
            Feed results dictionary
        """
        try:
            seller = db.query(Seller).filter(Seller.id == seller_id).first()
            if not seller:
                raise ValueError(f"Seller not found: {seller_id}")
            
            sp_client = SPAPIClient(
                seller_id=seller.seller_id,
                refresh_token=seller.lwa_refresh_token,
            )
            
            # Get feed status first
            feed_status = sp_client.get_feed_status(feed_id)
            
            # If done, get the result document
            if feed_status.get("processingStatus") == "DONE":
                result_document_id = feed_status.get("resultFeedDocumentId")
                if result_document_id:
                    # TODO: Download and parse result document
                    return {
                        "feed_id": feed_id,
                        "status": feed_status,
                        "message": "Results document available for download",
                    }
            
            return {"feed_id": feed_id, "status": feed_status}
            
        except Exception as e:
            logger.error(f"Error getting feed results {feed_id}: {str(e)}")
            raise
    
    @staticmethod
    def refresh_all_feed_statuses(db: Session, seller_id: UUID) -> int:
        """
        Refresh status of all submitted feeds
        
        Args:
            db: Database session
            seller_id: Seller UUID
            
        Returns:
            Number of feeds refreshed
        """
        try:
            seller = db.query(Seller).filter(Seller.id == seller_id).first()
            if not seller:
                raise ValueError(f"Seller not found: {seller_id}")
            
            sp_client = SPAPIClient(
                seller_id=seller.seller_id,
                refresh_token=seller.lwa_refresh_token,
            )
            
            # Get all submitted/processing listings
            pending_listings = db.query(Listing).filter(
                Listing.seller_id == seller_id,
                Listing.status.in_(["submitted", "processing"]),
                Listing.feed_submission_id.isnot(None),
            ).all()
            
            refreshed_count = 0
            for listing in pending_listings:
                try:
                    status = sp_client.get_feed_status(listing.feed_submission_id)
                    processing_status = status.get("processingStatus", "")
                    
                    if processing_status == "DONE":
                        listing.status = "success"
                        listing.completed_at = __import__("datetime").datetime.utcnow()
                    elif processing_status in ["FATAL", "CANCELLED"]:
                        listing.status = "failed"
                        listing.error_message = f"Feed processing: {processing_status}"
                    
                    refreshed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to refresh feed {listing.feed_submission_id}: {str(e)}")
            
            db.commit()
            return refreshed_count
            
        except Exception as e:
            logger.error(f"Error refreshing feed statuses: {str(e)}")
            raise
