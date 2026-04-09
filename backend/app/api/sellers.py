"""
Seller API Endpoints
Handles seller registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.product import SellerCreate, SellerResponse, MessageResponse
from app.models.seller import Seller
from app.services.auth import auth_service
from loguru import logger

router = APIRouter()


@router.post("/register", response_model=SellerResponse)
async def register_seller(
    seller_data: SellerCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new Amazon seller account.
    
    This endpoint stores seller credentials for SP-API integration.
    """
    try:
        # Check if seller already exists
        existing_seller = db.query(Seller).filter(
            Seller.email == seller_data.email
        ).first()
        
        if existing_seller:
            raise HTTPException(
                status_code=400,
                detail=f"Seller with email {seller_data.email} already exists"
            )
        
        # Create new seller
        new_seller = Seller(
            email=seller_data.email,
            seller_id=seller_data.seller_id,
            marketplace_id=seller_data.marketplace_id,
            region=seller_data.region,
            lwa_refresh_token=seller_data.lwa_refresh_token,
            mws_auth_token=seller_data.mws_auth_token,
            is_active=True,
        )
        
        db.add(new_seller)
        db.commit()
        db.refresh(new_seller)
        
        logger.info(f"New seller registered: {seller_data.email}")
        return new_seller
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering seller: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{seller_id}", response_model=SellerResponse)
async def get_seller(
    seller_id: str,
    db: Session = Depends(get_db)
):
    """Get seller details by ID"""
    from uuid import UUID
    
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    seller = db.query(Seller).filter(Seller.id == seller_uuid).first()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    return seller


@router.get("/email/{email}", response_model=SellerResponse)
async def get_seller_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """Get seller details by email"""
    seller = db.query(Seller).filter(Seller.email == email).first()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    return seller


@router.post("/auth-url")
async def get_auth_url(seller_email: str):
    """
    Get Amazon OAuth2 authorization URL for seller authentication.
    
    Use this URL to redirect sellers to Amazon for permission granting.
    """
    try:
        auth_url = auth_service.get_auth_url(seller_email)
        return {
            "auth_url": auth_url,
            "message": "Redirect seller to this URL to authorize with Amazon"
        }
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")


@router.post("/oauth/callback", response_model=SellerResponse)
async def oauth_callback(
    code: str,
    state: str,  # seller_email
    db: Session = Depends(get_db)
):
    """
    OAuth2 callback handler for Amazon LWA.
    
    This endpoint receives the authorization code from Amazon after seller grants permissions.
    """
    try:
        seller = await auth_service.register_seller(db, state, code)
        return seller
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")


@router.put("/{seller_id}/status", response_model=MessageResponse)
async def update_seller_status(
    seller_id: str,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """Activate or deactivate a seller account"""
    from uuid import UUID
    
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    seller = db.query(Seller).filter(Seller.id == seller_uuid).first()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    seller.is_active = is_active
    db.commit()
    
    status = "activated" if is_active else "deactivated"
    logger.info(f"Seller {seller_id} {status}")
    
    return {"message": f"Seller {status} successfully"}


@router.delete("/{seller_id}", response_model=MessageResponse)
async def delete_seller(
    seller_id: str,
    db: Session = Depends(get_db)
):
    """Delete a seller account (cascades to products and listings)"""
    from uuid import UUID
    
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    seller = db.query(Seller).filter(Seller.id == seller_uuid).first()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    db.delete(seller)
    db.commit()
    
    logger.info(f"Seller {seller_id} deleted")
    return {"message": "Seller deleted successfully"}
