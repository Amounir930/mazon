"""
Product Model
Represents a product in the catalog
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Product(Base):
    """Product catalog model"""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Information
    sku = Column(String(100), nullable=False, index=True)
    parent_sku = Column(String(100), index=True)  # To support Variation logic
    is_parent = Column(Boolean, default=False)  # True if this is a parent container
    name = Column(String(500), nullable=False)
    category = Column(String(100))
    brand = Column(String(200))
    
    # Identifiers
    upc = Column(String(50))
    ean = Column(String(50))
    
    # Content
    description = Column(Text)
    bullet_points = Column(JSON, default=list)  # Array of bullet points
    keywords = Column(ARRAY(String), default=[])  # Search keywords
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    compare_price = Column(Numeric(10, 2))  # Price before discount
    cost = Column(Numeric(10, 2))  # Cost for margin calculation
    
    # Inventory
    quantity = Column(Integer, default=0)
    weight = Column(Numeric(8, 2))  # Weight in kg
    
    # Dimensions (JSON for flexibility)
    dimensions = Column(JSON)  # {"length": float, "width": float, "height": float, "unit": "cm"}
    
    # Media
    images = Column(JSON, default=list)  # Array of image URLs
    
    # Additional Attributes
    attributes = Column(JSON, default=dict)  # color, size, material, etc.
    
    # Status
    status = Column(String(20), default="draft")  # draft, queued, processing, published, failed
    
    # AI Optimization
    optimized_data = Column(JSON)  # Store AI optimization suggestions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    seller = relationship("Seller", backref="products")
    listings = relationship("Listing", back_populates="product", cascade="all, delete-orphan")
    
    # Unique constraint: seller can't have duplicate SKUs
    __table_args__ = (
        # UniqueConstraint('seller_id', 'sku'),
    )
    
    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"
