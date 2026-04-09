"""
Auth API Endpoints
Login, Register, Refresh Token, Logout, Me
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.api.auth.service import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.api.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    MessageResponse,
    RefreshTokenRequest,
)
from app.schemas.product import SellerResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate user with email and password.
    Returns access_token and refresh_token.
    """
    # Find user by email
    user = db.query(Seller).filter(Seller.email == credentials.email).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=SellerResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user with email and password.
    Returns access_token and refresh_token.
    """
    # Check if user already exists
    existing = db.query(Seller).filter(Seller.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {data.email} already exists",
        )

    # Create new user
    user = Seller(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        name=data.name or data.email.split("@")[0],
        seller_id=f"SELLER-{data.email.split('@')[0].upper()}",
        marketplace_id="ARBP9OOSHTCHU",  # Default Egypt
        region="EU",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"New user registered: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=SellerResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh an access token using a refresh token.
    """
    # Validate refresh token
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Get user
    from uuid import UUID
    user = db.query(Seller).filter(Seller.id == UUID(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=SellerResponse.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: Seller = Depends(get_current_user),
):
    """
    Logout the current user.
    In a production setup, you might want to blacklist the token.
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=SellerResponse)
async def get_me(
    current_user: Seller = Depends(get_current_user),
):
    """
    Get the current authenticated user's profile.
    """
    return SellerResponse.model_validate(current_user)
