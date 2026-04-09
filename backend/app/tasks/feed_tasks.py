"""
Feed Tasks (Asyncio-based)
Handles background feed processing
"""
from datetime import datetime
from app.database import SessionLocal
from app.models.seller import Seller
from app.models.listing import Listing
from app.services.feed_service import FeedService
from loguru import logger


async def check_feed_status_task(feed_id: str) -> dict:
    """Check the status of a feed submission"""
    db = SessionLocal()
    try:
        status = FeedService.check_feed_status(db, feed_id)
        logger.info(f"Feed status checked: {feed_id} — {status.get('status')}")
        return status
    except Exception as e:
        logger.error(f"Feed status check failed: {feed_id} — {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


async def refresh_feeds_task() -> int:
    """Refresh status of all pending feeds"""
    db = SessionLocal()
    try:
        count = FeedService.refresh_all_feed_statuses(db)
        logger.info(f"Refreshed {count} feed statuses")
        return count
    except Exception as e:
        logger.error(f"Feed refresh failed: {str(e)}")
        return 0
    finally:
        db.close()
