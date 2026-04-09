"""
Tasks API
Manage background tasks
"""
from fastapi import APIRouter, HTTPException
from app.tasks.task_manager import task_manager
from app.tasks.listing_tasks import submit_listing_task, retry_listing_task
from loguru import logger

router = APIRouter()


@router.post("/submit-listing")
async def submit_listing(product_id: str):
    """Submit a product listing (async)"""
    task_id = await task_manager.submit(submit_listing_task(product_id))
    return {"task_id": task_id, "message": "Listing submitted in background"}


@router.post("/retry-listing/{listing_id}")
async def retry_listing(listing_id: str):
    """Retry a failed listing"""
    task_id = await task_manager.submit(retry_listing_task(listing_id))
    return {"task_id": task_id, "message": "Retry submitted in background"}


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    status = task_manager.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/")
async def list_tasks():
    """List all tasks"""
    return task_manager.list_all()
