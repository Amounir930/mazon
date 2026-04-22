from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.amazon_mirror_service import AmazonMirrorService
from app.services.sp_api_client import SPAPIClient
from app.config import get_settings

router = APIRouter()

def get_mirror_service():
    settings = get_settings()
    client = SPAPIClient(
        marketplace_id=settings.SP_API_MARKETPLACE_ID,
        country_code=settings.SP_API_COUNTRY
    )
    return AmazonMirrorService(client)

@router.get("/metrics")
async def get_metrics(
    days: int = 30,
    service: AmazonMirrorService = Depends(get_mirror_service)
):
    """
    Get aggregated dashboard metrics and chart data
    """
    try:
        data = await service.get_dashboard_summary(days=days)
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync")
async def force_sync(service: AmazonMirrorService = Depends(get_mirror_service)):
    """
    Forces a fresh sync from Amazon (ignores cache).
    """
    try:
        # Clear cache for this service instance (simple reset)
        service._cache = {}
        data = await service.get_dashboard_summary()
        return {
            "success": True,
            "message": "Dashboard synced with Amazon",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
