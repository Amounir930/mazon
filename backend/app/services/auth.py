"""
LWA OAuth2 Authentication Service
Handles Login with Amazon authentication flow
"""
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.seller import Seller
from loguru import logger

settings = get_settings()


class LWAAuthService:
    """Login with Amazon OAuth2 Service"""
    
    def __init__(self):
        self.lwa_auth_url = "https://www.amazon.com/ap/oa"
        self.lwa_token_url = "https://api.amazon.com/auth/o2/token"
    
    def get_auth_url(self, seller_email: str) -> str:
        """Generate Amazon OAuth2 authorization URL"""
        params = {
            "client_id": settings.SP_API_CLIENT_ID,
            "scope": "sellingpartnerapi::migration",
            "response_type": "code",
            "redirect_uri": settings.SP_API_REDIRECT_URI,
            "state": seller_email,
        }
        return f"{self.lwa_auth_url}?{requests.compat.urlencode(params)}"
    
    async def exchange_code_for_token(self, auth_code: str) -> dict:
        """Exchange authorization code for LWA access token"""
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": settings.SP_API_CLIENT_ID,
            "client_secret": settings.SP_API_CLIENT_SECRET,
            "redirect_uri": settings.SP_API_REDIRECT_URI,
        }
        
        response = requests.post(self.lwa_token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh expired access token"""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.SP_API_CLIENT_ID,
            "client_secret": settings.SP_API_CLIENT_SECRET,
        }
        
        response = requests.post(self.lwa_token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    async def register_seller(self, db: Session, seller_email: str, auth_code: str) -> Seller:
        """Complete seller registration with Amazon"""
        # Exchange code for tokens
        token_data = await self.exchange_code_for_token(auth_code)
        
        # Check if seller exists
        seller = db.query(Seller).filter(Seller.email == seller_email).first()
        
        if seller:
            # Update tokens
            seller.lwa_refresh_token = token_data["refresh_token"]
            seller.updated_at = datetime.utcnow()
            logger.info(f"Seller updated: {seller_email}")
        else:
            # Create new seller
            seller = Seller(
                email=seller_email,
                lwa_refresh_token=token_data["refresh_token"],
                marketplace_id=settings.DEFAULT_MARKETPLACE_ID,  # ARBP9OOSHTCHU (Egypt)
                region=settings.DEFAULT_REGION,
            )
            db.add(seller)
            logger.info(f"New seller registered: {seller_email}")
        
        db.commit()
        db.refresh(seller)
        return seller


auth_service = LWAAuthService()
