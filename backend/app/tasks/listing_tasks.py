"""
Listing Tasks (Asyncio-based)
Handles background listing submissions to Amazon

Uses SP-API (Phase 1) — Official Amazon Selling Partner API.
REPLACES: Playwright/ABIS AJAX approach (deprecated).
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
from app.services.sp_api_client import SPAPIClient
from app.tasks.polling_tasks import poll_listing_status
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

        # DISABLED: Skip validation — submit to Amazon even with incomplete data
        # Validation is now optional. Users can submit products with missing fields.
        # product_data = {
        #     "sku": product.sku,
        #     ...
        # }
        # validation = ValidationService.validate_product_dict(product_data)
        # if not validation.valid:
        #     listing.status = "failed"
        #     ...
        #     return {"status": "failed", "error": validation.to_dict()['errors']}

        # Log that validation was skipped
        logger.info(f"⚠️ Skipping validation for {product.sku} — submitting with available data")

        # Transition to submitted stage before API call
        listing.stage = "submitted"
        db.commit()

        # Step 5: Submit to Amazon via SP-API (Phase 1)
        from app.models.session import Session
        from app.services.session_store import decrypt_data
        import os

        # Get active session (for marketplace/country info)
        db_sessions = SessionLocal()
        auth_session = db_sessions.query(Session).filter(
            Session.auth_method == "browser",
            Session.is_active == True,
            Session.is_valid == True,
        ).order_by(Session.created_at.desc()).first()

        # Get credentials — from session OR fallback to ENV
        if auth_session and auth_session.credentials_json:
            credentials = json.loads(decrypt_data(auth_session.credentials_json))
            seller_id = credentials.get("seller_id", "A1DSHARRBRWYZW")
            marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
            country_code = auth_session.country_code or "eg"
            logger.info(f"✅ Using session credentials: seller={seller_id}")
        else:
            # Fallback to environment variables (Phase 1 setup)
            seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")
            marketplace_id = os.getenv("SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU")
            country_code = os.getenv("SP_API_COUNTRY", "eg")
            if auth_session:
                logger.warning(f"⚠️ No credentials in session — using ENV fallback (seller={seller_id})")
            else:
                logger.warning(f"⚠️ No active session — using ENV fallback (seller={seller_id})")
        
        db_sessions.close()

        logger.info(f"✅ Submitting via SP-API: seller={seller_id}, marketplace={marketplace_id}")

        # Get full product data
        product_data = {
            "sku": product.sku,
            "name": product.name,
            "description": product.description or "",
            "price": float(product.price) if product.price else 0,
            "quantity": product.quantity or 0,
            "currency": product.currency or "EGP",
            "product_type": product.product_type or "HOME_ORGANIZERS_AND_STORAGE",
            "condition": product.condition or "New",
            "fulfillment_channel": product.fulfillment_channel or "MFN",
            "brand": product.brand or "Generic",
            "color": product.attributes.get("color", "متعدد") if isinstance(product.attributes, dict) else "متعدد",
            "manufacturer": product.manufacturer or "",
            "model_number": product.model_number or "",
            "country_of_origin": product.country_of_origin or "CN",
            "upc": product.upc or "",
            "ean": product.ean or "",
            "bullet_points": _parse_json_field(product.bullet_points),
            "browse_node_id": product.browse_node_id or "21863799031",
            "included_components": product.name or "",
            "merchant_suggested_asin": (product.attributes or {}).get("asin", "") if isinstance(product.attributes, dict) else "",
        }

        result = None
        for attempt in range(MAX_RETRIES):
            try:
                listing.retry_count = attempt
                listing.stage = "processing"
                db.commit()

                # SP-API client (no Playwright needed!)
                client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
                result = client.create_listing_from_product(
                    seller_id=seller_id,
                    sku=product.sku,
                    product_data=product_data,
                )

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

        # Step 6: Update listing with result
        listing.sp_api_submission_id = result.get("submissionId", "")
        listing.sp_api_status = result.get("status", "UNKNOWN")

        if result.get("success"):
            listing.status = "processing"  # Not "success" yet — polling will update this
            listing.stage = "accepted"
            listing.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"✅ Listing submitted: {product.sku} → Status: {result.get('status')}")

            # Log activity
            _log_activity(db, product.id, "submitted", "success", listing.id, {
                "submission_id": result.get("submissionId"),
                "status": result.get("status"),
            })

            # Start background polling to check for ASIN assignment
            try:
                asyncio.create_task(
                    poll_listing_status(
                        sku=product.sku,
                        seller_id=seller_id,
                        listing_id=listing.id,
                    )
                )
                logger.info(f"🔄 Polling started for {product.sku}")
            except Exception as e:
                logger.warning(f"Failed to start polling: {e}")
        else:
            errors = result.get("errors", [])
            error_messages = [e.get("message", "Unknown error") for e in errors]
            listing.status = "failed"
            listing.stage = "rejected"
            listing.error_message = "\n".join(error_messages)[:500]
            listing.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"❌ Listing rejected: {product.sku} — {error_messages[0] if error_messages else 'Unknown'}")

            # === AI LEARNING FEEDBACK: Store rejection errors in product's optimized_data ===
            try:
                if product.optimized_data:
                    import json as _json
                    opt_data = _json.loads(product.optimized_data) if isinstance(product.optimized_data, str) else product.optimized_data
                else:
                    opt_data = {}

                if "rejection_history" not in opt_data:
                    opt_data["rejection_history"] = []

                opt_data["rejection_history"].append({
                    "date": datetime.utcnow().isoformat(),
                    "errors": error_messages,
                    "submission_id": result.get("submissionId", ""),
                })

                # Extract missing required fields from error messages
                missing_fields = []
                for msg in error_messages:
                    # Amazon errors like: "'عدد العناصر' مطلوب لكنه مفقود."
                    # Extract field name between quotes
                    import re
                    match = re.search(r"'([^']+)' مطلوب", msg)
                    if match:
                        missing_fields.append(match.group(1))

                if missing_fields:
                    if "learned_fields" not in opt_data:
                        opt_data["learned_fields"] = []
                    for field in missing_fields:
                        if field not in opt_data["learned_fields"]:
                            opt_data["learned_fields"].append(field)

                product.optimized_data = _json.dumps(opt_data, ensure_ascii=False)
                db.commit()
                logger.info(f"🧠 AI Learning: Stored {len(missing_fields)} missing fields for {product.sku}: {missing_fields}")
            except Exception as e:
                logger.warning(f"Failed to store AI learning feedback: {e}")
            # ==================================================================

            # Log activity
            _log_activity(db, product.id, "failed", "failed", listing.id, {
                "errors": error_messages,
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
