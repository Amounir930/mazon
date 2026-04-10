"""
Amazon Connect API
Handles Amazon SP-API credentials storage and verification
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.api.amazon_connect.schemas import (
    AmazonConnectRequest,
    AmazonConnectResponse,
    AmazonVerifyResponse,
)
from app.api.amazon_connect.service import amazon_service

router = APIRouter()


@router.post("connect", response_model=AmazonConnectResponse)
async def connect_amazon(data: AmazonConnectRequest, db: Session = Depends(get_db)):
    """
    Save Amazon credentials for the single seller.
    Overwrites any existing seller record.
    """
    seller = db.query(Seller).first()

    if seller:
        seller.lwa_client_id = data.lwa_client_id
        seller.lwa_client_secret = data.lwa_client_secret
        seller.lwa_refresh_token = data.lwa_refresh_token
        seller.amazon_seller_id = data.amazon_seller_id
        seller.display_name = data.display_name or seller.display_name
        seller.marketplace_id = data.marketplace_id or seller.marketplace_id
        seller.is_connected = False
        logger.info(f"Updated seller: {data.amazon_seller_id}")
    else:
        seller = Seller(
            lwa_client_id=data.lwa_client_id,
            lwa_client_secret=data.lwa_client_secret,
            lwa_refresh_token=data.lwa_refresh_token,
            amazon_seller_id=data.amazon_seller_id,
            display_name=data.display_name or "My Amazon Store",
            marketplace_id=data.marketplace_id or "ARBP9OOSHTCHU",
            region="EU",
            is_connected=False,
        )
        db.add(seller)
        logger.info(f"Created new seller: {data.amazon_seller_id}")

    db.commit()
    db.refresh(seller)

    return AmazonConnectResponse(
        seller_id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        is_connected=seller.is_connected,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        message="Credentials saved. Click 'Verify' to test connection.",
    )


@router.post("verify", response_model=AmazonVerifyResponse)
async def verify_connection(db: Session = Depends(get_db)):
    """Test Amazon SP-API connection"""
    seller = db.query(Seller).first()
    if not seller:
        raise HTTPException(status_code=404, detail="No seller configured")

    is_valid = await amazon_service.verify_connection(
        client_id=seller.lwa_client_id,
        client_secret=seller.lwa_client_secret,
        refresh_token=seller.lwa_refresh_token,
        seller_id=seller.amazon_seller_id,
    )

    if is_valid:
        seller.is_connected = True
        db.commit()
        return AmazonVerifyResponse(is_connected=True, message="Connected to Amazon successfully!")
    else:
        seller.is_connected = False
        db.commit()
        raise HTTPException(status_code=400, detail="Failed to connect to Amazon. Check your credentials.")


@router.get("status", response_model=AmazonConnectResponse)
async def get_connection_status(db: Session = Depends(get_db)):
    """Get current Amazon connection status"""
    seller = db.query(Seller).first()

    if not seller:
        return AmazonConnectResponse(
            seller_id=None,
            amazon_seller_id=None,
            is_connected=False,
            message="No seller configured",
        )

    return AmazonConnectResponse(
        seller_id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        is_connected=seller.is_connected,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        message="Connected" if seller.is_connected else "Not connected",
    )
