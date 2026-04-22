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

from app.database import SessionLocal, get_db
from app.models.product import Product
from app.models.listing import Listing
from app.models.seller import Seller
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data
from app.services.sp_api_client import SPAPIClient
from app.tasks.polling_tasks import poll_listing_status
from app.api.dependencies import get_sp_api_client, get_seller_id_from_session
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime
import json
import uuid


def _parse_images(images_field) -> List[str]:
    """
    Parse images field from DB — handles both JSON string and list formats.
    
    DB stores images as JSON string: '["url1", "url2"]'
    But sometimes it comes as raw string or list.
    """
    if not images_field:
        return []
    
    # If it's already a list, return it
    if isinstance(images_field, list):
        return images_field
    
    # If it's a string, try to parse as JSON
    if isinstance(images_field, str):
        try:
            parsed = json.loads(images_field)
            if isinstance(parsed, list):
                return parsed
            # Single URL string
            return [images_field] if images_field.startswith("https://") else []
        except json.JSONDecodeError:
            # Not JSON — treat as single URL
            return [images_field] if images_field.startswith("https://") else []
    
    return []

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
        if not product.ean and not product.upc and not getattr(product, "has_product_identifier", False):
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
            "color": product_attrs.get("color", "متعدد") or "متعدد",
            "manufacturer": product.manufacturer or (product.brand or "Generic"),
            "model_number": product.model_number or product.sku,
            "model_name": product_attrs.get("model_name") or product.model_number or product.sku,
            "ean": product.ean or "",
            "upc": product.upc or "",
            "price": float(product.price),
            "quantity": int(product.quantity),
            "condition": product.condition or "New",
            "fulfillment_channel": product.fulfillment_channel or "MFN",
            "country_of_origin": product.country_of_origin or "CN",
            "product_type": product.product_type or "HOME_ORGANIZERS_AND_STORAGE",
            "amazon_product_type": product_attrs.get("amazon_product_type") or getattr(product, "amazon_product_type", None) or product.product_type,
            "bullet_points": bullet_points,
            "browse_node_id": product.browse_node_id or "21863799031",
            # Merchant suggested ASIN 
            "merchant_suggested_asin": (product_attrs.get("suggested_asin") or product_attrs.get("merchant_suggested_asin") or product.ean or "")[:10].strip(),
            # Additional required fields
            "number_of_items": product.number_of_items or 1,
            "package_quantity": product.package_quantity or 1,
            "material": product.material or "",
            "target_audience": product.target_audience or "",
            # IMAGES — parse JSON string if needed (stored as JSON in DB)
            "images": _parse_images(product.images),
            "has_product_identifier": getattr(product, "has_product_identifier", False) or (not product.ean and not product.upc),
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

    ⚠️  Amazon archives the listing (not permanent deletion).
        The SKU can be recreated with a new PUT/PATCH request.

    API: DELETE /listings/2021-08-01/items/{sellerId}/{sku}
    """
    try:
        result = client.delete_listing_item(seller_id, sku)

        # Amazon returns ACCEPTED but may not delete immediately
        # Verify by trying to fetch the listing
        import time
        time.sleep(1)  # Wait for Amazon to process
        try:
            verify = client.get_listing_item(seller_id, sku)
            status = verify.get("status", "UNKNOWN")
            if status == "ACCEPTED" or "issues" in verify:
                # Listing still exists — might be archived
                message = f"Listing archived on Amazon: SKU={sku} (can be recreated)"
            else:
                message = f"Listing deleted: SKU={sku}"
        except Exception:
            message = f"Listing deleted: SKU={sku}"

        return {
            "success": True,
            "status": result.get("status", "ACCEPTED"),
            "sku": sku,
            "message": message,
            "note": "Amazon archives listings — SKU can be recreated later",
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
            # For simplicity, we query the session directly here.
            db = SessionLocal()
            try:
                auth_session = db.query(AuthSession).filter(
                    AuthSession.auth_method == "browser",
                    AuthSession.is_active == True,
                ).order_by(AuthSession.created_at.desc()).first()

                if not auth_session or not auth_session.credentials_json:
                    # Fallback to ENV
                    seller_id = os.getenv("SP_API_SELLER_ID")
                else:
                    credentials = json.loads(decrypt_data(auth_session.credentials_json))
                    seller_id = credentials.get("seller_id")
                
                if not seller_id:
                    raise HTTPException(status_code=401, detail="Seller ID not found. Please log in or set SP_API_SELLER_ID in .env")
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

        # Amazon returns 'issues' for ACCEPTED responses, but 'errors' for 400 responses
        issues = result.get("issues", [])
        amazon_errors = result.get("errors", [])

        # Extract error messages
        error_msgs = []
        for err in amazon_errors + issues:
            if err.get("severity") == "ERROR" or err.get("code") in ("InvalidInput", "BadRequest"):
                error_msgs.append(err.get("message", err.get("code", "Unknown error")))

        if result.get("status") == "INVALID" or amazon_errors:
            return {
                "success": False,
                "status": result.get("status", "FAILED"),
                "sku": sku,
                "errors": amazon_errors + issues,
                "message": f"Patch failed: {'; '.join(error_msgs)}",
            }

        return {
            "success": True,
            "status": result.get("status", "ACCEPTED"),
            "sku": sku,
            "errors": [],
            "message": "Listing updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Patch listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Diagnostic: View Raw Amazon Listing Data
# ============================================================


@router.get("/debug/listing/{sku}")
async def debug_listing(
    sku: str,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Diagnostic endpoint — returns RAW Amazon listing data + what we store locally.
    Use this to verify what fields Amazon actually returns.
    """
    seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")

    # Get raw Amazon data
    amazon_raw = client.get_listing_item(seller_id, sku)

    # Get local DB data
    product = None
    from app.database import SessionLocal as make_db
    db = make_db()
    try:
        product = db.query(Product).filter(Product.sku == sku).first()
    finally:
        db.close()

    # Extract what we currently use
    attrs = amazon_raw.get("attributes", {})
    extracted = {
        "price": None,
        "quantity": None,
        "description": None,
        "bullet_points": [],
        "manufacturer": None,
        "model_number": None,
        "country_of_origin": None,
        "ean": None,
        "upc": None,
        "images": [],
        "brand": None,
        "item_name": None,
        "product_type": None,
        "condition_type": None,
        "browse_nodes": None,
        "item_weight": None,
        "unit_count": None,
        "number_of_boxes": None,
        "included_components": None,
    }

    # Extract price
    offer = attrs.get("purchasable_offer", [])
    if offer and len(offer) > 0:
        our_price = offer[0].get("our_price", [])
        if our_price and len(our_price) > 0:
            schedule = our_price[0].get("schedule", [])
            if schedule and len(schedule) > 0:
                extracted["price"] = schedule[0].get("value_with_tax")
        extracted["currency"] = offer[0].get("currency")

    # Extract quantity
    qty_attrs = attrs.get("quantity", [])
    if qty_attrs and len(qty_attrs) > 0:
        extracted["quantity"] = qty_attrs[0].get("value")

    # Extract description
    desc_list = attrs.get("product_description", [])
    if desc_list and len(desc_list) > 0:
        extracted["description"] = desc_list[0].get("value")

    # Extract bullet points
    bp_list = attrs.get("bullet_point", [])
    extracted["bullet_points"] = [bp.get("value", "") for bp in bp_list]

    # Extract brand & name
    brand_list = attrs.get("brand", [])
    if brand_list:
        extracted["brand"] = brand_list[0].get("value")

    name_list = attrs.get("item_name", [])
    if name_list:
        extracted["item_name"] = name_list[0].get("value")

    # Extract images
    main_img = attrs.get("main_product_image_id", [])
    if main_img:
        img_id = main_img[0].get("value", "")
        if img_id:
            extracted["images"].append(f"https://m.media-amazon.com/images/I/{img_id}.jpg")

    other_imgs = attrs.get("other_product_image_id", [])
    for img in other_imgs:
        img_id = img.get("value", "")
        if img_id:
            extracted["images"].append(f"https://m.media-amazon.com/images/I/{img_id}.jpg")

    # Extract additional fields
    for field in ["manufacturer", "model_number", "country_of_origin", "product_type", "condition_type", "item_weight", "unit_count", "number_of_boxes", "included_components", "browse_nodes"]:
        field_data = attrs.get(field, [])
        if field_data and len(field_data) > 0:
            extracted[field] = field_data[0].get("value")

    # Extract EAN/UPC
    ext_id = attrs.get("externally_assigned_product_identifier", [])
    if ext_id:
        extracted["ean"] = ext_id[0].get("value") if ext_id[0].get("type") == "ean" else None
        extracted["upc"] = ext_id[0].get("value") if ext_id[0].get("type") == "upc" else None
    
    # Check for GTIN exemption
    gtin_exempt = attrs.get("supplier_declared_has_product_identifier_exemption", [])
    if gtin_exempt and len(gtin_exempt) > 0:
        extracted["has_product_identifier"] = gtin_exempt[0].get("value", False)

    return {
        "sku": sku,
        "amazon_raw_status": amazon_raw.get("status", "UNKNOWN"),
        "amazon_attributes_count": len(attrs),
        "amazon_attribute_keys": list(attrs.keys()),
        "extracted_fields": extracted,
        "local_product": {
            "exists": product is not None,
            "price": str(product.price) if product and product.price else None,
            "quantity": product.quantity if product else None,
            "description": product.description[:100] if product and product.description else None,
            "bullet_points": product.bullet_points[:200] if product and product.bullet_points else None,
            "images_count": len(json.loads(product.images)) if product and product.images else 0,
            "images": json.loads(product.images) if product and product.images else [],
        } if product else None,
        "raw_attributes_preview": {k: str(v)[:200] for k, v in list(attrs.items())[:5]},
        "image_fields_full": {
            k: attrs.get(k, [])
            for k in ["main_product_image_locator", "other_product_image_locator_1", "other_product_image_locator_2", "other_product_image_locator_3", "other_product_image_locator_4", "other_product_image_locator_5"]
        },
        "full_amazon_raw_keys": list(amazon_raw.keys()),
    }


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


# ============================================================
# Diagnostic: Test Full Sync for One SKU
# ============================================================


@router.post("/debug/full-sync-test/{sku}")
async def debug_full_sync_test(
    sku: str,
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """Test full sync extraction for a single SKU. Returns exactly what would be saved."""
    seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")

    detail = client.get_listing_item(seller_id, sku)
    attrs = detail.get("attributes", {})
    issues = detail.get("issues", [])

    def attr_val(key, default=None):
        items = attrs.get(key, [])
        if items and len(items) > 0:
            return items[0].get("value", default)
        return default

    def get_image_url(key):
        items = attrs.get(key, [])
        if items and len(items) > 0:
            url = items[0].get("media_location", "")
            if url:
                return url
            val = items[0].get("value", "")
            if val:
                img_id = val.replace(".jpg", "").replace(".png", "")
                return f"https://m.media-amazon.com/images/I/{img_id}.jpg"
        return ""

    images_list = []
    main_img = get_image_url("main_product_image_locator")
    if main_img:
        images_list.append(main_img)
    for i in range(1, 6):
        img_url = get_image_url(f"other_product_image_locator_{i}")
        if img_url:
            images_list.append(img_url)

    return {
        "sku": sku,
        "attrs_keys_count": len(attrs),
        "attrs_keys": list(attrs.keys()),
        "issues": issues,
        "images_list": images_list,
        "main_img_raw": attrs.get("main_product_image_locator", "MISSING"),
        "other_1_raw": attrs.get("other_product_image_locator_1", "MISSING"),
    }


@router.post("/import-products")
async def import_products_from_amazon(
    limit: int = 100,
    full_sync: bool = False,
    db: Session = Depends(get_db),
    client: SPAPIClient = Depends(get_sp_api_client),
):
    """
    Import Amazon listings into the local database via SP-API.

    Query params:
    - limit: Max products to import (default: 100, max: 1000)
    - full_sync: If True, fetches FULL details (price, quantity, description) for each SKU

    Flow (basic):
    1. Fetch listings from Amazon (paginated)
    2. For each listing: check if exists → update or create (basic info only)

    Flow (full_sync=True):
    1. Fetch listings from Amazon (paginated)
    2. For EACH listing: call get_listing_item() → full details (price, qty, description)
    3. Update or create product with COMPLETE data
    4. Return import stats

    This replaces the scraping-based sync with official SP-API.
    """
    seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")
    limit = min(max(limit, 1), 1000)  # Clamp 1-1000

    # Get default seller from DB or create one
    seller = db.query(Seller).first()
    if not seller:
        seller = Seller(
            id=str(uuid.uuid4()),
            lwa_client_id=os.getenv("SP_API_CLIENT_ID", ""),
            lwa_client_secret=os.getenv("SP_API_CLIENT_SECRET", ""),
            lwa_refresh_token=os.getenv("SP_API_REFRESH_TOKEN", ""),
            amazon_seller_id=seller_id,
            display_name="Amazon SP-API Store",
            marketplace_id=os.getenv("SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU"),
            region="EU",
            is_connected=True,
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)

    # Phase 1: Fetch listings from Amazon (with pagination, up to limit)
    all_items = []
    page_size = min(200, limit)
    page = 0
    max_pages = max(1, (limit // page_size) + 1)

    while page < max_pages and len(all_items) < limit:
        page += 1
        remaining = limit - len(all_items)
        current_page_size = min(page_size, remaining)

        result = client.search_listings_items(
            seller_id=seller_id,
            page_size=current_page_size,
        )

        items = result.get("items", [])
        if not items:
            break

        all_items.extend(items)
        logger.info(f"Import page {page}: fetched {len(items)} (total: {len(all_items)}/{limit})")

        # Check for next page
        pagination = result.get("pagination", {})
        next_token = pagination.get("nextToken")
        if not next_token or len(all_items) >= limit:
            break

        # Fetch next page
        path = f"/listings/2021-08-01/items/{seller_id}"
        params = {
            "marketplaceIds": client.marketplace_id,
            "pageSize": current_page_size,
            "nextToken": next_token,
        }
        result = client._make_request("GET", path, params=params)
        items = result.get("items", [])
        if not items:
            break
        all_items.extend(items)

    logger.info(f"Phase 1 complete: {len(all_items)} listings fetched from Amazon")

    # Phase 2 (Full Sync): Fetch full details for each SKU
    if full_sync:
        logger.info(f"Phase 2: Fetching FULL details for {len(all_items)} SKUs...")

    # Import/update products in local DB
    created = 0
    updated = 0
    errors = 0
    full_details_fetched = 0

    for item in all_items:
        try:
            sku = item.get("sku", "")
            if not sku:
                continue

            # Start with basic data from search
            summary = item.get("summaries", [{}])[0] if item.get("summaries") else {}
            asin = item.get("asin", "") or summary.get("asin", "")
            item_name = summary.get("itemName", "") or sku
            brand = summary.get("brand", "")
            product_type = summary.get("productType", "")
            condition = summary.get("conditionType", "new_new")
            status_list = summary.get("status", [])

            # Extract main image
            main_image = ""
            if summary.get("mainImage"):
                main_image = summary["mainImage"].get("link", "")

            # Full details from get_listing_item
            price = 0
            quantity = 0
            description = ""
            description_en = ""
            bullet_points = []
            bullet_points_ar = []
            bullet_points_en = []
            manufacturer = ""
            model_number = ""
            country_of_origin = ""
            ean = ""
            upc = ""
            images_list = []
            extra_attrs = {}

            if full_sync:
                try:
                    detail = client.get_listing_item(seller_id, sku)
                    issues = detail.get("issues", [])
                    attrs = detail.get("attributes", {})

                    if not issues and attrs:
                        full_details_fetched += 1

                        # Helper: extract single value from Amazon attribute
                        def attr_val(key, default=None):
                            items = attrs.get(key, [])
                            if items and len(items) > 0:
                                return items[0].get("value", default)
                            return default

                        def attr_val_lang(key, lang="ar", default=None):
                            """Extract value with preferred language"""
                            items = attrs.get(key, [])
                            for item in items:
                                lt = item.get("language_tag", "")
                                if lt.startswith(lang):
                                    return item.get("value", default)
                            # Fallback to first available
                            if items:
                                return items[0].get("value", default)
                            return default

                        # === PRICE ===
                        offer = attrs.get("purchasable_offer", [])
                        if offer and len(offer) > 0:
                            our_price = offer[0].get("our_price", [])
                            if our_price and len(our_price) > 0:
                                schedule = our_price[0].get("schedule", [])
                                if schedule and len(schedule) > 0:
                                    price = schedule[0].get("value_with_tax", 0)

                        # === QUANTITY ===
                        qty_attrs = attrs.get("quantity", [])
                        if qty_attrs and len(qty_attrs) > 0:
                            quantity = qty_attrs[0].get("value", 0)

                        # === DESCRIPTION (Arabic first, then English) ===
                        desc_ar = attr_val_lang("product_description", "ar", "")
                        desc_en = attr_val_lang("product_description", "en", "")
                        description = desc_ar or desc_en or attr_val("product_description", "")
                        description_en = desc_en or desc_ar or description

                        # === BULLET POINTS ===
                        bp_list = attrs.get("bullet_point", [])
                        for bp in bp_list:
                            val = bp.get("value", "")
                            lang = bp.get("language_tag", "en_US")
                            bullet_points.append(val)
                            if lang.startswith("ar"):
                                bullet_points_ar.append(val)
                            else:
                                bullet_points_en.append(val)

                        # === BRAND & NAME ===
                        brand = attr_val_lang("brand", "ar") or attr_val_lang("brand", "en") or attr_val("brand", "Generic")
                        item_name = attr_val_lang("item_name", "ar") or attr_val_lang("item_name", "en") or attr_val("item_name", sku)

                        # === MANUFACTURER & MODEL ===
                        manufacturer = attr_val("manufacturer", "")
                        model_number = attr_val("model_number", "")

                        # === ORIGIN & MATERIAL ===
                        country_of_origin = attr_val("country_of_origin", "")
                        material = attr_val_lang("material", "ar") or attr_val_lang("material", "en") or attr_val("material", "")

                        # === EAN/UPC ===
                        ext_id = attrs.get("externally_assigned_product_identifier", [])
                        if ext_id and len(ext_id) > 0:
                            id_type = ext_id[0].get("type", "")
                            id_val = ext_id[0].get("value", "")
                            if id_type == "ean":
                                ean = id_val
                            elif id_type == "upc":
                                upc = id_val
                        
                        # === GTIN Exemption ===
                        gtin_exempt = attrs.get("supplier_declared_has_product_identifier_exemption", [])
                        if gtin_exempt and len(gtin_exempt) > 0:
                            has_product_identifier = gtin_exempt[0].get("value", False)

                        # === ALL IMAGES (main + 5 other) ===
                        # Amazon returns media_location: "https://..." NOT value: "image_id"
                        # Debug: check if image keys exist
                        img_keys = [k for k in attrs.keys() if 'image' in k.lower() or 'locator' in k.lower()]
                        logger.info(f"  Image-related keys in attrs: {img_keys}")

                        def get_image_url(key):
                            items = attrs.get(key, [])
                            if items and len(items) > 0:
                                url = items[0].get("media_location", "")
                                if url:
                                    return url
                                # Fallback: try value field
                                val = items[0].get("value", "")
                                if val:
                                    img_id = val.replace(".jpg", "").replace(".png", "")
                                    return f"https://m.media-amazon.com/images/I/{img_id}.jpg"
                            return ""

                        main_img = get_image_url("main_product_image_locator")
                        if main_img:
                            images_list.append(main_img)
                            logger.info(f"  Main image: {main_img}")
                        else:
                            logger.info(f"  No main image found. Raw: {attrs.get('main_product_image_locator', 'MISSING')}")

                        # Other images: other_product_image_locator_1 through _5
                        for i in range(1, 6):
                            img_url = get_image_url(f"other_product_image_locator_{i}")
                            if img_url:
                                images_list.append(img_url)
                                logger.info(f"  Image {i}: {img_url}")

                        # === ADDITIONAL FIELDS ===
                        product_type = attr_val("product_type", product_type)
                        condition = attr_val("condition_type", condition)
                        unit_count = attr_val("unit_count", "")
                        number_of_items = attr_val("number_of_items", "")
                        style = attr_val_lang("style", "ar") or attr_val_lang("style", "en") or attr_val("style", "")
                        finish_type = attr_val_lang("finish_type", "ar") or attr_val_lang("finish_type", "en") or attr_val("finish_type", "")
                        theme = attr_val_lang("theme", "ar") or attr_val_lang("theme", "en") or attr_val("theme", "")
                        room_type = attr_val_lang("room_type", "ar") or attr_val_lang("room_type", "en") or attr_val("room_type", "")

                        # Weight & dimensions
                        item_weight = attr_val("item_weight", "")
                        item_package_weight = attr_val("item_package_weight", "")

                        # Store extra metadata in attributes JSON
                        extra_attrs = {
                            "asin": asin,
                            "source": "sp-api-import",
                            "import_date": datetime.utcnow().isoformat(),
                            "amazon_status": status_list,
                            "color": attr_val_lang("color", "ar") or attr_val("color", ""),
                            "pattern": attr_val_lang("pattern", "ar") or attr_val("pattern", ""),
                            "style": style,
                            "finish_type": finish_type,
                            "theme": theme,
                            "room_type": room_type,
                            "material": material,
                            "unit_count": unit_count,
                            "number_of_items": number_of_items,
                            "item_weight": item_weight,
                            "item_package_weight": item_package_weight,
                        }
                        logger.info(f"  Full details fetched: SKU={sku}, price={price}, qty={quantity}, images={len(images_list)}, attrs={len(extra_attrs)}")
                        logger.info(f"  Images: {images_list}")
                    else:
                        logger.warning(f"  Could not fetch full details for SKU={sku}: {issues}")
                except Exception as e:
                    logger.warning(f"  Error fetching full details for SKU={sku}: {e}")

            # Check if product exists
            existing = db.query(Product).filter(Product.sku == sku).first()

            if existing:
                # Update existing product
                existing.name = item_name or existing.name
                existing.name_en = item_name or existing.name_en
                existing.name_ar = item_name or existing.name_ar
                existing.brand = brand or existing.brand
                existing.product_type = product_type or existing.product_type
                existing.status = "published" if "DISCOVERABLE" in status_list else existing.status
                existing.updated_at = datetime.utcnow()

                if full_sync:
                    # SMART SYNC: Only update price if local price is 0 or None (not set)
                    # This preserves locally-edited prices
                    local_price = float(existing.price) if existing.price else 0
                    if price > 0 and local_price == 0:
                        existing.price = price

                    if quantity >= 0:
                        existing.quantity = quantity
                    if description:
                        existing.description = description
                        existing.description_en = description_en
                    if bullet_points:
                        existing.bullet_points = json.dumps(bullet_points)
                        existing.bullet_points_en = json.dumps(bullet_points_en)
                        existing.bullet_points_ar = json.dumps(bullet_points_ar)
                    if manufacturer:
                        existing.manufacturer = manufacturer
                    if model_number:
                        existing.model_number = model_number
                    if country_of_origin:
                        existing.country_of_origin = country_of_origin
                    if material:
                        existing.material = material
                    if ean:
                        existing.ean = ean
                    if upc:
                        existing.upc = upc
                    if 'has_product_identifier' in dir():
                        existing.has_product_identifier = has_product_identifier
                    if images_list:
                        existing.images = json.dumps(images_list)
                    elif main_image and (not existing.images or existing.images == "[]"):
                        existing.images = json.dumps([main_image])
                    # Update attributes with extra metadata
                    if 'extra_attrs' in dir():
                        existing.attributes = json.dumps(extra_attrs)
                elif main_image and (not existing.images or existing.images == "[]"):
                    existing.images = json.dumps([main_image])

                updated += 1
            else:
                # Create new product
                new_product = Product(
                    id=str(uuid.uuid4()),
                    seller_id=seller.id,
                    sku=sku,
                    name=item_name,
                    name_en=item_name,
                    name_ar=item_name,
                    brand=brand or "Generic",
                    category=product_type,
                    product_type=product_type,
                    condition="New" if "new" in condition.lower() else condition,
                    price=price if full_sync else 0,
                    quantity=quantity if full_sync else 0,
                    description=description if full_sync else "",
                    description_en=description_en if full_sync else "",
                    bullet_points=json.dumps(bullet_points) if full_sync else "[]",
                    bullet_points_ar=json.dumps(bullet_points_ar) if full_sync else "[]",
                    bullet_points_en=json.dumps(bullet_points_en) if full_sync else "[]",
                    manufacturer=manufacturer if full_sync else "",
                    model_number=model_number if full_sync else "",
                    country_of_origin=country_of_origin if full_sync else "",
                    ean=ean if full_sync else "",
                    upc=upc if full_sync else "",
                    has_product_identifier=has_product_identifier if full_sync and 'has_product_identifier' in dir() else False,
                    material=material if full_sync else "",
                    status="published" if "DISCOVERABLE" in status_list else "draft",
                    attributes=json.dumps(extra_attrs if full_sync and extra_attrs else {
                        "asin": asin,
                        "source": "sp-api-import",
                        "import_date": datetime.utcnow().isoformat(),
                        "amazon_status": status_list,
                    }),
                    images=json.dumps(images_list if full_sync and images_list else ([main_image] if main_image else [])),
                )
                db.add(new_product)
                created += 1

        except Exception as e:
            logger.error(f"Error importing SKU {item.get('sku', 'unknown')}: {e}")
            errors += 1
            continue

    db.commit()

    sync_type = "FULL" if full_sync else "BASIC"
    logger.info(
        f"Import complete ({sync_type}): {created} created, {updated} updated, "
        f"{errors} errors, {len(all_items)} total from Amazon, {full_details_fetched} full details fetched"
    )

    return {
        "success": True,
        "sync_type": sync_type,
        "total_from_amazon": len(all_items),
        "full_details_fetched": full_details_fetched,
        "created": created,
        "updated": updated,
        "errors": errors,
        "message": f"تم استيراد {created} منتج جديد، وتحديث {updated} منتج ({sync_type})",
    }
