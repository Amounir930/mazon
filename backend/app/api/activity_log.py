"""
Activity Log API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.models.activity_log import ActivityLog
from loguru import logger

router = APIRouter()


def activity_log_to_dict(log: ActivityLog) -> dict:
    """Convert ActivityLog to dict"""
    d = {c.name: getattr(log, c.name) for c in log.__table__.columns}
    # Parse details JSON
    if d.get("details") and isinstance(d["details"], str):
        try:
            d["details"] = json.loads(d["details"])
        except Exception:
            d["details"] = {}
    # Convert datetime to string
    if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d


@router.get("/{product_id}/activity-log")
async def get_activity_log(product_id: str, db: Session = Depends(get_db)):
    """Get activity log for a specific product"""
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.product_id == product_id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )
    return {
        "product_id": product_id,
        "logs": [activity_log_to_dict(log) for log in logs],
        "total": len(logs),
    }


def create_activity_log(
    db: Session,
    product_id: str,
    action: str,
    status: str,
    details: dict | None = None,
    listing_id: str | None = None,
) -> ActivityLog:
    """Create an activity log entry (internal helper)"""
    log = ActivityLog(
        product_id=product_id,
        listing_id=listing_id,
        action=action,
        status=status,
        details=json.dumps(details) if details else None,
    )
    db.add(log)
    db.commit()
    logger.info(f"Activity logged: {action} - {status} for product {product_id}")
    return log
