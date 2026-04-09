"""
Product Service
Handles product CRUD operations and business logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, tuple
from uuid import UUID
from datetime import datetime

from app.models.product import Product
from app.models.seller import Seller
from app.schemas.product import ProductCreate, ProductUpdate
from loguru import logger


class ProductService:
    """Product CRUD operations"""
    
    @staticmethod
    def create_product(db: Session, seller_id: UUID, product_data: ProductCreate) -> Product:
        """Create a new product"""
        # Verify seller exists
        seller = db.query(Seller).filter(Seller.id == seller_id).first()
        if not seller:
            raise ValueError(f"Seller not found: {seller_id}")
        
        # Check for duplicate SKU
        existing = db.query(Product).filter(
            and_(Product.seller_id == seller_id, Product.sku == product_data.sku)
        ).first()
        
        if existing:
            raise ValueError(f"Product with SKU {product_data.sku} already exists for this seller")
        
        # Create product
        product = Product(
            seller_id=seller_id,
            **product_data.model_dump(),
            status="draft",
        )
        
        db.add(product)
        db.flush()  # Get product ID without committing
        logger.info(f"Product created: {product.sku} (ID: {product.id})")
        return product
    
    @staticmethod
    def get_product(db: Session, product_id: UUID) -> Optional[Product]:
        """Get product by ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_products_by_seller(
        db: Session,
        seller_id: UUID,
        status: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Product], int]:
        """Get all products for a seller with filtering and pagination"""
        query = db.query(Product).filter(Product.seller_id == seller_id)
        
        # Apply filters
        if status:
            query = query.filter(Product.status == status)
        if category:
            query = query.filter(Product.category == category)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
        
        return products, total
    
    @staticmethod
    def update_product(db: Session, product_id: UUID, update_data: ProductUpdate) -> Product:
        """Update product"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product not found: {product_id}")
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        
        db.flush()
        logger.info(f"Product updated: {product.sku} (ID: {product.id})")
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: UUID) -> bool:
        """Delete product"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
        
        db.delete(product)
        logger.info(f"Product deleted: {product_id}")
        return True
    
    @staticmethod
    def update_product_status(db: Session, product_id: UUID, status: str) -> Optional[Product]:
        """Update product status"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        
        product.status = status
        product.updated_at = datetime.utcnow()
        db.flush()
        return product
    
    @staticmethod
    def get_product_by_sku(db: Session, seller_id: UUID, sku: str) -> Optional[Product]:
        """Get product by SKU for a specific seller"""
        return db.query(Product).filter(
            and_(Product.seller_id == seller_id, Product.sku == sku)
        ).first()
