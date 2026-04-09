"""
Product Model
Represents a product in the catalog
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, Boolean
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Product(Base):
    """Product catalog model"""

    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

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
    bullet_points = Column(Text, default="[]")  # JSON string
    keywords = Column(Text, default="[]")  # JSON string

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    compare_price = Column(Numeric(10, 2))  # Price before discount
    cost = Column(Numeric(10, 2))  # Cost for margin calculation

    # Inventory
    quantity = Column(Integer, default=0)
    weight = Column(Numeric(8, 2))  # Weight in kg

    # Dimensions (JSON string)
    dimensions = Column(Text, default="{}")

    # Media
    images = Column(Text, default="[]")  # JSON string

    # Additional Attributes
    attributes = Column(Text, default="{}")  # JSON string

    # Status
    status = Column(String(20), default="draft")  # draft, queued, processing, published, failed

    # AI Optimization
    optimized_data = Column(Text)  # JSON string

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"
