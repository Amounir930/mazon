"""
Polling Tasks for SP-API Listing Status Updates
"""
import asyncio
from datetime import datetime
from loguru import logger


async def poll_listing_status(
    sku: str,
    seller_id: str,
    listing_id: str,
    max_polls: int = 12,
    interval_seconds: int = 300,
):
    """
    Poll Amazon SP-API for listing status updates.
    Runs every 5 minutes for up to 1 hour (12 polls).
    Updates listing record when status changes to ACTIVE or INVALID.
    """
    from app.database import SessionLocal
    from app.models.listing import Listing
    from app.services.sp_api_client import SPAPIClient

    client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')

    for poll_num in range(max_polls):
        await asyncio.sleep(interval_seconds)

        try:
            result = client.get_listing_item(seller_id, sku)
            status = result.get('status', 'UNKNOWN')
            asin = result.get('asin', '')
            issues = result.get('issues', [])

            db = SessionLocal()
            try:
                listing = db.query(Listing).filter(Listing.id == listing_id).first()
                if not listing:
                    logger.warning(f"Listing {listing_id} not found during polling")
                    break

                listing.sp_api_status = status
                listing.sp_api_last_polled_at = datetime.utcnow()

                if status == 'ACTIVE' or asin:
                    listing.status = 'success'
                    listing.stage = 'active'
                    listing.amazon_asin = asin
                    listing.completed_at = datetime.utcnow()
                    logger.info(f"✅ Listing ACTIVE: {sku} → ASIN {asin}")
                    db.commit()
                    break
                elif status == 'INVALID' and issues:
                    errors = [i for i in issues if i.get('severity') == 'ERROR']
                    if errors:
                        listing.status = 'failed'
                        listing.stage = 'rejected'
                        listing.error_message = '\n'.join([e.get('message', '')[:200] for e in errors])[:500]
                        listing.completed_at = datetime.utcnow()
                        logger.error(f"❌ Listing INVALID: {sku} — {errors[0].get('message', '')}")
                        db.commit()
                        break
                else:
                    logger.info(f"Poll #{poll_num+1}: {sku} status={status}, still processing...")
            finally:
                db.close()

        except Exception as e:
            logger.warning(f"Poll #{poll_num+1} failed for {sku}: {e}")

    logger.info(f"Polling complete for {sku} after {min(poll_num+1, max_polls)} attempts")
