"""
Product Model
Represents a product in the catalog
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Product(Base):
    """Product catalog model"""

    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(36), ForeignKey("sellers.id"), nullable=False, index=True)

    # Basic Information
    sku = Column(String(100), nullable=False, index=True)
    parent_sku = Column(String(100), index=True)  # To support Variation logic
    is_parent = Column(Boolean, default=False)  # True if this is a parent container
    name = Column(String(500), nullable=False)
    name_ar = Column(String(500))
    name_en = Column(String(500))
    category = Column(String(100))
    brand = Column(String(200))

    # Identifiers
    upc = Column(String(50))
    ean = Column(String(50))

    # Content
    description = Column(Text)
    description_ar = Column(Text)
    description_en = Column(Text)
    bullet_points = Column(Text, default="[]")  # JSON string
    bullet_points_ar = Column(Text, default="[]")
    bullet_points_en = Column(Text, default="[]")
    keywords = Column(Text, default="[]")  # JSON string

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    compare_price = Column(Numeric(10, 2))  # Price before discount
    cost = Column(Numeric(10, 2))  # Cost for margin calculation
    currency = Column(String(10), default="EGP")  # Currency code (ISO 4217)

    # Sale Pricing
    sale_price = Column(Numeric(10, 2))  # Promotional price
    sale_start_date = Column(DateTime(timezone=True))  # Sale start date
    sale_end_date = Column(DateTime(timezone=True))  # Sale end date

    # Inventory
    quantity = Column(Integer, default=0)
    weight = Column(Numeric(8, 2))  # Weight in kg

    # Dimensions (JSON string)
    dimensions = Column(Text, default="{}")

    # Media
    images = Column(Text, default="[]")  # JSON string

    # Additional Attributes
    attributes = Column(Text, default="{}")  # JSON string

    # Amazon-specific fields
    condition = Column(String(20), default="New")  # New, Used, Refurbished
    fulfillment_channel = Column(String(20), default="MFN")  # MFN (Merchant), AFN (Amazon)
    handling_time = Column(Integer, default=0)  # days
    product_type = Column(String(100))  # PRODUCT_TYPE
    manufacturer = Column(String(200))
    model_number = Column(String(100))
    country_of_origin = Column(String(10))
    package_quantity = Column(Integer, default=1)
    browse_node_id = Column(String(50))  # Amazon category node for better discoverability

    # Status
    status = Column(String(20), default="draft")  # draft, queued, processing, published, failed

    # AI Optimization
    optimized_data = Column(Text)  # JSON string

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    seller = relationship("Seller", back_populates="products")
    listings = relationship("Listing", back_populates="product")

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"
