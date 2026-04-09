"""
Auth API Schemas
Request/Response models for authentication endpoints
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Register request schema"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(None, max_length=200)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "SellerResponse"


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


# Import here to avoid circular imports
from app.schemas.product import SellerResponse  # noqa: E402
TokenResponse.model_rebuild()
