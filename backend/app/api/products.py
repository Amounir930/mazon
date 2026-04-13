"""
Product API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import json
from decimal import Decimal

from app.database import get_db
from app.models.product import Product
from app.models.seller import Seller
from app.schemas.product import ProductCreate, ProductUpdate, ProductListResponse, MessageResponse
from app.api.activity_log import create_activity_log
from loguru import logger

router = APIRouter()


def product_to_dict(product: Product) -> dict:
    """Convert Product model to dict (handle JSON strings)"""
    d = {c.name: getattr(product, c.name) for c in product.__table__.columns}
    # Parse JSON strings
    for field in ['bullet_points', 'bullet_points_ar', 'bullet_points_en', 'keywords', 'images', 'dimensions', 'attributes', 'optimized_data', 'unit_count']:
        val = d.get(field)
        if val and isinstance(val, str):
            try:
                d[field] = json.loads(val)
            except Exception:
                d[field] = [] if field not in ('dimensions', 'attributes', 'optimized_data', 'unit_count') else {}
    # Convert Decimal to float for JSON serialization
    for field in ['price', 'compare_price', 'cost', 'weight', 'sale_price']:
        if d.get(field) is not None:
            d[field] = float(d[field])
    # Default currency
    if d.get('currency') is None:
        d['currency'] = 'EGP'
    # FIX: Apply default values for integer fields that are NULL in old DB records
    int_defaults = {
        'quantity': 0,
        'handling_time': 0,
        'number_of_items': 1,
        'package_quantity': 1,
        'retry_count': 0,
    }
    for field, default_val in int_defaults.items():
        if d.get(field) is None:
            d[field] = default_val
    # Convert datetime to string
    for field in ['created_at', 'updated_at']:
        val = d.get(field)
        if val and hasattr(val, 'isoformat'):
            d[field] = val.isoformat()

    # Handle sale dates
    for field in ['sale_start_date', 'sale_end_date']:
        val = d.get(field)
        if val and hasattr(val, 'isoformat'):
            d[field] = val.isoformat()
    return d


@router.get("", response_model=ProductListResponse)
async def list_products(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if seller_id:
        query = query.filter(Product.seller_id == seller_id)
    if status:
        query = query.filter(Product.status == status)
    if category:
        query = query.filter(Product.category == category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.like(search_term)) |
            (Product.name_ar.like(search_term)) |
            (Product.name_en.like(search_term)) |
            (Product.sku.like(search_term))
        )

    total = query.count()
    products = query.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListResponse(
        items=[product_to_dict(p) for p in products],
        total=total,
        page=page,
        pages=(total + page_size - 1) // page_size,
        has_next=page * page_size < total,
        has_prev=page > 1,
    )


@router.post("", status_code=201)
async def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    # Auto-assign seller_id if empty (use first available seller)
    seller_id = data.seller_id or ""
    if not seller_id:
        first_seller = db.query(Seller).first()
        if first_seller:
            seller_id = first_seller.id
        else:
            raise HTTPException(status_code=400, detail="No sellers configured. Please add a seller first.")

    # Check SKU uniqueness for this seller
    existing = db.query(Product).filter(
        Product.seller_id == seller_id,
        Product.sku == data.sku
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="SKU already exists for this seller"
        )

    # Validate against Amazon requirements to determine status
    from app.services.validation_service import ValidationService

    validation = ValidationService.validate_product(
        sku=data.sku,
        name=data.name,
        price=float(data.price),
        images=data.images or [],
        brand=data.brand or "",
        product_type=data.product_type or "",
        condition=data.condition or "New",
        fulfillment_channel=data.fulfillment_channel or "MFN",
        upc=data.upc or "",
        ean=data.ean or "",
        bullet_points=data.bullet_points or [],
    )

    # Determine status: valid = draft (ready), invalid = incomplete
    status = "draft" if validation.valid else "incomplete"

    product = Product(
        seller_id=seller_id,
        sku=data.sku,
        name=data.name,
        name_ar=data.name_ar,
        name_en=data.name_en,
        category=data.category or "",
        brand=data.brand or "",
        price=data.price,
        currency=data.currency or "EGP",
        quantity=data.quantity or 0,
        description=data.description or "",
        description_ar=data.description_ar or "",
        description_en=data.description_en or "",
        bullet_points=json.dumps(data.bullet_points or []),
        bullet_points_ar=json.dumps(data.bullet_points_ar or []),
        bullet_points_en=json.dumps(data.bullet_points_en or []),
        keywords=json.dumps(data.keywords or []),
        images=json.dumps(data.images or []),
        attributes=json.dumps(data.attributes or {}),
        upc=data.upc or "",
        ean=data.ean or "",
        condition=data.condition or "New",
        fulfillment_channel=data.fulfillment_channel or "MFN",
        handling_time=data.handling_time or 0,
        product_type=data.product_type or "",
        manufacturer=data.manufacturer or "",
        model_number=data.model_number or "",
        country_of_origin=data.country_of_origin or "",
        package_quantity=data.package_quantity or 1,
        browse_node_id=data.browse_node_id or "",
        # حقول إضافية من صفحة 2
        material=data.material or "",
        number_of_items=data.number_of_items or 1,
        unit_count=json.dumps(data.unit_count) if data.unit_count else None,
        target_audience=data.target_audience or "",
        # Sale pricing
        compare_price=data.compare_price,
        cost=data.cost,
        sale_price=data.sale_price,
        sale_start_date=data.sale_start_date,
        sale_end_date=data.sale_end_date,
        # المنتج بيتحفظ draft لو كامل، incomplete لو ناقص
        status=status,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Log activity
    create_activity_log(db, product.id, "created", "success", {
        "sku": product.sku,
        "name": product.name,
        "status": status,
        "validation_errors": [e.field for e in validation.errors] if not validation.valid else [],
    })

    # Return product with validation info
    result = product_to_dict(product)
    result['listing_copies_supported'] = True
    result['validation'] = validation.to_dict()
    result['is_amazon_ready'] = validation.valid
    return result


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Use raw SQL to bypass SQLAlchemy relationship cascade issues
        # Step 1: Delete activity logs
        db.execute(text("DELETE FROM activity_logs WHERE product_id = :pid"), {"pid": product_id})
        
        # Step 2: Delete inventory records
        db.execute(text("DELETE FROM inventory WHERE product_id = :pid"), {"pid": product_id})
        
        # Step 3: Delete listings (may have FK to sellers too, so use raw SQL)
        db.execute(text("DELETE FROM listings WHERE product_id = :pid"), {"pid": product_id})
        
        # Step 4: Delete the product
        db.execute(text("DELETE FROM products WHERE id = :pid"), {"pid": product_id})
        
        db.commit()
        logger.info(f"Product {product_id} deleted successfully")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


@router.put("/{product_id}")
async def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle JSON fields (dict/list → JSON string for SQLite)
    json_fields = [
        'bullet_points', 'bullet_points_ar', 'bullet_points_en',
        'keywords', 'images', 'dimensions', 'attributes',
        'optimized_data', 'unit_count'  # ← FIX: unit_count is a dict
    ]
    for field, value in update_data.items():
        if field in json_fields and value is not None:
            setattr(product, field, json.dumps(value))
        else:
            setattr(product, field, value)

    # Re-validate after update to determine if status should change
    from app.services.validation_service import ValidationService

    # Parse JSON fields for validation
    images = []
    try:
        images = json.loads(product.images) if isinstance(product.images, str) else (product.images or [])
    except Exception:
        images = []

    bullet_points = []
    try:
        bullet_points = json.loads(product.bullet_points) if isinstance(product.bullet_points, str) else (product.bullet_points or [])
    except Exception:
        bullet_points = []

    validation = ValidationService.validate_product(
        sku=product.sku,
        name=product.name,
        price=float(product.price) if product.price else 0,
        images=images,
        brand=product.brand or "",
        product_type=product.product_type or "",
        condition=product.condition or "New",
        fulfillment_channel=product.fulfillment_channel or "MFN",
        upc=product.upc or "",
        ean=product.ean or "",
        bullet_points=bullet_points,
    )

    # Update status based on validation
    if validation.valid and product.status == "incomplete":
        product.status = "draft"  # Now ready for Amazon
    elif not validation.valid and product.status != "incomplete":
        product.status = "incomplete"

    db.commit()
    db.refresh(product)

    # Log activity
    create_activity_log(db, product.id, "updated", "success", {
        "fields_updated": list(update_data.keys()),
        "new_status": product.status,
    })

    return product_to_dict(product)


@router.post("/lookup")
async def lookup_product(product_id: str, id_type: str = "EAN", db: Session = Depends(get_db)):
    """
    يبحث في Amazon عن طريق ASIN/UPC/EAN قبل إضافة المنتج.
    لو موجود → يرفض. لو مش موجود → يسمح.
    """
    try:
        from app.services.amazon_lookup import AmazonProductLookup

        lookup = AmazonProductLookup("amazon_eg")
        result = await lookup.lookup(product_id, id_type)

        if result.get("found"):
            return {
                "available": False,
                "reason": f"Product already exists on Amazon",
                "asin": result.get("asin"),
                "title": result.get("title"),
            }
        else:
            return {
                "available": True,
                "reason": "Product not found on Amazon - safe to add",
            }
    except Exception as e:
        # لو البحث فشل → نسمح بالحفظ (مش هنعوق المستخدم)
        logger.warning(f"Lookup failed: {e}")
        return {
            "available": True,
            "reason": f"Lookup skipped: {str(e)}",
        }


@router.post("/preview-feed")
async def preview_amazon_feed(data: ProductCreate):
    """
    يولّد معاينة للبيانات اللي هتترسل لـ Amazon (JSON format - Listings Items API)
    Amazon deprecated XML feeds من مارس 2024. الطريقة الجديدة JSON.
    
    Reference: https://developer-docs.amazon.com/sp-api/docs/create-a-listing
    """
    from app.services.listings_items_service import ListingsItemsService
    from app.services.validation_service import ValidationService

    # Build images list
    images = data.images or []
    image_urls = images  # Already URLs after upload

    # Build bullet points from description
    bullet_points = data.bullet_points or []
    if not bullet_points and data.description_en:
        bullet_points = [s.strip() for s in data.description_en.replace('\n', '.').split('.') if len(s.strip()) > 10][:5]

    # Build the Amazon Listings Items API payload
    payload = ListingsItemsService.build_listing_payload(
        sku=data.sku or f"AUTO-PREVIEW",
        name=data.name,
        brand=data.brand or "Generic",
        price=float(data.price) if data.price else 0,
        quantity=data.quantity or 0,
        product_type=data.product_type or "",
        description=data.description_en or data.description or "",
        bullet_points=bullet_points,
        images=image_urls,
        condition=data.condition or "New",
        manufacturer=data.manufacturer or "",
        model_number=data.model_number or "",
        country_of_origin=data.country_of_origin or "",
        material=data.material or "",
        target_audience=data.target_audience or "",
        keywords=data.keywords or [],
        weight=float(data.weight) if data.weight else None,
        weight_unit="kilograms",
        dimensions=data.dimensions or {},
        handling_time=data.handling_time or 1,
        package_quantity=data.package_quantity or 1,
        number_of_items=data.number_of_items or 1,
        browse_node_id=data.browse_node_id or "",
        currency=data.currency or "EGP",
        compare_price=float(data.compare_price) if data.compare_price else None,
        sale_price=float(data.sale_price) if data.sale_price else None,
    )

    # Validation
    validation = ValidationService.validate_product(
        sku=payload.get("attributes", {}).get("item_name", [{}])[0].get("value", ""),
        name=payload.get("attributes", {}).get("item_name", [{}])[0].get("value", ""),
        price=float(data.price) if data.price else 0,
        images=image_urls,
        brand=data.brand or "Generic",
        product_type=data.product_type or "",
        condition=data.condition or "New",
        fulfillment_channel=data.fulfillment_channel or "MFN",
        upc=data.upc or "",
        ean=data.ean or "",
        bullet_points=bullet_points,
    )

    # Count filled attributes
    total_attrs = len([k for k, v in payload.get("attributes", {}).items() if v])
    total_offer = len(payload.get("offer", {}).get("attributes", {}))

    return {
        "validation": validation.to_dict(),
        "api_type": "Listings Items API (JSON)",
        "api_deprecated": "XML feeds (POST_PRODUCT_DATA) deprecated by Amazon since March 2024",
        "endpoint": ListingsItemsService.get_endpoint(),
        "marketplace_id": ListingsItemsService.MARKETPLACE_ID,
        "language_tag": ListingsItemsService.LANGUAGE_TAG,
        "required_attributes": ListingsItemsService.get_required_attributes(),
        "json_payload": payload,
        "rate_limit_info": {
            "max_requests_per_second": 20,
            "max_requests_per_5min": 100,
            "retry_strategy": "Exponential Backoff (1s, 2s, 4s, 8s, 16s, 32s)",
            "max_retries": 5,
            "jitter": "0-1s random delay added to avoid thundering herd",
        },
        "summary": {
            "total_attributes": total_attrs,
            "total_offer_attributes": total_offer,
            "errors": len(validation.errors),
            "warnings": len(validation.warnings),
            "ready_for_amazon": validation.valid,
        },
    }


@router.post("/match-skus")
async def match_skus(db: Session = Depends(get_db)):
    """
    Match local product SKUs with Amazon inventory.
    Returns matched, unmatched, updated counts and list of SKUs needing listing.
    """
    from app.services.sku_matcher import SKUMatcher

    result = await SKUMatcher.match_skus(db)
    return result


@router.post("/{product_id}/submit-to-amazon")
async def submit_product_to_amazon(product_id: str):
    """
    Submit a product to Amazon via SP-API.

    This endpoint calls the SP-API router internally.
    """
    from app.api.sp_api_router import submit_product_to_amazon as sp_submit
    from fastapi import BackgroundTasks
    
    # Note: BackgroundTasks won't work here properly, use /sp-api/submit/{product_id} instead
    return await sp_submit(product_id)
