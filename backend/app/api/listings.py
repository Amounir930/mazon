"""
Listing API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.listing import Listing
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
    return [
        {c.name: getattr(l, c.name) for c in l.__table__.columns}
        for l in listings
    ]


@router.post("/submit")
async def submit_listing(product_id: str):
    """Submit a product listing (async)"""
    task_id = await task_manager.submit(submit_listing_task(product_id))
    return {"task_id": task_id, "message": "Listing submitted in background"}


@router.post("/{listing_id}/retry")
async def retry_listing(listing_id: str):
    """Retry a failed listing"""
    task_id = await task_manager.submit(retry_listing_task(listing_id))
    return {"task_id": task_id, "message": "Retry submitted in background"}
