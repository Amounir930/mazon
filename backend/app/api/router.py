"""
API Router Configuration
Aggregates all route routers
"""
from fastapi import APIRouter
from app.api import sellers, products, listings, feeds, auth

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sellers.router, prefix="/sellers", tags=["sellers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
