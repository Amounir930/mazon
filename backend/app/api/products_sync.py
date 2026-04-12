"""
Product Sync API
Pulls products from Amazon SP-API and stores them in local database
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
from typing import Optional
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.models.product import Product
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.session import Session as AuthSession
from app.api.activity_log import create_activity_log

router = APIRouter()


# ============================================================
# Cookie-based Sync Endpoints (NEW - Cookie Scraping)
# ============================================================

@router.post("/products")
async def sync_products_from_amazon(
    db: Session = Depends(get_db),
):
    """
    مزامنة المنتجات من Amazon Seller Central → Local Database.
    يستخدم الـ Cookies المحفوظة لتحميل تقرير المنتجات.

    Request: POST /api/v1/sync/products
    Response: {
        "success": true,
        "synced": 50,
        "updated": 10,
        "total": 60,
        "message": "تم استيراد 60 منتج"
    }
    """
    try:
        from app.services.sync_engine import AmazonProductSyncEngine, get_active_session

        # Get active session cookies
        cookies, country = get_active_session()
        if not cookies:
            raise HTTPException(
                status_code=401,
                detail="لا يوجد جلسة نشطة - يرجى تسجيل الدخول أولاً"
            )

        # Initialize sync engine
        sync_engine = AmazonProductSyncEngine(country_code=country)
        sync_engine.setup_cookies(cookies)

        # Execute sync
        result = sync_engine.sync_products()

        logger.info(f"Product sync result: {result}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Product sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"فشلت المزامنة: {str(e)}")


@router.post("/export-to-amazon")
async def export_products_to_amazon(
    db: Session = Depends(get_db),
    only_new: bool = Query(True, description="تصدير المنتجات الجديدة فقط (بدون listings)"),
):
    """
    تصدير المنتجات من Local Database → Amazon Listing.
    
    - only_new=True (default): يرفع بس المنتجات اللي مفيهاش listing لسه
    - only_new=False: يرفع كل المنتجات (إعادة رفع)

    Request: POST /api/v1/sync/export-to-amazon?only_new=true
    Response: {
        "success": true,
        "submitted": 10,
        "failed": 0,
        "total": 10,
        "message": "تم رفع 10 منتج إلى Amazon"
    }
    """
    try:
        # Get products based on filter
        if only_new:
            # فقط المنتجات اللي مفيهاش listing لسه
            from sqlalchemy import not_, exists
            from app.models.listing import Listing
            
            products = db.query(Product).filter(
                not_(exists().where(Listing.product_id == Product.id))
            ).all()
            
            filter_desc = "الجديدة (بدون listings)"
        else:
            # كل المنتجات
            products = db.query(Product).all()
            filter_desc = "كل المنتجات"

        if not products:
            return {
                "success": True,
                "message": "لا توجد منتجات في قاعدة البيانات - أضف منتجات أولاً",
                "submitted": 0,
                "failed": 0,
                "total": 0,
            }

        # Submit each product as a listing
        from app.tasks.task_manager import task_manager
        from app.tasks.listing_tasks import submit_listing_task

        submitted = 0
        failed = 0
        results = []

        for product in products:
            try:
                task_id = await task_manager.submit(submit_listing_task(product.id))
                results.append({
                    "product_id": product.id,
                    "sku": product.sku,
                    "task_id": task_id,
                    "status": "queued"
                })
                submitted += 1
            except Exception as e:
                failed += 1
                logger.error(f"Failed to submit listing for {product.sku}: {e}")

        logger.info(f"Export to Amazon ({filter_desc}): {submitted} submitted, {failed} failed, {len(products)} total")

        return {
            "success": True,
            "submitted": submitted,
            "failed": failed,
            "total": len(products),
            "results": results[:10],  # Return first 10 for preview
            "message": f"تم رفع {submitted} منتج إلى Amazon ({failed} فشل)" if failed == 0 else f"تم رفع {submitted} منتج، فشل {failed}",
            "filter": filter_desc,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Export to Amazon failed: {e}")
        raise HTTPException(status_code=500, detail=f"فشل التصدير: {str(e)}")


@router.post("/products-old")
async def sync_products_cookie(
    email: str = Query(..., description="Email for cookie-based sync"),
    db: Session = Depends(get_db),
):
    """
    Sync products to Amazon using Direct API (ALister approach) - OLD.
    """
    try:
        # Get all products from DB
        products = db.query(Product).all()
        
        if not products:
            return {
                "success": True,
                "message": "No products in database - nothing to sync",
                "synced": 0,
                "results": [],
            }
        
        # Sync via Direct API
        from app.services.amazon_direct_api import AmazonDirectAPI
        
        api = AmazonDirectAPI(email)
        results = []
        synced = 0
        
        for product in products:
            result = await api.create_listing(product.id)
            results.append({
                "sku": product.sku,
                "success": result.get("success", False),
                "message": result.get("message", result.get("error", "")),
            })
            if result.get("success"):
                synced += 1
        
        logger.info(f"Direct API sync: {synced}/{len(products)} listings created")
        
        return {
            "success": True,
            "synced": synced,
            "total": len(products),
            "results": results,
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Direct API sync failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "synced": 0,
            "total": 0,
            "results": [],
        }


@router.post("/products/{product_id}")
async def sync_single_product(product_id: str, db: Session = Depends(get_db)):
    """
    Sync a single product to Amazon using Direct API.
    
    Request: POST /sync/products/{product_id}
    Response: {
        "success": true,
        "message": "Listing created"
    }
    """
    try:
        # Get product from DB
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {
                "success": False,
                "error": f"Product {product_id} not found",
            }
        
        # Sync via Direct API
        from app.services.amazon_direct_api import AmazonDirectAPI
        
        api = AmazonDirectAPI("amazon_eg")
        result = await api.create_listing(product_id)
        
        if result.get("success"):
            logger.info(f"Listing created for product {product.sku}")
            return {
                "success": True,
                "message": f"Listing created for {product.sku}",
                "asin": result.get("asin"),
                "listing_id": result.get("listing_id"),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
            }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Single product sync failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/orders")
async def sync_orders_cookie(
    email: str = Query(..., description="Email for cookie-based sync"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Sync orders using cookie-based authentication.
    Uses active browser session cookies to fetch orders from Amazon Seller Central.
    
    Request: POST /api/v1/sync/orders?email=user@email.com&days=30
    Response: {
        "success": true,
        "synced": 50,
        "total": 50,
        "orders": [...]
    }
    """
    try:
        from app.services.cookie_scraper import CookieScraper

        scraper = CookieScraper()
        
        # Sync orders via cookies
        result = await scraper.sync_orders(email, days=days)
        scraper.close()

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Failed to sync orders"),
                "orders": [],
                "synced": 0,
                "total": 0,
            }

        # Store synced orders in local database
        orders = result.get("orders", [])
        synced_count = 0

        for item in orders:
            order_id = item.get("amazon_order_id", "")
            if not order_id:
                continue

            # Check if order already exists
            existing = db.query(Order).filter(Order.amazon_order_id == order_id).first()
            if existing:
                # Update existing order
                existing.order_status = item.get("status", existing.order_status)
                existing.total = item.get("total", existing.total)
                existing.buyer_name = item.get("buyer_name", existing.buyer_name)
                existing.last_update_date = datetime.now(timezone.utc)
            else:
                # Create new order
                order = Order(
                    seller_id=None,  # Will be linked later
                    amazon_order_id=order_id,
                    order_status=item.get("status", "Unknown"),
                    total=item.get("total", 0),
                    buyer_name=item.get("buyer_name", ""),
                    purchase_date=datetime.now(timezone.utc),  # Will be parsed from actual date
                    items=json.dumps(item.get("items", [])),
                    source="cookie",
                )
                db.add(order)
                synced_count += 1

        db.commit()

        logger.info(f"Cookie sync: {synced_count} orders synced for {email}")

        return {
            "success": True,
            "synced": synced_count,
            "total": result.get("total", 0),
            "orders": orders[:10],  # Return first 10 for preview
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Cookie-based orders sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/inventory")
async def sync_inventory_cookie(
    email: str = Query(..., description="Email for cookie-based sync"),
    db: Session = Depends(get_db),
):
    """
    Sync inventory using cookie-based authentication.
    Uses active browser session cookies to fetch inventory from Amazon Seller Central.
    
    Request: POST /api/v1/sync/inventory?email=user@email.com
    Response: {
        "success": true,
        "synced": 100,
        "total": 100,
        "inventory": [...]
    }
    """
    try:
        from app.services.cookie_scraper import CookieScraper

        scraper = CookieScraper()
        
        # Sync inventory via cookies
        result = await scraper.sync_inventory(email)
        scraper.close()

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Failed to sync inventory"),
                "inventory": [],
                "synced": 0,
                "total": 0,
            }

        # Store synced inventory in local database
        inventory_items = result.get("inventory", [])
        synced_count = 0

        for item in inventory_items:
            item_sku = item.get("sku", "")
            if not item_sku:
                continue

            # Check if inventory record already exists
            existing = db.query(Inventory).filter(Inventory.sku == item_sku).first()
            if existing:
                # Update existing inventory
                existing.available = item.get("available", existing.available)
                existing.reserved = item.get("reserved", existing.reserved)
                existing.inbound = item.get("inbound", existing.inbound)
                existing.fba = item.get("fba", existing.fba)
                existing.fbm = item.get("fbm", existing.fbm)
                existing.synced_at = datetime.now(timezone.utc)
            else:
                # Create new inventory record
                inv = Inventory(
                    seller_id=None,  # Will be linked later
                    sku=item_sku,
                    asin=item.get("asin", ""),
                    product_name=item.get("name", ""),
                    available=item.get("available", 0),
                    reserved=item.get("reserved", 0),
                    inbound=item.get("inbound", 0),
                    fba=item.get("fba", False),
                    fbm=item.get("fbm", True),
                    fulfillment_channel=item.get("fulfillment", "MFN"),
                    source="cookie",
                )
                db.add(inv)
                synced_count += 1

        db.commit()

        logger.info(f"Cookie sync: {synced_count} inventory items synced for {email}")

        return {
            "success": True,
            "synced": synced_count,
            "total": result.get("total", 0),
            "inventory": inventory_items[:10],  # Return first 10 for preview
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Cookie-based inventory sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============================================================
# Legacy Cookie-based Sync Endpoints (GET - keep for backward compatibility)
# ============================================================

@router.get("/products/legacy")
async def sync_products_cookie_legacy(
    email: Optional[str] = Query(None, description="Email for cookie-based sync"),
    db: Session = Depends(get_db),
):
    """
    Sync products using cookie-based authentication.
    Uses active browser session cookies to fetch products from Amazon.
    """
    try:
        from app.services.cookie_auth import CookieAuth
        
        # Get active session
        active_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
            AuthSession.is_valid == True,
        ).first()
        
        if not active_session or not active_session.cookies_json:
            raise HTTPException(status_code=401, detail="No active session - please login first")
        
        # Decrypt cookies
        from app.services.session_store import decrypt_data
        cookies = json.loads(decrypt_data(active_session.cookies_json))
        country_code = active_session.country_code or "eg"
        
        # Sync products via cookies
        result = await CookieAuth.sync_products(cookies, country_code)
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Failed to sync products"),
                "products": [],
            }
        
        # Store synced products in local database
        products = result.get("products", [])
        synced_count = 0
        
        for item in products:
            item_sku = item.get("sku", "")
            if not item_sku:
                continue
            
            # Check if product already exists
            existing = db.query(Product).filter(Product.sku == item_sku).first()
            if existing:
                # Update existing product
                existing.name = item.get("title", existing.name)
                existing.price = item.get("price", existing.price)
                existing.quantity = item.get("quantity", existing.quantity)
                existing.status = "published"
                existing.updated_at = datetime.utcnow()
            else:
                # Create new product
                product = Product(
                    seller_id=None,  # Will be linked later
                    sku=item_sku,
                    name=item.get("title", item_sku),
                    price=item.get("price", 0),
                    quantity=item.get("quantity", 0),
                    category=item.get("category", ""),
                    status="published",
                )
                db.add(product)
                synced_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "synced_count": synced_count,
            "total": len(products),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Cookie-based sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/orders/legacy")
async def sync_orders_cookie_legacy(
    email: Optional[str] = Query(None, description="Email for cookie-based sync"),
    db: Session = Depends(get_db),
):
    """
    Sync orders using cookie-based authentication.
    Uses active browser session cookies to fetch orders from Amazon.
    """
    try:
        from app.services.cookie_auth import CookieAuth
        
        # Get active session
        active_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
            AuthSession.is_valid == True,
        ).first()
        
        if not active_session or not active_session.cookies_json:
            raise HTTPException(status_code=401, detail="No active session - please login first")
        
        # Decrypt cookies
        from app.services.session_store import decrypt_data
        cookies = json.loads(decrypt_data(active_session.cookies_json))
        country_code = active_session.country_code or "eg"
        
        # Sync orders via cookies
        result = await CookieAuth.sync_orders(cookies, country_code)
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Failed to sync orders"),
                "orders": [],
            }
        
        return {
            "success": True,
            "orders": result.get("orders", []),
            "total": result.get("total", 0),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Cookie-based orders sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============================================================
# Legacy SP-API Sync (keep for backward compatibility)
# ============================================================


@router.post("/sync")
async def sync_products_from_amazon(
    sku: Optional[str] = Query(None, description="Sync specific SKU only"),
    db: Session = Depends(get_db),
):
    """
    Pull products from Amazon and store them locally.

    - If `sku` is provided: sync only that SKU (partial sync)
    - If `sku` is not provided: sync all products from Amazon

    In MOCK mode: returns sample products
    In REAL mode: fetches from Amazon SP-API
    """
    seller = db.query(Seller).first()
    if not seller or not seller.is_connected:
        raise HTTPException(status_code=400, detail="Amazon not connected. Please connect and verify first.")

    try:
        from app.services.amazon_api import AmazonAPIClient

        client = AmazonAPIClient(
            seller_id=seller.amazon_seller_id,
            marketplace_id=seller.marketplace_id,
            refresh_token=seller.lwa_refresh_token,
        )

        # Fetch products from Amazon
        if sku:
            # Partial sync: get specific SKU
            try:
                listing = await client.get_listings()
                amazon_listings = [l for l in listing if l.get("sku") == sku] if listing else []
            except Exception:
                amazon_listings = []
        else:
            amazon_listings = await client.get_listings()

        if not amazon_listings:
            return {"message": "No products found on Amazon", "synced_count": 0}

        synced_count = 0
        updated_count = 0
        skipped_count = 0

        for item in amazon_listings:
            item_sku = item.get("sku", "")
            if not item_sku:
                continue

            # Extract Amazon data with more fields
            item_data = {
                "title": item.get("title", item_sku),
                "price": item.get("price", 0),
                "quantity": item.get("quantity", 0),
                "category": item.get("category", ""),
                "brand": item.get("brand", ""),
                "description": item.get("description", ""),
                "bullet_points": item.get("bullet_points", []),
                "images": item.get("images", []),
                # Amazon-specific fields
                "condition": item.get("condition", "New"),
                "fulfillment_channel": item.get("fulfillment_channel", "MFN"),
                "handling_time": item.get("handling_time", 0),
                "product_type": item.get("product_type", ""),
                "asin": item.get("asin", ""),
            }

            # Check if product already exists
            existing = db.query(Product).filter(Product.sku == item_sku).first()
            if existing:
                # Update existing product with all fields
                existing.name = item_data["title"]
                existing.price = item_data["price"]
                existing.quantity = item_data["quantity"]
                existing.category = item_data["category"]
                existing.brand = item_data["brand"]
                existing.description = item_data["description"]
                existing.status = "published"
                existing.updated_at = datetime.utcnow()

                # Update Amazon-specific fields if available
                if item_data["condition"] != "New":
                    existing.condition = item_data["condition"]
                if item_data["fulfillment_channel"]:
                    existing.fulfillment_channel = item_data["fulfillment_channel"]
                if item_data["handling_time"] is not None:
                    existing.handling_time = item_data["handling_time"]
                if item_data["product_type"]:
                    existing.product_type = item_data["product_type"]

                # Log activity
                create_activity_log(db, existing.id, "synced", "success", {
                    "source": "amazon",
                    "sku": item_sku,
                    "fields_updated": ["name", "price", "quantity", "condition", "fulfillment"],
                })

                updated_count += 1
                logger.debug(f"Updated existing product: {item_sku}")
            else:
                # Create new product with all fields
                bullet_points = item_data["bullet_points"]
                images = item_data["images"]

                product = Product(
                    seller_id=seller.id,
                    sku=item_sku,
                    name=item_data["title"],
                    price=item_data["price"],
                    quantity=item_data["quantity"],
                    category=item_data["category"],
                    brand=item_data["brand"],
                    description=item_data["description"],
                    bullet_points=json.dumps(bullet_points),
                    images=json.dumps(images),
                    status="published",
                    # Amazon-specific fields
                    condition=item_data["condition"],
                    fulfillment_channel=item_data["fulfillment_channel"],
                    handling_time=item_data["handling_time"],
                    product_type=item_data["product_type"],
                )
                db.add(product)
                db.flush()  # Get product ID

                # Log activity
                create_activity_log(db, product.id, "synced", "success", {
                    "source": "amazon",
                    "sku": item_sku,
                    "action": "created_from_sync",
                })

                synced_count += 1
                logger.info(f"New product synced: {item_sku}")

        db.commit()

        # Update last sync time
        seller.last_sync_at = datetime.utcnow()
        db.commit()

        total = synced_count + updated_count
        sync_type = f"partial (SKU: {sku})" if sku else "full"
        logger.info(f"Sync {sync_type} complete: {synced_count} new, {updated_count} updated, {total} total")

        return {
            "message": f"Synced {total} products from Amazon ({synced_count} new, {updated_count} updated)",
            "sync_type": sync_type,
            "synced_count": synced_count,
            "updated_count": updated_count,
            "total": total,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
