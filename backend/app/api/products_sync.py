"""
Product Sync API
Pulls products from Amazon SP-API and stores them in local database
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import Optional
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.models.product import Product
from app.api.activity_log import create_activity_log

router = APIRouter()


@router.post("/sync")
async def sync_products_from_amazon(
    sku: Optional[str] = Query(None, description="Sync specific SKU only"),
    db: Session = Depends(get_db),
):
    """
    Pull products from Amazon and store them locally.

    - If `sku` is provided: sync only that SKU (partial sync)
    - If `sku` is not provided: sync all products from Amazon

    In MOCK mode: returns sample products
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
        if sku:
            # Partial sync: get specific SKU
            try:
                listing = await client.get_listings()
                amazon_listings = [l for l in listing if l.get("sku") == sku] if listing else []
            except Exception:
                amazon_listings = []
        else:
            amazon_listings = await client.get_listings()

        if not amazon_listings:
            return {"message": "No products found on Amazon", "synced_count": 0}

        synced_count = 0
        updated_count = 0
        skipped_count = 0

        for item in amazon_listings:
            item_sku = item.get("sku", "")
            if not item_sku:
                continue

            # Extract Amazon data with more fields
            item_data = {
                "title": item.get("title", item_sku),
                "price": item.get("price", 0),
                "quantity": item.get("quantity", 0),
                "category": item.get("category", ""),
                "brand": item.get("brand", ""),
                "description": item.get("description", ""),
                "bullet_points": item.get("bullet_points", []),
                "images": item.get("images", []),
                # Amazon-specific fields
                "condition": item.get("condition", "New"),
                "fulfillment_channel": item.get("fulfillment_channel", "MFN"),
                "handling_time": item.get("handling_time", 0),
                "product_type": item.get("product_type", ""),
                "asin": item.get("asin", ""),
            }

            # Check if product already exists
            existing = db.query(Product).filter(Product.sku == item_sku).first()
            if existing:
                # Update existing product with all fields
                existing.name = item_data["title"]
                existing.price = item_data["price"]
                existing.quantity = item_data["quantity"]
                existing.category = item_data["category"]
                existing.brand = item_data["brand"]
                existing.description = item_data["description"]
                existing.status = "published"
                existing.updated_at = datetime.utcnow()

                # Update Amazon-specific fields if available
                if item_data["condition"] != "New":
                    existing.condition = item_data["condition"]
                if item_data["fulfillment_channel"]:
                    existing.fulfillment_channel = item_data["fulfillment_channel"]
                if item_data["handling_time"] is not None:
                    existing.handling_time = item_data["handling_time"]
                if item_data["product_type"]:
                    existing.product_type = item_data["product_type"]

                # Log activity
                create_activity_log(db, existing.id, "synced", "success", {
                    "source": "amazon",
                    "sku": item_sku,
                    "fields_updated": ["name", "price", "quantity", "condition", "fulfillment"],
                })

                updated_count += 1
                logger.debug(f"Updated existing product: {item_sku}")
            else:
                # Create new product with all fields
                bullet_points = item_data["bullet_points"]
                images = item_data["images"]

                product = Product(
                    seller_id=seller.id,
                    sku=item_sku,
                    name=item_data["title"],
                    price=item_data["price"],
                    quantity=item_data["quantity"],
                    category=item_data["category"],
                    brand=item_data["brand"],
                    description=item_data["description"],
                    bullet_points=json.dumps(bullet_points),
                    images=json.dumps(images),
                    status="published",
                    # Amazon-specific fields
                    condition=item_data["condition"],
                    fulfillment_channel=item_data["fulfillment_channel"],
                    handling_time=item_data["handling_time"],
                    product_type=item_data["product_type"],
                )
                db.add(product)
                db.flush()  # Get product ID

                # Log activity
                create_activity_log(db, product.id, "synced", "success", {
                    "source": "amazon",
                    "sku": item_sku,
                    "action": "created_from_sync",
                })

                synced_count += 1
                logger.info(f"New product synced: {item_sku}")

        db.commit()

        # Update last sync time
        seller.last_sync_at = datetime.utcnow()
        db.commit()

        total = synced_count + updated_count
        sync_type = f"partial (SKU: {sku})" if sku else "full"
        logger.info(f"Sync {sync_type} complete: {synced_count} new, {updated_count} updated, {total} total")

        return {
            "message": f"Synced {total} products from Amazon ({synced_count} new, {updated_count} updated)",
            "sync_type": sync_type,
            "synced_count": synced_count,
            "updated_count": updated_count,
            "total": total,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
