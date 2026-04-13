"""
API Router Configuration
Aggregates all route routers
"""
from fastapi import APIRouter
from app.api import sellers, products, listings, feeds, tasks, amazon_connect, products_sync, bulk_upload, auth_routes, activity_log, price_updates, export_templates, catalog_search, images, sp_api_router

api_router = APIRouter()

# Include all sub-routers
# NOTE: order matters! More specific routes first, then generic ones
api_router.include_router(auth_routes.router, prefix="")
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(amazon_connect.router, prefix="/amazon", tags=["amazon"])
api_router.include_router(sellers.router, prefix="/sellers", tags=["sellers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(price_updates.router, prefix="/products", tags=["price-updates"])
api_router.include_router(export_templates.router, prefix="/export", tags=["export"])
api_router.include_router(catalog_search.router, prefix="/catalog", tags=["catalog-search"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
api_router.include_router(products_sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(bulk_upload.router, prefix="/bulk", tags=["bulk"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(activity_log.router, prefix="/products", tags=["activity-log"])
api_router.include_router(sp_api_router.router, prefix="/sp-api", tags=["sp-api"])
