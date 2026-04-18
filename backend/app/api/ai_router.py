"""
AI Product Generation API Router
==================================
Async endpoints for AI-powered product generation + Amazon catalog import.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from app.services.ai_product_assistant import AIProductAssistant
from app.schemas.ai import AIProductRequest
from app.services.sp_api_client import SPAPIClient
from app.database import SessionLocal
from app.models.product import Product

router = APIRouter()


# ... existing generate_product endpoint ...


class AmazonImportRequest(BaseModel):
    """Request to import product from Amazon by ASIN/UPC/EAN"""
    search_value: str  # ASIN, UPC, or EAN
    search_type: str = "ASIN"  # ASIN, UPC, EAN


@router.post("/import-from-amazon")
async def import_from_amazon(request: AmazonImportRequest):
    """
    POST /api/v1/ai/import-from-amazon

    Search Amazon catalog by ASIN/UPC/EAN and return product data for import.

    Request Body:
    {
        "search_value": "B0XXXXXXXX",
        "search_type": "ASIN"  // or "UPC" or "EAN"
    }

    Response:
    {
        "found": true,
        "asin": "B0XXXXXXXX",
        "title": "Product Title",
        "brand": "Brand Name",
        "bullet_points": ["...", "..."],
        "description": "...",
        "images": ["..."],
        "price_estimate": 100,
        "product_type": "..."
    }
    """
    try:
        client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')

        if request.search_type == "ASIN":
            # Direct ASIN lookup
            result = client.get_catalog_item(
                asin=request.search_value,
                included_data=["summaries", "images", "identifiers", "dimensions"]
            )
            items = [result] if result.get("asin") else []
        else:
            # Search by UPC/EAN
            result = client.search_catalog_items(
                identifiers=[request.search_value],
                identifiers_type=request.search_type,  # EAN, UPC, etc.
                included_data=["summaries", "images", "identifiers"]
            )
            items = result.get("items", [])

        if not items:
            return {
                "found": False,
                "message": "لم يتم العثور على المنتج في Amazon"
            }

        item = items[0]
        asin = item.get("asin", "")
        summaries = item.get("summaries", [{}])
        summary = summaries[0] if summaries else {}

        # Extract product data
        product_data = {
            "found": True,
            "asin": asin,
            "title": summary.get("title", ""),
            "brand": summary.get("brand", "Generic"),
            "bullet_points": summary.get("bulletPoints", []),
            "description": summary.get("productDescription", ""),
            "images": [img.get("link", "") for img in item.get("images", [])[:9] if img.get("link")],
            "product_type": summary.get("productType", ""),
            "manufacturer": summary.get("manufacturer", ""),
            "country_of_origin": summary.get("countryOfOrigin", ""),
            "item_weight": summary.get("itemWeight", {}),
            "dimensions": item.get("dimensions", {}),
        }

        return product_data

    except Exception as e:
        logger.error(f"Amazon import failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل الاستيراد: {str(e)}"
        )


@router.get("/learned-fields/{product_id}")
async def get_learned_fields(product_id: str):
    """
    GET /api/v1/ai/learned-fields/{product_id}
    
    Get fields that were previously rejected by Amazon for this product.
    """
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(404, "Product not found")
        
        learned_fields = []
        rejection_history = []
        
        if product.optimized_data:
            import json as _json
            opt_data = _json.loads(product.optimized_data) if isinstance(product.optimized_data, str) else product.optimized_data
            learned_fields = opt_data.get("learned_fields", [])
            rejection_history = opt_data.get("rejection_history", [])
        
        return {
            "product_id": product_id,
            "learned_fields": learned_fields,
            "rejection_count": len(rejection_history),
            "rejection_history": rejection_history[-5:],  # Last 5 rejections
        }
    finally:
        db.close()


@router.post("/generate-product")
async def generate_product(request: AIProductRequest):
    """
    POST /api/v1/ai/generate-product
    """
    # DEBUG: Log request for troubleshooting
    logger.info(f"📥 AI generate request: name='{request.name}' (len={len(request.name)}), specs='{request.specs[:50]}...' (len={len(request.specs)}), copies={request.copies}")

    # Validate copies range
    if request.copies < 1 or request.copies > 10:
        raise HTTPException(
            status_code=400,
            detail="عدد المنتجات يجب أن يكون بين 1 و 10"
        )
    
    try:
        assistant = AIProductAssistant()
        result = await assistant.generate_products(
            name=request.name,
            specs=request.specs,
            copies=request.copies,
        )

        # DEBUG: Log AI response for troubleshooting
        logger.info(f"✅ AI generated {len(result.variants)} variant(s)")
        logger.info(f"   base_product: brand={result.base_product.brand}, product_type={result.base_product.product_type}")
        
        # Build response matching frontend expectations
        return {
            "success": True,
            "data": {
                "base_product": result.base_product.model_dump(),
                "variants": [v.model_dump() for v in result.variants],
            },
            "validation_errors": [],
            "warnings": [],
            "fallback_used": False,
            "metadata": {
                "model_used": "qwen-max",
                "tokens_used": None,
                "processing_time_ms": None,
            }
        }
        
    except ValueError as e:
        logger.error(f"AI generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"فشل التوليد: {str(e)}",
            "data": None,
            "validation_errors": [],
            "warnings": [],
        }
    except Exception as e:
        logger.error(f"Unexpected error in AI generation: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "خطأ غير متوقع في التوليد — حاول مرة أخرى",
            "data": None,
            "validation_errors": [],
            "warnings": [],
        }
