"""
Listing API Endpoints
Handles listing queue management and submission
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.product import (
    ListingCreate,
    ListingResponse,
    MessageResponse,
)
from app.services.listing_service import ListingService
from app.tasks.listing_tasks import submit_listing_task
from loguru import logger

router = APIRouter()


@router.post("/submit", response_model=ListingResponse, status_code=201)
async def submit_listing(
    listing_data: ListingCreate,
    db: Session = Depends(get_db),
):
    """
    Submit a product listing to Amazon.
    
    This creates a listing record and queues it for async processing via Celery.
    """
    try:
        listing = ListingService.create_listing(db, listing_data)
        
        # Queue async submission
        task = submit_listing_task.delay(str(listing.id))
        
        logger.info(f"Listing queued for submission: {listing.id}")
        return listing
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting listing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    db: Session = Depends(get_db),
):
    """Get listing details by ID"""
    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing ID format")
    
    listing = ListingService.get_listing(db, listing_uuid)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return listing


@router.get("/", response_model=list[ListingResponse])
async def list_listings(
    seller_id: str = Query(..., description="Filter by seller UUID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all listings for a seller"""
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    listings = ListingService.get_listings_by_seller(db, seller_uuid, status=status, limit=limit)
    return listings


@router.post("/{listing_id}/retry", response_model=MessageResponse)
async def retry_listing(
    listing_id: str,
    db: Session = Depends(get_db),
):
    """Retry a failed listing submission"""
    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing ID format")
    
    listing = ListingService.get_listing(db, listing_uuid)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.status != "failed":
        raise HTTPException(status_code=400, detail="Can only retry failed listings")
    
    # Reset listing status and requeue
    ListingService.retry_listing(db, listing_uuid)
    
    # Queue async submission
    task = submit_listing_task.delay(str(listing_uuid))
    
    logger.info(f"Listing retry queued: {listing_id}")
    return {"message": "Listing retry queued successfully"}


@router.delete("/{listing_id}", response_model=MessageResponse)
async def cancel_listing(
    listing_id: str,
    db: Session = Depends(get_db),
):
    """Cancel a pending listing submission"""
    try:
        listing_uuid = UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing ID format")
    
    success = ListingService.cancel_listing(db, listing_uuid)
    
    if not success:
        raise HTTPException(status_code=400, detail="Can only cancel queued or processing listings")
    
    logger.info(f"Listing cancelled: {listing_id}")
    return {"message": "Listing cancelled successfully"}


@router.post("/bulk-submit", response_model=list[ListingResponse], status_code=201)
async def bulk_submit_listings(
    product_ids: list[str],
    seller_id: str = Query(..., description="Seller UUID"),
    db: Session = Depends(get_db),
):
    """
    Submit multiple product listings in a single request.
    
    All listings are queued for async processing.
    """
    try:
        seller_uuid = UUID(seller_id)
        product_uuids = [UUID(pid) for pid in product_ids]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")
    
    created_listings = []
    
    try:
        for product_uuid in product_uuids:
            listing_data = ListingCreate(product_id=product_uuid, seller_id=seller_uuid)
            listing = ListingService.create_listing(db, listing_data)
            
            # Queue async submission
            submit_listing_task.delay(str(listing.id))
            
            created_listings.append(listing)
        
        logger.info(f"Bulk submitted {len(created_listings)} listings for seller {seller_id}")
        return created_listings
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk submit: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
