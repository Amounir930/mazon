"""
Product Sync API
Pulls products from Amazon SP-API and stores them in local database
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.models.product import Product

router = APIRouter()


@router.post("/sync")
async def sync_products_from_amazon(db: Session = Depends(get_db)):
    """
    Pull all products from Amazon and store them locally.

    In MOCK mode: returns 5 sample products
    In REAL mode: fetches from Amazon SP-API
    """
    seller = db.query(Seller).first()
    if not seller or not seller.is_connected:
        raise HTTPException(status_code=400, detail="Amazon not connected. Please connect and verify first.")

    try:
        from app.services.amazon_api import AmazonAPIClient

        client = AmazonAPIClient(
            seller_id=seller.amazon_seller_id,
            marketplace_id=seller.marketplace_id,
            refresh_token=seller.lwa_refresh_token,
        )

        # Fetch products from Amazon
        amazon_listings = await client.get_listings()

        if not amazon_listings:
            return {"message": "No products found on Amazon", "synced_count": 0}

        synced_count = 0
        skipped_count = 0

        for item in amazon_listings:
            sku = item.get("sku", "")
            if not sku:
                continue

            # Check if product already exists
            existing = db.query(Product).filter(Product.sku == sku).first()
            if existing:
                # Update existing product
                existing.name = item.get("title", existing.name)
                existing.price = item.get("price", existing.price)
                existing.quantity = item.get("quantity", existing.quantity)
                existing.category = item.get("category", existing.category)
                existing.brand = item.get("brand", existing.brand)
                existing.status = "published"
                existing.updated_at = datetime.utcnow()
                skipped_count += 1
                logger.debug(f"Updated existing product: {sku}")
            else:
                # Create new product
                bullet_points = item.get("bullet_points", [])
                images = item.get("images", [])

                product = Product(
                    sku=sku,
                    name=item.get("title", sku),
                    price=item.get("price", 0),
                    quantity=item.get("quantity", 0),
                    category=item.get("category", ""),
                    brand=item.get("brand", ""),
                    description=item.get("description", ""),
                    bullet_points=json.dumps(bullet_points),
                    images=json.dumps(images),
                    status="published",
                )
                db.add(product)
                synced_count += 1
                logger.info(f"New product synced: {sku}")

        db.commit()

        # Update last sync time
        seller.last_sync_at = datetime.utcnow()
        db.commit()

        total = synced_count + skipped_count
        logger.info(f"Sync complete: {synced_count} new, {skipped_count} updated, {total} total")

        return {
            "message": f"Synced {total} products from Amazon ({synced_count} new, {skipped_count} updated)",
            "synced_count": synced_count,
            "updated_count": skipped_count,
            "total": total,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
