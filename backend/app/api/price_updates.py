"""
Price & Quantity Update API
Handles individual product price/quantity updates with Amazon sync
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.product import Product
from app.models.seller import Seller
from app.api.activity_log import create_activity_log
from app.tasks.task_manager import task_manager
from app.tasks.listing_tasks import submit_listing_task
from loguru import logger

router = APIRouter()


class PriceUpdateRequest(BaseModel):
    price: Decimal = Field(..., gt=0, lt=999999)
    currency: str = Field(default="EGP", max_length=10)
    sync_to_amazon: bool = Field(default=True, description="Submit to Amazon after update")


class QuantityUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=0)
    sync_to_amazon: bool = Field(default=True, description="Submit to Amazon after update")


@router.post("/{product_id}/price")
async def update_product_price(
    product_id: str,
    data: PriceUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update product price locally and optionally sync to Amazon"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_price = product.price
    product.price = data.price
    product.currency = data.currency
    product.updated_at = datetime.utcnow()
    db.commit()

    # Log activity
    create_activity_log(db, product_id, "updated", "success", {
        "field": "price",
        "old_value": float(old_price),
        "new_value": float(data.price),
        "currency": data.currency,
    })

    result = {"product_id": product_id, "price": float(data.price), "currency": data.currency}

    # Optionally submit to Amazon
    if data.sync_to_amazon:
        seller = db.query(Seller).first()
        if seller and seller.is_connected:
            task_id = await task_manager.submit(submit_listing_task(product_id))
            result["task_id"] = task_id
            result["message"] = "Price update submitted to Amazon"
        else:
            result["message"] = "Price updated locally (Amazon not connected)"

    return result


@router.post("/{product_id}/quantity")
async def update_product_quantity(
    product_id: str,
    data: QuantityUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update product quantity locally and optionally sync to Amazon"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_qty = product.quantity
    product.quantity = data.quantity
    product.updated_at = datetime.utcnow()
    db.commit()

    # Log activity
    create_activity_log(db, product_id, "updated", "success", {
        "field": "quantity",
        "old_value": old_qty,
        "new_value": data.quantity,
    })

    result = {"product_id": product_id, "quantity": data.quantity}

    # Optionally submit to Amazon
    if data.sync_to_amazon:
        seller = db.query(Seller).first()
        if seller and seller.is_connected:
            task_id = await task_manager.submit(submit_listing_task(product_id))
            result["task_id"] = task_id
            result["message"] = "Quantity update submitted to Amazon"
        else:
            result["message"] = "Quantity updated locally (Amazon not connected)"

    return result


@router.post("/bulk-price-update")
async def bulk_price_update(
    product_ids: list[str],
    data: PriceUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update price for multiple products at once"""
    results = []
    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            product.price = data.price
            product.currency = data.currency
            product.updated_at = datetime.utcnow()
            results.append({"product_id": pid, "status": "updated"})

    db.commit()
    logger.info(f"Bulk price update: {len(results)} products updated")
    return {"updated_count": len(results), "results": results}


@router.post("/bulk-quantity-update")
async def bulk_quantity_update(
    product_ids: list[str],
    data: QuantityUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update quantity for multiple products at once"""
    results = []
    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            product.quantity = data.quantity
            product.updated_at = datetime.utcnow()
            results.append({"product_id": pid, "status": "updated"})

    db.commit()
    logger.info(f"Bulk quantity update: {len(results)} products updated")
    return {"updated_count": len(results), "results": results}
