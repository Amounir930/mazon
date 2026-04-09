"""
Product API Endpoints
Handles product CRUD operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    MessageResponse,
)
from app.services.product_service import ProductService
from loguru import logger

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    seller_id: str = Query(..., description="Seller UUID"),
    db: Session = Depends(get_db),
):
    """
    Create a new product in the catalog.
    
    Requires seller_id to associate the product with the correct seller account.
    """
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    try:
        product = ProductService.create_product(db, seller_uuid, product_data)
        logger.info(f"Product created: {product.sku} for seller {seller_id}")
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
):
    """Get product details by ID"""
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    product = ProductService.get_product(db, product_uuid)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/", response_model=ProductListResponse)
async def list_products(
    seller_id: str = Query(..., description="Filter by seller UUID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all products for a seller with pagination and filtering.
    """
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    products, total = ProductService.get_products_by_seller(
        db, seller_uuid, status=status, category=category,
        skip=(page - 1) * page_size, limit=page_size
    )
    
    pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    update_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Update product details"""
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    try:
        product = ProductService.update_product(db, product_uuid, update_data)
        logger.info(f"Product updated: {product.sku}")
        return product
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
):
    """Delete a product"""
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    success = ProductService.delete_product(db, product_uuid)
    
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Product deleted: {product_id}")
    return {"message": "Product deleted successfully"}


@router.post("/bulk-create", response_model=list[ProductResponse], status_code=201)
async def bulk_create_products(
    products_data: list[ProductCreate],
    seller_id: str = Query(..., description="Seller UUID"),
    db: Session = Depends(get_db),
):
    """
    Create multiple products in a single request.
    
    Useful for bulk uploads from CSV/Excel files.
    """
    try:
        seller_uuid = UUID(seller_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller ID format")
    
    created_products = []
    
    try:
        for product_data in products_data:
            product = ProductService.create_product(db, seller_uuid, product_data)
            created_products.append(product)
        
        db.commit()
        logger.info(f"Bulk created {len(created_products)} products for seller {seller_id}")
        return created_products
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk create: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{product_id}/optimize")
async def optimize_product_listing(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Optimize product listing using AI.
    
    Returns optimized title, description, bullet points, and keywords.
    """
    try:
        product_uuid = UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    product = ProductService.get_product(db, product_uuid)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # TODO: Integrate with AI optimization service
    # For now, return placeholder
    return {
        "message": "AI optimization not yet implemented",
        "product_id": product_id,
    }
