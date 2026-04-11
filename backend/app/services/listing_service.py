"""
Listing Service
Handles listing queue management
"""
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.listing import Listing
from app.models.product import Product
from app.models.seller import Seller
from app.schemas.product import ListingCreate
from loguru import logger


class ListingService:
    """Listing queue management"""
    
    @staticmethod
    def create_listing(db: Session, listing_data: ListingCreate) -> Listing:
        """Create a new listing submission"""
        # Verify product exists
        product = db.query(Product).filter(Product.id == listing_data.product_id).first()
        if not product:
            raise ValueError(f"Product not found: {listing_data.product_id}")

        # Verify seller owns the product
        if product.seller_id != listing_data.seller_id:
            raise ValueError("Product does not belong to the specified seller")

        # Check for duplicate pending listing
        existing = db.query(Listing).filter(
            Listing.product_id == listing_data.product_id,
            Listing.status.in_(["queued", "processing", "submitted"]),
        ).first()

        if existing:
            raise ValueError(f"Product already has a pending listing: {existing.id}")

        # Get next queue position
        max_position = db.query(Listing).filter(
            Listing.seller_id == listing_data.seller_id,
            Listing.status == "queued",
        ).count()

        # Create listing
        listing = Listing(
            product_id=listing_data.product_id,
            seller_id=listing_data.seller_id,
            status="queued",
            queue_position=max_position + 1,
        )

        db.add(listing)
        db.flush()

        # Update product status
        product.status = "queued"

        logger.info(f"Listing created: {listing.id} for product {listing_data.product_id}")
        return listing
    
    @staticmethod
    def get_listing(db: Session, listing_id: UUID) -> Optional[Listing]:
        """Get listing by ID"""
        return db.query(Listing).filter(Listing.id == listing_id).first()
    
    @staticmethod
    def get_listings_by_seller(
        db: Session,
        seller_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[Listing]:
        """Get all listings for a seller"""
        query = db.query(Listing).filter(Listing.seller_id == seller_id)
        
        if status:
            query = query.filter(Listing.status == status)
        
        return query.order_by(Listing.queue_position.asc()).limit(limit).all()
    
    @staticmethod
    def update_listing_status(
        db: Session,
        listing_id: UUID,
        status: str,
        feed_submission_id: Optional[str] = None,
        amazon_asin: Optional[str] = None,
        amazon_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Listing]:
        """Update listing status"""
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            return None
        
        listing.status = status
        
        if feed_submission_id:
            listing.feed_submission_id = feed_submission_id
        if amazon_asin:
            listing.amazon_asin = amazon_asin
        if amazon_url:
            listing.amazon_url = amazon_url
        if error_message:
            listing.error_message = error_message
        
        if status in ["submitted", "success", "failed"]:
            listing.submitted_at = listing.submitted_at or datetime.utcnow()
        if status in ["success", "failed"]:
            listing.completed_at = datetime.utcnow()
        
        db.flush()
        return listing
    
    @staticmethod
    def retry_listing(db: Session, listing_id: UUID) -> bool:
        """Reset a failed listing for retry"""
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing or listing.status != "failed":
            return False
        
        listing.status = "queued"
        listing.error_message = None
        listing.submitted_at = None
        listing.completed_at = None
        db.flush()
        
        logger.info(f"Listing queued for retry: {listing_id}")
        return True
    
    @staticmethod
    def cancel_listing(db: Session, listing_id: UUID) -> bool:
        """Cancel a pending listing"""
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing or listing.status not in ["queued", "processing"]:
            return False
        
        listing.status = "cancelled"
        db.flush()
        
        logger.info(f"Listing cancelled: {listing_id}")
        return True
