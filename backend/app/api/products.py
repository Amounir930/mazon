"""
Product API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import json
from decimal import Decimal

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductListResponse, MessageResponse
from app.api.activity_log import create_activity_log
from loguru import logger

router = APIRouter()


def product_to_dict(product: Product) -> dict:
    """Convert Product model to dict (handle JSON strings)"""
    d = {c.name: getattr(product, c.name) for c in product.__table__.columns}
    # Parse JSON strings
    for field in ['bullet_points', 'bullet_points_ar', 'bullet_points_en', 'keywords', 'images', 'dimensions', 'attributes', 'optimized_data']:
        val = d.get(field)
        if val and isinstance(val, str):
            try:
                d[field] = json.loads(val)
            except Exception:
                d[field] = [] if field not in ('dimensions', 'attributes', 'optimized_data') else {}
    # Convert Decimal to float for JSON serialization
    for field in ['price', 'compare_price', 'cost', 'weight', 'sale_price']:
        if d.get(field) is not None:
            d[field] = float(d[field])
    # Default currency
    if d.get('currency') is None:
        d['currency'] = 'EGP'
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
    # Check SKU uniqueness for this seller
    existing = db.query(Product).filter(
        Product.seller_id == data.seller_id,
        Product.sku == data.sku
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="SKU already exists for this seller"
        )

    product = Product(
        seller_id=data.seller_id,
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
        # Sale pricing
        sale_price=data.sale_price,
        sale_start_date=data.sale_start_date,
        sale_end_date=data.sale_end_date,
        browse_node_id=data.browse_node_id or "",
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Log activity
    create_activity_log(db, product.id, "created", "success", {"sku": product.sku, "name": product.name})

    # Return product with listing_copies support info
    result = product_to_dict(product)
    result['listing_copies_supported'] = True
    return result


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@router.put("/{product_id}")
async def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle JSON fields
    json_fields = ['bullet_points', 'bullet_points_ar', 'bullet_points_en', 'keywords', 'images', 'dimensions', 'attributes', 'optimized_data']
    for field, value in update_data.items():
        if field in json_fields and value is not None:
            setattr(product, field, json.dumps(value))
        else:
            setattr(product, field, value)

    db.commit()
    db.refresh(product)

    # Log activity
    create_activity_log(db, product.id, "updated", "success", {"fields_updated": list(update_data.keys())})

    return product_to_dict(product)


@router.post("/match-skus")
async def match_skus(db: Session = Depends(get_db)):
    """
    Match local product SKUs with Amazon inventory.
    Returns matched, unmatched, updated counts and list of SKUs needing listing.
    """
    from app.services.sku_matcher import SKUMatcher

    result = await SKUMatcher.match_skus(db)
    return result
