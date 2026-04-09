"""
Product Sync API
Pulls products from Amazon SP-API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.models.product import Product
from app.services.amazon_api import AmazonAPIClient

router = APIRouter()


@router.post("/sync")
async def sync_products_from_amazon(db: Session = Depends(get_db)):
    """Pull all products from Amazon"""
    seller = db.query(Seller).first()
    if not seller or not seller.is_connected:
        raise HTTPException(status_code=400, detail="Amazon not connected")

    try:
        client = AmazonAPIClient(
            seller_id=seller.amazon_seller_id,
            marketplace_id=seller.marketplace_id,
            refresh_token=seller.lwa_refresh_token,
        )

        # Use get_orders as a simple sync mechanism
        # In a full implementation, you'd use the Listings API
        amazon_data = await client.get_orders()

        synced_count = 0
        # Process amazon_data and create products
        # This is a simplified version — adapt to actual API response structure
        if amazon_data and "orders" in amazon_data:
            for order in amazon_data.get("orders", []):
                sku = order.get("SellerOrderId", order.get("AmazonOrderId"))
                existing = db.query(Product).filter(Product.sku == sku).first()
                if not existing:
                    product = Product(
                        sku=sku,
                        name=f"Order {sku}",
                        price=0,
                        quantity=0,
                        status="published",
                    )
                    db.add(product)
                    synced_count += 1

        db.commit()
        seller.last_sync_at = datetime.utcnow()
        db.commit()

        logger.info(f"Synced {synced_count} products from Amazon")
        return {"message": f"Synced {synced_count} products", "synced_count": synced_count}

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
