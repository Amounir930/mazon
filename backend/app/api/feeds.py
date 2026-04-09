"""
Feed API Endpoints — Single Client
Handles Amazon feed submission and status tracking
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.listing import Listing
from app.schemas.product import MessageResponse
from app.services.feed_service import FeedService
from loguru import logger

router = APIRouter()


@router.get("/{feed_id}/status")
async def get_feed_status(
    feed_id: str,
    db: Session = Depends(get_db),
):
    """Check the processing status of a submitted feed"""
    try:
        status = FeedService.check_feed_status(db, feed_id)
        return status
    except Exception as e:
        logger.error(f"Error checking feed status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check feed status: {str(e)}")


@router.post("/{feed_id}/get-results")
async def get_feed_results(
    feed_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed results of a processed feed"""
    try:
        results = FeedService.get_feed_results(db, feed_id)
        return results
    except Exception as e:
        logger.error(f"Error getting feed results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get feed results: {str(e)}")


@router.post("/refresh-status", response_model=MessageResponse)
async def refresh_all_feed_statuses(
    db: Session = Depends(get_db),
):
    """Refresh status of all submitted feeds"""
    try:
        count = FeedService.refresh_all_feed_statuses(db)
        logger.info(f"Refreshed {count} feed statuses")
        return {"message": f"Refreshed {count} feed statuses"}
    except Exception as e:
        logger.error(f"Error refreshing feed statuses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh feed statuses")


@router.get("/", response_model=list)
async def list_feeds(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all feed submissions"""
    feeds = FeedService.list_feeds(db, status=status)
    return feeds
