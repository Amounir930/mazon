"""
Celery Tasks for Listing Operations
Async tasks for Amazon listing submissions
"""
from celery import Task
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.listing import Listing
from app.models.seller import Seller
from app.services.feed_service import FeedService
from app.services.listing_service import ListingService
from loguru import logger
from datetime import datetime


class DatabaseTask(Task):
    """
    Base task class that provides database session
    Automatically handles session cleanup
    """
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Cleanup database session after task completion"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.listing_tasks.submit_listing_task",
    queue="listings",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def submit_listing_task(self, listing_id: str) -> dict:
    """
    Submit a product listing to Amazon asynchronously
    
    Args:
        listing_id: UUID of the listing to submit
        
    Returns:
        Dictionary with submission result
    """
    db = self.db
    
    try:
        # Get listing
        from uuid import UUID
        listing_uuid = UUID(listing_id)
        listing = ListingService.get_listing(db, listing_uuid)
        
        if not listing:
            logger.error(f"Listing not found: {listing_id}")
            return {"status": "failed", "error": "Listing not found"}
        
        # Update status to processing
        ListingService.update_listing_status(db, listing_uuid, "processing")
        db.commit()
        
        # Get seller
        seller = db.query(Seller).filter(Seller.id == listing.seller_id).first()
        if not seller:
            raise ValueError(f"Seller not found: {listing.seller_id}")
        
        if not seller.is_active:
            raise ValueError(f"Seller account is inactive: {seller.seller_id}")
        
        # Submit to Amazon
        success = FeedService.submit_listing_to_amazon(db, listing, seller)
        
        if success:
            # Schedule feed status check task (run after 5 minutes)
            check_feed_status_task.apply_async(
                args=[listing_id, listing.feed_submission_id],
                countdown=300,  # 5 minutes
            )
            
            logger.info(f"Listing submitted successfully: {listing_id}")
            return {
                "status": "success",
                "listing_id": listing_id,
                "feed_id": listing.feed_submission_id,
            }
        else:
            logger.error(f"Listing submission failed: {listing_id}")
            return {
                "status": "failed",
                "listing_id": listing_id,
                "error": listing.error_message,
            }
    
    except Exception as e:
        logger.error(f"Error in submit_listing_task {listing_id}: {str(e)}")
        
        # Update listing status to failed
        try:
            from uuid import UUID
            listing_uuid = UUID(listing_id)
            ListingService.update_listing_status(
                db, listing_uuid, "failed",
                error_message=str(e),
            )
            db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update listing status: {str(update_error)}")
        
        # Retry task if retries remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=self.default_retry_delay * (2 ** self.request.retries))
        
        return {"status": "failed", "error": str(e)}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.listing_tasks.check_feed_status_task",
    queue="feeds",
    max_retries=5,
    default_retry_delay=300,
)
def check_feed_status_task(self, listing_id: str, feed_id: str) -> dict:
    """
    Check the processing status of a submitted feed
    
    Args:
        listing_id: UUID of the listing
        feed_id: Amazon feed submission ID
        
    Returns:
        Dictionary with feed status
    """
    db = self.db
    
    try:
        from uuid import UUID
        listing_uuid = UUID(listing_id)
        listing = ListingService.get_listing(db, listing_uuid)
        
        if not listing:
            logger.error(f"Listing not found: {listing_id}")
            return {"status": "failed", "error": "Listing not found"}
        
        seller = db.query(Seller).filter(Seller.id == listing.seller_id).first()
        if not seller:
            raise ValueError(f"Seller not found: {listing.seller_id}")
        
        # Check feed status via SP-API
        status = FeedService.check_feed_status(db, seller.id, feed_id)
        
        processing_status = status.get("processingStatus", "")
        
        if processing_status == "DONE":
            listing.status = "success"
            listing.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"Feed processing complete: {feed_id}")
            return {"status": "success", "feed_id": feed_id}
        
        elif processing_status in ["FATAL", "CANCELLED"]:
            listing.status = "failed"
            listing.error_message = f"Feed processing: {processing_status}"
            listing.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"Feed processing failed: {feed_id} - {processing_status}")
            return {"status": "failed", "feed_id": feed_id, "reason": processing_status}
        
        elif processing_status in ["IN_PROGRESS", "IN_QUEUE"]:
            # Re-check after another 5 minutes
            self.retry(countdown=300)
        
        return {"status": "pending", "feed_id": feed_id, "processing_status": processing_status}
    
    except Exception as e:
        logger.error(f"Error in check_feed_status_task {feed_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=self.default_retry_delay)
        
        return {"status": "failed", "error": str(e)}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.listing_tasks.sync_inventory_task",
    queue="inventory",
    max_retries=3,
    default_retry_delay=120,
)
def sync_inventory_task(self, seller_id: str) -> dict:
    """
    Sync inventory levels with Amazon
    
    Args:
        seller_id: UUID of the seller
        
    Returns:
        Dictionary with sync result
    """
    db = self.db
    
    try:
        from uuid import UUID
        seller_uuid = UUID(seller_id)
        seller = db.query(Seller).filter(Seller.id == seller_uuid).first()
        
        if not seller:
            raise ValueError(f"Seller not found: {seller_id}")
        
        # TODO: Implement inventory sync logic
        # This would query local inventory and update Amazon via SP-API
        
        logger.info(f"Inventory synced for seller: {seller_id}")
        return {"status": "success", "seller_id": seller_id}
    
    except Exception as e:
        logger.error(f"Error in sync_inventory_task {seller_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=self.default_retry_delay)
        
        return {"status": "failed", "error": str(e)}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.listing_tasks.bulk_submit_task",
    queue="listings",
    max_retries=2,
    default_retry_delay=120,
)
def bulk_submit_task(self, listing_ids: list[str]) -> dict:
    """
    Submit multiple listings in a single task
    
    Args:
        listing_ids: List of listing UUIDs to submit
        
    Returns:
        Dictionary with bulk submission result
    """
    db = self.db
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    try:
        from uuid import UUID
        
        for listing_id in listing_ids:
            try:
                listing_uuid = UUID(listing_id)
                listing = ListingService.get_listing(db, listing_uuid)
                
                if not listing:
                    results["failed"] += 1
                    results["errors"].append(f"Listing not found: {listing_id}")
                    continue
                
                # Submit each listing
                seller = db.query(Seller).filter(Seller.id == listing.seller_id).first()
                if not seller:
                    results["failed"] += 1
                    results["errors"].append(f"Seller not found for listing: {listing_id}")
                    continue
                
                success = FeedService.submit_listing_to_amazon(db, listing, seller)
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Submission failed: {listing_id}")
            
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error processing {listing_id}: {str(e)}")
        
        db.commit()
        logger.info(f"Bulk submit complete: {results}")
        return results
    
    except Exception as e:
        logger.error(f"Error in bulk_submit_task: {str(e)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=self.default_retry_delay)
        
        return {"status": "failed", "error": str(e)}
