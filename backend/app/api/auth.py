"""
Authentication API Endpoints
Provides mock authentication for the demo environment
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    seller_id: str
    marketplace_id: str
    region: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Mock login endpoint for demo users.
    Accepts demo@example.com / demo123
    """
    if request.email == "demo@example.com" and request.password == "demo123":
        return {
            "access_token": "mock-token-a1b2c3d4e5f67890",
            "token_type": "bearer",
            "user": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "demo@example.com",
                "seller_id": "MOCK-SELLER-001",
                "marketplace_id": "ARBP9OOSHTCHU",
                "region": "EU",
            }
        }
    
    raise HTTPException(
        status_code=401,
        detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
    )
