import os
import sys
import json
import time
from datetime import datetime, timedelta, timezone
from loguru import logger

# Add backend to path to use SPAPIClient
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.sp_api_client import SPAPIClient
from app.config import get_settings

def test_direct_orders():
    settings = get_settings()
    logger.info("🚀 Starting Direct Amazon Orders Test...")
    
    client = SPAPIClient(
        marketplace_id=settings.SP_API_MARKETPLACE_ID,
        country_code=settings.SP_API_COUNTRY
    )
    
    # Test 1: Get Orders with standard params
    created_after = (datetime.now(timezone.utc) - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # We will try different parameter formats
    test_params = [
        {
            "name": "Standard MarketplaceIds (Single String)",
            "params": {
                "MarketplaceIds": settings.SP_API_MARKETPLACE_ID,
                "CreatedAfter": created_after
            }
        },
        {
            "name": "Lowercase marketplaceIds (like Sales API)",
            "params": {
                "marketplaceIds": settings.SP_API_MARKETPLACE_ID,
                "CreatedAfter": created_after
            }
        },
        {
            "name": "MarketplaceIds without CreatedAfter",
            "params": {
                "MarketplaceIds": settings.SP_API_MARKETPLACE_ID
            }
        }
    ]
    
    # Final Comparative Test: Prove Sales Works while Orders Fails
    logger.info("--- Final Comparison: Testing Sales API (Expected 200) ---")
    try:
        sales_params = {
            "marketplaceIds": settings.SP_API_MARKETPLACE_ID,
            "interval": (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ') + "--" + datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "granularity": "Day"
        }
        response = client._make_request("GET", "/sales/v1/orderMetrics", params=sales_params)
        logger.success("✅ Sales API is WORKING (200 OK). Connection is verified.")
    except Exception as e:
        logger.error(f"❌ Sales API also failed: {str(e)}")

    logger.info("--- Final Comparison: Testing Orders API (Expected 403) ---")
    try:
        response = client._make_request("GET", "/orders/v1/orders", params={"MarketplaceIds": settings.SP_API_MARKETPLACE_ID})
        if "errors" in response and any(e.get('code') == 'Unauthorized' for e in response['errors']):
             logger.error("❌ Orders API is BLOCKED (403 Forbidden).")
    except Exception as e:
        logger.error(f"❌ Orders API failed: {str(e)}")

if __name__ == "__main__":
    test_direct_orders()
