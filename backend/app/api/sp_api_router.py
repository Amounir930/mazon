"""
SP-API Router
Handles all Amazon SP-API operations through our backend
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from loguru import logger

# Load .env file from backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.database import SessionLocal
from app.models.product import Product
from app.models.listing import Listing
from app.models.seller import Seller
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data
from app.services.sp_api_client import SPAPIClient
from app.tasks.polling_tasks import poll_listing_status
from app.api.dependencies import get_sp_api_client, get_seller_id_from_session
from datetime import datetime
import json

router = APIRouter()


class SubmitToListingsRequest(BaseModel):
    product_id: str


@router.post("/submit/{product_id}")
async def submit_product_to_amazon(product_id: str, background_tasks: BackgroundTasks):
    """
    Submit a product from our database to Amazon via SP-API.

    Flow:
    1. Get product from DB
    2. Get active session (cookies + credentials)
    3. Build SP-API payload
    4. PUT /listings/2021-08-01/items/{sellerId}/{sku}
    5. Create listing record in DB
    6. Return result
    """
    db = SessionLocal()
    try:
        # 1. Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        logger.info(f"Submitting product to Amazon: {product.sku} — {product.name}")

        # 2. Validate product has required fields
        if not product.ean and not product.upc:
            raise HTTPException(
                status_code=400,
                detail="المنتج محتاج باركود (EAN أو UPC) عشان يترفع على أمازون"
            )

        if not product.price or product.price <= 0:
            raise HTTPException(
                status_code=400,
                detail="المنتج محتاج سعر أكبر من صفر"
            )

        if product.quantity is None or product.quantity < 0:
            raise HTTPException(
                status_code=400,
                detail="المنتج محتاج كمية صحيحة"
            )

        # 3. Get active session (for marketplace/country info) — fallback to ENV
        import os
        
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
            AuthSession.is_valid == True,
        ).order_by(AuthSession.created_at.desc()).first()

        # 4. Get Seller credentials — from session OR fallback to ENV
        seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")
        
        if auth_session and auth_session.credentials_json:
            credentials = json.loads(decrypt_data(auth_session.credentials_json))
            seller_id = credentials.get("seller_id", seller_id)
            logger.info(f"✅ Using session credentials: seller={seller_id}")
        else:
            logger.warning(f"⚠️ No credentials in session — using ENV fallback (seller={seller_id})")
        
        marketplace_id = auth_session.marketplace_id if auth_session else os.getenv("SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU") or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code if auth_session else os.getenv("SP_API_COUNTRY", "eg") or "eg"

        # 5. Create listing record (status: processing)
        listing = Listing(
            product_id=product.id,
            seller_id=product.seller_id,
            status="processing",
            stage="submitting",
            submitted_at=datetime.utcnow(),
            sp_api_submission_id=None,
        )
        db.add(listing)
        db.commit()

        # 6. Build product data for SP-API
        # Parse attributes JSON safely
        try:
            product_attrs = json.loads(product.attributes) if isinstance(product.attributes, str) else {}
        except Exception:
            product_attrs = {}

        # Parse bullet_points JSON string if needed
        bullet_points = product.bullet_points
        if isinstance(bullet_points, str):
            try:
                bullet_points = json.loads(bullet_points)
            except Exception:
                bullet_points = []
        if not isinstance(bullet_points, list):
            bullet_points = []

        product_data = {
            "sku": product.sku,
            "name": product.name or product.name_en or "Unnamed Product",
            "description": product.description or product.name or "No description",
            "brand": product.brand or "Generic",
            "manufacturer": product.manufacturer or (product.brand or "Generic"),
            "model_number": product.model_number or product.sku,
            "ean": product.ean or "",
            "upc": product.upc or "",
            "price": float(product.price),
            "quantity": int(product.quantity),
            "condition": product.condition or "New",
            "fulfillment_channel": product.fulfillment_channel or "MFN",
            "country_of_origin": product.country_of_origin or "CN",
            "product_type": product.product_type or "HOME_ORGANIZERS_AND_STORAGE",
            "bullet_points": bullet_points,
            "browse_node_id": product.browse_node_id or "21863799031",
            # Merchant suggested ASIN — from product attributes or fallback to SKU (max 10 chars!)
            "merchant_suggested_asin": (product_attrs.get("suggested_asin") or product_attrs.get("merchant_suggested_asin") or product.sku)[:10].strip(),
        }

        # 7. Initialize SP-API client
        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)

        # 8. Create listing on Amazon
        result = client.create_listing_from_product(
            seller_id=seller_id,
            sku=product.sku,
            product_data=product_data,
        )

        # 9. Update listing record
        listing.sp_api_submission_id = result.get("submissionId", "")
        listing.sp_api_status = result.get("status", "UNKNOWN")

        if result.get("success"):
            listing.status = "success"
            listing.stage = "accepted"
            listing.amazon_asin = result.get("asin", "")
            listing.completed_at = datetime.utcnow()
            logger.info(f"✅ Listing success: {product.sku} → {listing.amazon_asin}")
        else:
            errors = result.get("errors", [])
            error_messages = [e.get("message", "Unknown error") for e in errors]
            listing.status = "failed"
            listing.stage = "rejected"
            listing.error_message = "\n".join(error_messages)[:500]
            listing.completed_at = datetime.utcnow()
            logger.error(f"❌ Listing failed: {product.sku} — {error_messages}")

        db.commit()

        # 10. Queue background polling if success
        if result.get("success"):
            background_tasks.add_task(
                poll_listing_status,
                sku=product.sku,
                seller_id=seller_id,
                listing_id=listing.id,
            )

        # 11. Return result
        return {
            "success": result.get("success", False),
            "listing_id": listing.id,
            "submission_id": listing.sp_api_submission_id,
            "status": listing.sp_api_status,
            "asin": listing.amazon_asin,
            "errors": result.get("errors", []),
            "message": "تم إرسال المنتج لأمزون بنجاح" if result.get("success") else "فشل إرسال المنتج — راجع الأخطاء",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"SP-API submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"خطأ في الإرسال: {str(e)}")
    finally:
        db.close()


@router.get("/listing/{sku}")
async def get_listing_status(sku: str):
    """Get listing status from Amazon SP-API"""
    db = SessionLocal()
    try:
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
        ).order_by(AuthSession.created_at.desc()).first()

        if not auth_session:
            raise HTTPException(status_code=400, detail="No active session")

        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        seller_id = credentials.get("seller_id", "A1DSHARRBRWYZW")
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"

        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        result = client.get_listing_item(seller_id, sku)

        return {
            "sku": sku,
            "status": result.get("status", "UNKNOWN"),
            "asin": result.get("asin", ""),
            "data": result,
        }
    except Exception as e:
        logger.error(f"Get listing status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/schema/{product_type}")
async def get_product_type_schema(product_type: str):
    """Get required attributes for a product type from Amazon"""
    db = SessionLocal()
    try:
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
        ).order_by(AuthSession.created_at.desc()).first()

        if not auth_session:
            raise HTTPException(status_code=401, detail="No active session — please log in to Amazon first")

        if not auth_session.credentials_json:
            raise HTTPException(status_code=401, detail="Session credentials missing — please reconnect")

        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"

        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        schema = client.get_product_type_definitions(product_type)

        # Extract required attributes
        required_attrs = []
        if isinstance(schema, dict):
            requirements = schema.get("requirements", {})
            if isinstance(requirements, dict):
                listing_reqs = requirements.get("LISTING", {})
                for attr_name, attr_info in listing_reqs.items():
                    if isinstance(attr_info, dict) and attr_info.get("required", False):
                        required_attrs.append(attr_name)

        return {
            "product_type": product_type,
            "required_attributes": required_attrs,
            "full_schema": schema,
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Get schema error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Schema fetch failed: {str(e)}")
    finally:
        db.close()


# ============================================================
# NEW: Dependency-Injected Endpoints (Phase 1)
# ============================================================


@router.delete("/listing/{seller_id}/{sku}")
async def delete_listing(
    seller_id: str,
    sku: str,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Delete a listing from Amazon SP-API.

    API: DELETE /listings/2021-08-01/items/{sellerId}/{sku}
    Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#deletelistingsitem
    """
    try:
        result = client.delete_listing_item(seller_id, sku)

        return {
            "success": True,
            "status": result.get("status", "ACCEPTED"),
            "message": f"Listing deleted: SKU={sku}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listings")
async def search_listings(
    seller_id: Optional[str] = None,
    skus: Optional[str] = None,
    status: Optional[str] = None,
    page_size: int = 10,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Search all Amazon listings for a seller.

    Query params:
    - seller_id: Amazon Seller ID (optional — defaults to session seller)
    - skus: Comma-separated SKUs to filter (optional)
    - status: ACTIVE, INCOMPLETE, or INACTIVE (optional)
    - page_size: Number of results (default: 10, max: 200)

    Dependency Injection handles:
    - Session lookup
    - Credential decryption
    - Client initialization
    """
    try:
        # If no seller_id provided, get from session
        if not seller_id:
            seller_id_dep = Depends(get_seller_id_from_session)
            # We can't use Depends inside another function, so we need to
            # call the dependency manually through the FastAPI dependency system.
            # For simplicity, let's use a direct session query here as fallback.
            db = SessionLocal()
            try:
                auth_session = db.query(AuthSession).filter(
                    AuthSession.auth_method == "browser",
                    AuthSession.is_active == True,
                ).order_by(AuthSession.created_at.desc()).first()

                if not auth_session or not auth_session.credentials_json:
                    raise HTTPException(status_code=401, detail="No active session with credentials")

                credentials = json.loads(decrypt_data(auth_session.credentials_json))
                seller_id = credentials.get("seller_id")
                if not seller_id:
                    raise HTTPException(status_code=400, detail="Seller ID not found in session")
            finally:
                db.close()

        result = client.search_listings_items(
            seller_id=seller_id,
            skus=skus.split(",") if skus else None,
            status=status,
            page_size=page_size,
        )

        items = result.get("items", [])
        return {
            "success": True,
            "seller_id": seller_id,
            "total_results": len(items),
            "items": items,
            "pagination": result.get("pagination", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search listings error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# PATCH Endpoint (Phase 2 - Ready)
# ============================================================


class PatchListingRequest(BaseModel):
    """Request body for PATCH listing endpoint"""
    product_type: str
    patches: List[dict]


@router.patch("/listing/{seller_id}/{sku}")
async def patch_listing(
    seller_id: str,
    sku: str,
    request: PatchListingRequest,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Partial update of a listing (e.g., price or quantity only).

    Patches format:
    [
        {"op": "replace", "path": "/attributes/purchasable_offer/0/our_price/0/schedule/0/value_with_tax", "value": 150},
        {"op": "replace", "path": "/attributes/quantity/0/value", "value": 50}
    ]

    ⚠️  productType is REQUIRED (per Amazon SP-API spec).
    """
    try:
        if not request.patches:
            raise HTTPException(status_code=400, detail="patches array is required")

        if not request.product_type:
            raise HTTPException(status_code=400, detail="productType is required")

        result = client.patch_listing_item(
            seller_id=seller_id,
            sku=sku,
            product_type=request.product_type,
            patches=request.patches,
        )

        issues = result.get("issues", [])
        errors = [i for i in issues if i.get("severity") == "ERROR"]

        return {
            "success": len(errors) == 0,
            "status": result.get("status", "UNKNOWN"),
            "sku": sku,
            "errors": errors,
            "message": "Listing updated" if len(errors) == 0 else "Patch failed — see errors",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Patch listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Catalog SP-API Endpoints (Phase 3)
# ============================================================


@router.get("/catalog/search")
async def search_catalog_sp_api(
    keywords: Optional[str] = None,
    identifiers: Optional[str] = None,
    page_size: int = 10,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Search Amazon catalog via SP-API (official replacement for scraping).

    Query params:
    - keywords: Search terms (e.g., "wireless headphones")
    - identifiers: Comma-separated EAN/UPC/ISBN/ASIN (optional)
    - page_size: Results count (default: 10, max: 20)

    Returns official catalog data: summaries, images, dimensions, identifiers.
    """
    try:
        result = client.search_catalog_items(
            keywords=keywords,
            identifiers=identifiers.split(",") if identifiers else None,
            page_size=page_size,
            included_data=["summaries", "images", "identifiers", "dimensions"],
        )

        return {
            "success": True,
            "method": "SP-API",
            "total_results": result.get("numberOfResults", 0),
            "items": result.get("items", []),
            "pagination": result.get("pagination", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog/{asin}")
async def get_catalog_item_sp_api(
    asin: str,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Get catalog item details by ASIN via SP-API.

    Returns full product info: summaries, images, dimensions, identifiers.
    """
    try:
        result = client.get_catalog_item(
            asin=asin,
            included_data=["summaries", "images", "identifiers", "dimensions", "links"],
        )

        return {
            "success": True,
            "method": "SP-API",
            "asin": asin,
            "item": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog lookup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
