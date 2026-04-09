"""
Seller API Endpoints — Single Client
Manage Amazon SP-API credentials (one seller only)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.seller import Seller
from app.schemas.product import MessageResponse
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

router = APIRouter()


class SellerInfoResponse(BaseModel):
    id: Optional[str] = None
    amazon_seller_id: Optional[str] = None
    display_name: Optional[str] = None
    marketplace_id: Optional[str] = None
    region: Optional[str] = None
    is_connected: bool = False
    last_sync_at: Optional[str] = None
    message: str = ""


@router.get("/info", response_model=SellerInfoResponse)
async def get_seller_info(db: Session = Depends(get_db)):
    """Get the single seller configuration"""
    seller = db.query(Seller).first()

    if not seller:
        return SellerInfoResponse(message="No seller configured")

    return SellerInfoResponse(
        id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        region=seller.region,
        is_connected=seller.is_connected,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        message="Connected" if seller.is_connected else "Not connected",
    )


@router.put("/info", response_model=SellerInfoResponse)
async def update_seller_info(
    display_name: Optional[str] = None,
    marketplace_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update seller display name or marketplace"""
    seller = db.query(Seller).first()

    if not seller:
        raise HTTPException(status_code=404, detail="No seller configured. Connect Amazon first.")

    if display_name:
        seller.display_name = display_name
    if marketplace_id:
        seller.marketplace_id = marketplace_id

    db.commit()
    db.refresh(seller)

    logger.info(f"Seller info updated: {seller.display_name}")

    return SellerInfoResponse(
        id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        region=seller.region,
        is_connected=seller.is_connected,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        message="Updated successfully",
    )


@router.delete("/disconnect", response_model=MessageResponse)
async def disconnect_seller(db: Session = Depends(get_db)):
    """Disconnect the seller (reset connection status)"""
    seller = db.query(Seller).first()

    if not seller:
        raise HTTPException(status_code=404, detail="No seller configured")

    seller.is_connected = False
    db.commit()

    logger.info("Seller disconnected")
    return {"message": "Disconnected successfully"}
