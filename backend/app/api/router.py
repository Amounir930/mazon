"""
API Router Configuration
Aggregates all route routers
"""
from fastapi import APIRouter
from app.api import sellers, products, listings, feeds, tasks
# New v3.0 modules (will be created in later phases)
# from app.api import amazon_connect, products_sync, bulk_upload

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(sellers.router, prefix="/sellers", tags=["sellers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# TODO (Phase 4): Uncomment when modules are created
# api_router.include_router(amazon_connect.router, prefix="/amazon", tags=["amazon"])
# api_router.include_router(products_sync.router, prefix="/sync", tags=["sync"])
# api_router.include_router(bulk_upload.router, prefix="/bulk", tags=["bulk"])
