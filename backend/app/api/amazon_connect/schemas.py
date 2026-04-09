"""
Amazon Connect Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional


class AmazonConnectRequest(BaseModel):
    lwa_client_id: str = Field(..., description="Amazon LWA Client ID")
    lwa_client_secret: str = Field(..., description="Amazon LWA Client Secret")
    lwa_refresh_token: str = Field(..., description="Amazon LWA Refresh Token")
    amazon_seller_id: str = Field(..., description="Amazon Seller/Merchant ID")
    display_name: Optional[str] = Field("My Amazon Store", max_length=200)
    marketplace_id: Optional[str] = Field("ARBP9OOSHTCHU", description="Marketplace ID")


class AmazonConnectResponse(BaseModel):
    seller_id: Optional[str]
    amazon_seller_id: Optional[str]
    is_connected: bool
    display_name: Optional[str] = None
    marketplace_id: Optional[str] = None
    last_sync_at: Optional[str] = None
    message: str


class AmazonVerifyResponse(BaseModel):
    is_connected: bool
    message: str
