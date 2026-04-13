"""
Listing Tasks (Asyncio-based)
Handles background listing submissions to Amazon

Uses Direct API (ABIS AJAX) — Cookie-based, ALister approach.
NO SP-API credentials needed — uses cookies from pywebview login.
"""
import asyncio
import json
from datetime import datetime
from app.database import SessionLocal
from app.database import Session as DBSession
from app.models.seller import Seller
from app.models.listing import Listing
from app.models.product import Product
from app.models.activity_log import ActivityLog
from app.services.validation_service import ValidationService
from loguru import logger
import json

# Retry configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # seconds: 2, 4, 8


def _parse_json_field(value: str, default=None):
    """Safely parse a JSON string field"""
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


async def submit_listing_task(product_id: str) -> dict:
    """
    Submit a product listing to Amazon.

    Flow:
    1. Get seller credentials
    2. Get product data
    3. Create listing record (status=processing)
    4. Submit to Amazon via SP-API (or mock)
    5. Update listing with result
    """
    db = SessionLocal()
    try:
        # Step 1: Verify seller
        seller = db.query(Seller).first()
        if not seller or not seller.is_connected:
            raise ValueError("Amazon not connected. Please connect and verify first.")

        # Step 2: Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Step 3: Create listing record
        listing = Listing(
            product_id=product.id,
            seller_id=product.seller_id,
            status="processing",
            stage="validating",
            submitted_at=datetime.utcnow(),
        )
        db.add(listing)
        db.commit()
        logger.info(f"Listing created for product {product.sku} (ID: {listing.id})")

        # Log activity
        _log_activity(db, product.id, "submitted", "success", listing.id, {"listing_id": listing.id})

        # Step 4: Submit to Amazon — transition to processing
        listing.stage = "processing"
        db.commit()

        # Validate product before submission
        product_data = {
            "sku": product.sku,
            "name": product.name,
            "price": float(product.price) if product.price else 0,
            "images": _parse_json_field(product.images, []),
            "brand": product.brand,
            "product_type": product.product_type,
            "condition": product.condition,
            "fulfillment_channel": product.fulfillment_channel,
            "upc": product.upc,
            "ean": product.ean,
        }
        validation = ValidationService.validate_product_dict(product_data)
        if not validation.valid:
            listing.status = "failed"
            listing.stage = "failed"
            listing.error_message = f"Validation failed: {validation.to_dict()['errors']}"
            listing.completed_at = datetime.utcnow()
            db.commit()
            _log_activity(db, product.id, "failed", "failed", listing.id, {"validation_errors": validation.to_dict()['errors']})
            logger.error(f"❌ Validation failed for {product.sku}: {validation.to_dict()['errors']}")
            return {"status": "failed", "error": validation.to_dict()['errors']}

        # Transition to submitted stage before API call
        listing.stage = "submitted"
        db.commit()

        # Step 4: Submit to Amazon via ABIS Client (Phase 4 — correct payload format + CSRF)
        # This uses the new ABISClient with:
        # - application/x-www-form-urlencoded (NOT application/json)
        # - CSRF Token extraction from page
        # - Proper cookie handling
        from app.services.abis_client import ABISClient
        from app.models.session import Session

        # Get session with cookies
        db_sessions = SessionLocal()
        auth_session = db_sessions.query(Session).filter(
            Session.auth_method == "browser",
            Session.cookies_json.isnot(None)
        ).order_by(Session.created_at.desc()).first()

        if not auth_session:
            db_sessions.close()
            logger.error("❌ No browser session with cookies found — user must login via Seller Central first")
            listing.status = "failed"
            listing.stage = "failed"
            listing.error_message = "No active session with cookies — Please login to Amazon Seller Central first"
            listing.completed_at = datetime.utcnow()
            db.commit()
            return {"status": "failed", "error": "No active session with cookies"}

        # Decrypt cookies
        from app.services.session_store import decrypt_data
        import json
        cookies = json.loads(decrypt_data(auth_session.cookies_json))
        country_code = auth_session.country_code or "eg"
        db_sessions.close()

        logger.info(f"✅ Using session: {len(cookies)} cookies, country={country_code}")

        # Initialize ABIS client
        client = ABISClient(cookies=cookies, country_code=country_code)

        # Set CSRF token from auth session (if available)
        csrf_token = auth_session.csrf_token
        if csrf_token:
            client.csrf_token = csrf_token
            logger.info(f"✅ CSRF token loaded from session: {csrf_token[:20]}...")
        else:
            logger.warning("⚠️ No CSRF token in session — will fetch fresh token before POST")

        result = None
        for attempt in range(MAX_RETRIES):
            try:
                listing.retry_count = attempt
                listing.stage = "processing"
                db.commit()

                # Get product data for ABIS payload
                product_data = {
                    "sku": product.sku,
                    "name": product.name,
                    "description": product.description or "",
                    "price": float(product.price) if product.price else 0,
                    "quantity": product.quantity or 0,
                    "currency": product.currency or "EGP",
                    "product_type": product.product_type or "",
                    "condition": product.condition or "New",
                    "fulfillment_channel": product.fulfillment_channel or "MFN",
                    "brand": product.brand or "Generic",
                    "manufacturer": product.manufacturer or "",
                    "model_number": product.model_number or "",
                    "country_of_origin": product.country_of_origin or "",
                    "upc": product.upc or "",
                    "ean": product.ean or "",
                    "bullet_points": _parse_json_field(product.bullet_points),
                    "material": product.material or "",
                }

                # ABIS Client is synchronous (not async)
                result = client.create_listing(product_data)

                # Success — break out of retry loop
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    # Final attempt failed
                    logger.error(f"❌ All {MAX_RETRIES} retries exhausted for {product.sku}: {str(e)}")
                    result = {"success": False, "error": str(e)}
                else:
                    wait_time = BACKOFF_FACTOR ** (attempt + 1)
                    listing.status = "retrying"
                    listing.stage = "processing"
                    listing.retry_count = attempt + 1
                    listing.error_message = f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s..."
                    db.commit()
                    _log_activity(db, product.id, "failed", "failed", listing.id, {
                        "attempt": attempt + 1,
                        "retry_in": wait_time,
                        "error": str(e),
                    })
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed for {product.sku}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

        # Step 5: Update listing with result
        if result and result.get("success"):
            listing.status = "success"
            listing.stage = "success"
            listing.amazon_asin = result.get("listing_id", "") or result.get("asin", "")
            listing.amazon_url = f"https://www.amazon.eg/dp/{listing.amazon_asin}" if listing.amazon_asin else ""
            listing.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Listing success: {product.sku} → ASIN {listing.amazon_asin}")

            # Log activity
            _log_activity(db, product.id, "published", "success", listing.id, {"asin": listing.amazon_asin})
        else:
            error_msg = result.get("error", result.get("message", "Unknown error"))
            is_session_expired = result.get("session_expired", False)
            listing.status = "failed"
            listing.stage = "failed"
            listing.error_message = str(error_msg)
            listing.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"❌ Listing failed: {product.sku} — {error_msg}")

            # Log activity with session expired flag
            _log_activity(db, product.id, "failed", "failed", listing.id, {
                "error": error_msg,
                "session_expired": is_session_expired
            })

        return {"status": listing.status, "asin": listing.amazon_asin}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Submit listing exception: {str(e)}")

        # Try to update the listing with error
        try:
            listing = db.query(Listing).filter(
                Listing.product_id == product_id
            ).order_by(Listing.created_at.desc()).first()
            if listing:
                listing.status = "failed"
                listing.stage = "failed"
                listing.error_message = str(e)
                listing.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass

        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


async def retry_listing_task(listing_id: str) -> dict:
    """
    Retry a failed listing submission.

    Flow:
    1. Get the listing
    2. Reset its status
    3. Re-submit via submit_listing_task
    """
    db = SessionLocal()
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        if listing.status not in ("failed",):
            return {"status": listing.status, "message": "Listing is not in failed state"}

        # Check max retries
        if listing.retry_count >= MAX_RETRIES:
            return {"status": "failed", "message": f"Max retries ({MAX_RETRIES}) exceeded"}

        # Reset status
        listing.status = "queued"
        listing.stage = "queued"
        listing.error_message = None
        listing.retry_count = 0
        listing.submitted_at = None
        listing.completed_at = None
        db.commit()

        logger.info(f"Retrying listing {listing_id} for product {listing.product_id}")

        # Re-submit
        result = await submit_listing_task(listing.product_id)
        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Retry failed for listing {listing_id}: {str(e)}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def _log_activity(db: DBSession, product_id: str, action: str, status: str, listing_id: str | None = None, details: dict | None = None):
    """Helper to log activity"""
    log = ActivityLog(
        product_id=product_id,
        listing_id=listing_id,
        action=action,
        status=status,
        details=json.dumps(details) if details else None,
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()
