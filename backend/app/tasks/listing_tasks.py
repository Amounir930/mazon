"""
Listing Tasks (Asyncio-based)
Replaces Celery tasks
"""
import asyncio
from datetime import datetime
from app.database import SessionLocal
from app.models.seller import Seller
from app.models.listing import Listing
from app.models.product import Product
from app.services.amazon_api import AmazonAPIClient
from loguru import logger


async def submit_listing_task(product_id: str) -> dict:
    """Submit a product listing to Amazon"""
    db = SessionLocal()
    try:
        # Get seller
        seller = db.query(Seller).first()
        if not seller or not seller.is_connected:
            raise ValueError("Amazon not connected")

        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Create listing record
        listing = Listing(
            product_id=product.id,
            status="processing",
            submitted_at=datetime.utcnow(),
        )
        db.add(listing)
        db.commit()

        # Submit to Amazon
        client = AmazonAPIClient(
            seller_id=seller.amazon_seller_id,
            marketplace_id=seller.marketplace_id,
            refresh_token=seller.lwa_refresh_token,
        )

        result = await client.create_or_update_listing(
            sku=product.sku,
            product_data={
                "name": product.name,
                "brand": product.brand or "",
                "description": product.description or "",
                "bullet_points": _parse_json_safe(product.bullet_points, []),
            },
        )

        if result.get("success"):
            listing.status = "success"
            listing.amazon_asin = result.get("data", {}).get("asin", "")
            listing.completed_at = datetime.utcnow()
            logger.info(f"Listing submitted: {product.sku}")
        else:
            listing.status = "failed"
            listing.error_message = str(result.get("error", "Unknown error"))
            logger.error(f"Listing failed: {product.sku}")

        db.commit()

        return {"status": listing.status, "asin": listing.amazon_asin}

    except Exception as e:
        db.rollback()
        logger.error(f"Submit listing failed: {str(e)}")

        # Update listing
        listing = db.query(Listing).filter(
            Listing.product_id == product_id
        ).order_by(Listing.created_at.desc()).first()
        if listing:
            listing.status = "failed"
            listing.error_message = str(e)
            db.commit()

        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


async def retry_listing_task(listing_id: str) -> dict:
    """Retry a failed listing"""
    db = SessionLocal()
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # Reset status
        listing.status = "queued"
        listing.error_message = None
        listing.submitted_at = None
        listing.completed_at = None
        db.commit()

        # Re-submit
        result = await submit_listing_task(listing.product_id)
        return result

    except Exception as e:
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def _parse_json_safe(value: str, default):
    """Safely parse a JSON string, returning default on failure"""
    import json
    if value is None:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
