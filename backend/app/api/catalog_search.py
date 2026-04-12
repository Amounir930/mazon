"""
Amazon Catalog Search API Endpoints
البحث في كتالوج Amazon باستخدام niquests + BeautifulSoup
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from loguru import logger

from app.services.catalog_search import AmazonCatalogSearchClient, get_active_session

router = APIRouter()


@router.get("/search")
async def search_catalog(
    query: str = Query(..., description="كلمة البحث (ASIN, UPC, Keywords, Product Name)"),
    search_type: str = Query("KEYWORD", description="نوع البحث: KEYWORD, ASIN, UPC, EAN"),
):
    """
    البحث في كتالوج Amazon Seller Central.

    أنواع البحث:
    - KEYWORD: البحث بكلمة مفتاحية
    - ASIN: البحث بـ ASIN (مثال: B08XYZ1234)
    - UPC: البحث بـ UPC Barcode
    - EAN: البحث بـ EAN Barcode

    Request: GET /api/v1/catalog/search?query=iphone&search_type=KEYWORD
    """
    try:
        # Get active session cookies
        cookies, country = get_active_session()
        if not cookies:
            raise HTTPException(
                status_code=401,
                detail="لا يوجد جلسة نشطة - يرجى تسجيل الدخول أولاً"
            )

        # Initialize search client
        client = AmazonCatalogSearchClient(country_code=country)
        client.setup_cookies(cookies)

        # Execute search based on type
        results = []

        if search_type.upper() == "ASIN":
            result = client.search_by_asin(query)
            if result:
                results = [result] if isinstance(result, dict) else result
        elif search_type.upper() in ("UPC", "EAN"):
            results = client.search_by_keyword(query)
        else:
            # Default: KEYWORD search
            results = client.search_by_keyword(query)

        logger.info(f"Catalog search: '{query}' ({search_type}) → {len(results)} results")

        return {
            "success": True,
            "query": query,
            "search_type": search_type,
            "total": len(results),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog search failed: {e}")
        raise HTTPException(status_code=500, detail=f"فشل البحث: {str(e)}")


@router.get("/lookup/{asin}")
async def lookup_asin(asin: str):
    """
    البحث عن منتج محدد بواسطة ASIN.

    Request: GET /api/v1/catalog/lookup/B08XYZ1234
    """
    try:
        cookies, country = get_active_session()
        if not cookies:
            raise HTTPException(
                status_code=401,
                detail="لا يوجد جلسة نشطة - يرجى تسجيل الدخول أولاً"
            )

        client = AmazonCatalogSearchClient(country_code=country)
        client.setup_cookies(cookies)

        result = client.search_by_asin(asin)

        if not result:
            return {
                "success": False,
                "message": "لم يتم العثور على المنتج",
                "asin": asin,
            }

        return {
            "success": True,
            "asin": asin,
            "product": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ASIN lookup failed: {e}")
        raise HTTPException(status_code=500, detail=f"فشل البحث: {str(e)}")
