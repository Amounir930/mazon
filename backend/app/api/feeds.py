"""
Feed API Endpoints
Handles Amazon feed submission and status tracking
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.product import MessageResponse
from app.services.feed_service import FeedService
from loguru import logger

router = APIRouter()


@router.get("/{feed_id}/status")
async def get_feed_status(
    feed_id: str,
    seller_id: str = Query(..., description="Seller UUID"),
    db: Session = Depends(get_db),
):
    """
    Check the processing status of a submitted feed.
    
    Returns Amazon's feed processing status and any errors.
    """
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    try:
        status = FeedService.check_feed_status(db, seller_uuid, feed_id)
        return status
    except Exception as e:
        logger.error(f"Error checking feed status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check feed status: {str(e)}")


@router.post("/{feed_id}/get-results")
async def get_feed_results(
    feed_id: str,
    seller_id: str = Query(..., description="Seller UUID"),
    db: Session = Depends(get_db),
):
    """
    Get detailed results of a processed feed.
    
    Returns processing report with success/failure details for each item.
    """
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    try:
        results = FeedService.get_feed_results(db, seller_uuid, feed_id)
        return results
    except Exception as e:
        logger.error(f"Error getting feed results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get feed results: {str(e)}")


@router.post("/refresh-status", response_model=MessageResponse)
async def refresh_all_feed_statuses(
    seller_id: str = Query(..., description="Seller UUID"),
    db: Session = Depends(get_db),
):
    """
    Refresh status of all submitted feeds.
    
    Queries Amazon for latest status of all pending/processing feeds.
    """
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    try:
        count = FeedService.refresh_all_feed_statuses(db, seller_uuid)
        logger.info(f"Refreshed {count} feed statuses for seller {seller_id}")
        return {"message": f"Refreshed {count} feed statuses"}
    except Exception as e:
        logger.error(f"Error refreshing feed statuses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh feed statuses")
