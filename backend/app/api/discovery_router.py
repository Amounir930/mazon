from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_sp_api_client
from app.services.discovery_service import DiscoveryService
from app.services.sp_api_client import SPAPIClient

router = APIRouter()

def get_discovery_service(client: SPAPIClient = Depends(get_sp_api_client)):
    return DiscoveryService(client)

@router.get("/top-items")
async def get_top_items(
    keywords: str = Query("bestsellers", description="Search keywords"),
    category: str = Query(None, description="Category ID (classificationId)"),
    service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Find top selling items on Amazon (Pure Stateless / Live).
    """
    items = await service.get_amazon_top_sellers(keywords=keywords, category=category)
    return {
        "success": True,
        "count": len(items),
        "data": items
    }
