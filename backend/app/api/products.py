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
    for field in ['price', 'compare_price', 'cost', 'weight']:
        if d.get(field) is not None:
            d[field] = float(d[field])
    # Convert datetime to string
    for field in ['created_at', 'updated_at']:
        val = d.get(field)
        if val and hasattr(val, 'isoformat'):
            d[field] = val.isoformat()
    return d


@router.get("", response_model=ProductListResponse)
async def list_products(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if status:
        query = query.filter(Product.status == status)
    if category:
        query = query.filter(Product.category == category)

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
    product = Product(
        sku=data.sku,
        name=data.name,
        name_ar=data.name_ar,
        name_en=data.name_en,
        category=data.category or "",
        brand=data.brand or "",
        price=data.price,
        quantity=data.quantity or 0,
        description=data.description or "",
        description_ar=data.description_ar or "",
        description_en=data.description_en or "",
        bullet_points=json.dumps(data.bullet_points or []),
        bullet_points_ar=json.dumps(data.bullet_points_ar or []),
        bullet_points_en=json.dumps(data.bullet_points_en or []),
        images=json.dumps(data.images or []),
        attributes=json.dumps(data.attributes or {}),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_to_dict(product)


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
    return product_to_dict(product)
