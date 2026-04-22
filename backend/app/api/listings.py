"""
Listing API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import json

from app.database import get_db
from app.models.listing import Listing
from app.models.product import Product
from app.tasks.task_manager import task_manager
from app.tasks.listing_tasks import submit_listing_task, retry_listing_task
from loguru import logger

router = APIRouter()


@router.get("")
async def list_listings(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).order_by(Listing.created_at.desc())
    if status:
        query = query.filter(Listing.status == status)
    listings = query.all()
    result = []
    for l in listings:
        try:
            item = {c.name: getattr(l, c.name) for c in l.__table__.columns}
            # Convert datetime to string for JSON serialization
            for field in ['submitted_at', 'completed_at', 'created_at', 'sp_api_last_polled_at']:
                val = item.get(field)
                if val and hasattr(val, 'isoformat'):
                    item[field] = val.isoformat()

            # FIX: Include product name and image for frontend display
            product = db.query(Product).filter(Product.id == l.product_id).first()
            if product:
                item['product_name'] = product.name
                
                # Safely parse images JSON
                images = []
                if product.images:
                    if isinstance(product.images, str):
                        try:
                            images = json.loads(product.images)
                        except Exception:
                            images = [product.images] if product.images.startswith('http') else []
                    elif isinstance(product.images, list):
                        images = product.images
                item['product_images'] = images
            else:
                item['product_name'] = "منتج غير موجود"
                item['product_images'] = []

            result.append(item)
        except Exception as e:
            logger.error(f"Error processing listing {l.id}: {e}")
            continue

    return result



@router.post("/submit")
async def submit_listing(product_id: str):
    """Submit a product listing (async)"""
    task_id = await task_manager.submit(submit_listing_task(product_id))
    return {"task_id": task_id, "message": "Listing submitted in background"}


@router.post("/submit-multi")
async def submit_multi_listing(product_id: str, copies: int = Query(1, ge=1, le=50)):
    """Submit multiple product listings with unique SKUs"""
    results = []
    
    # Loop and create multiple listings
    for i in range(1, copies + 1):
        task_id = await task_manager.submit(submit_listing_task(product_id))
        results.append({
            "copy_number": i,
            "task_id": task_id,
            "status": "queued"
        })
    
    logger.info(f"Created {copies} listing submissions for product {product_id}")
    
    return {
        "product_id": product_id,
        "total_listings": copies,
        "listings": results,
        "message": f"Successfully created {copies} listing submissions"
    }


@router.post("/{listing_id}/retry")
async def retry_listing(listing_id: str):
    """Retry a failed listing"""
    task_id = await task_manager.submit(retry_listing_task(listing_id))
    return {"task_id": task_id, "message": "Retry submitted in background"}


@router.delete("/{listing_id}/cancel")
async def cancel_listing_feed(listing_id: str, db: Session = Depends(get_db)):
    """Cancel an active feed submission if it's still in queue"""
    from app.models.seller import Seller
    from app.services.amazon_api import AmazonAPIClient
    
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    # Check both potential ID fields
    submission_id = listing.feed_submission_id or listing.sp_api_submission_id
    
    if not submission_id:
        raise HTTPException(status_code=400, detail="Listing does not have an active feed submission ID")

    if listing.status not in ["queued", "processing", "submitted"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel listing in status: {listing.status}")

    seller = db.query(Seller).filter(Seller.id == listing.seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    try:
        # Use SPAPIClient instead of AmazonAPIClient for better reliability with current credentials
        from app.services.sp_api_client import SPAPIClient
        
        # Get country code from seller or session if possible, fallback to 'eg'
        country_code = getattr(seller, 'country_code', 'eg') or 'eg'
        
        client = SPAPIClient(
            marketplace_id=seller.marketplace_id,
            country_code=country_code,
            refresh_token=seller.lwa_refresh_token
        )
        
        # All SPAPIClient instances have cancel_feed now (synchronous)
        result = client.cancel_feed(submission_id)

        # Update local listing status
        listing.status = "failed"
        listing.error_message = "Cancelled by user"
        db.commit()
        
        return {"success": True, "message": "Feed cancellation request sent to Amazon", "amazon_response": result}
        
    except Exception as e:
        logger.error(f"Failed to cancel feed {submission_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel feed: {str(e)}")
