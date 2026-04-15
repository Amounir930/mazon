"""
Pydantic Schemas for Product Validation
Request/Response models for API endpoints
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import re


# ============ Product Schemas ============

class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    model_config = ConfigDict(protected_namespaces=(), extra='allow')
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    seller_id: Optional[str] = Field(None, description="Owner seller ID (auto-assigned if empty)")
    name: str = Field(..., min_length=2, max_length=500, description="Product name")
    name_ar: Optional[str] = Field(None, max_length=500)
    name_en: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=200)
    price: Decimal = Field(..., ge=0, lt=999999, description="Product price")  # Changed gt=0 to ge=0
    compare_price: Optional[Decimal] = Field(None, ge=0, lt=999999)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="EGP", max_length=10, description="Currency code (ISO 4217)")
    quantity: int = Field(default=0, ge=0, description="Available quantity")
    weight: Optional[Decimal] = Field(None, ge=0)

    # Sale pricing
    sale_price: Optional[Decimal] = Field(None, ge=0, lt=999999, description="Promotional sale price")
    sale_start_date: Optional[str] = Field(None, description="Sale start date (ISO format)")
    sale_end_date: Optional[str] = Field(None, description="Sale end date (ISO format)")
    
    # Frontend-only fields (not saved to DB)
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    listing_copies: Optional[int] = Field(None, ge=1)
    variation_theme: Optional[str] = None
    
    description: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    bullet_points: list[str] = Field(default=[])
    bullet_points_ar: list[str] = Field(default=[])
    bullet_points_en: list[str] = Field(default=[])
    keywords: list[str] = Field(default=[])
    dimensions: Optional[dict[str, Any]] = None
    images: list[str] = Field(default=[])
    attributes: dict[str, Any] = Field(default={})

    # Amazon-specific fields
    upc: Optional[str] = Field(None, max_length=50, description="UPC barcode (12 digits)")
    ean: Optional[str] = Field(None, max_length=50, description="EAN barcode (13 digits)")
    has_product_identifier: Optional[bool] = Field(default=False, description="GTIN exemption: product does not have a product identifier")
    condition: str = Field(default="New", max_length=20)
    fulfillment_channel: str = Field(default="MFN", max_length=20)
    handling_time: int = Field(default=0, ge=0)
    product_type: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    model_number: Optional[str] = Field(None, max_length=100)
    country_of_origin: Optional[str] = Field(None, max_length=10)
    package_quantity: int = Field(default=1, ge=1)
    browse_node_id: Optional[str] = Field(None, max_length=50, description="Amazon Browse Node ID")

    # Additional fields from Page 2
    material: Optional[str] = Field(None, max_length=200, description="Material / Composition")
    number_of_items: int = Field(default=1, ge=1, description="Number of items in package")
    unit_count: Optional[dict[str, Any]] = Field(None, description="Unit count: {value, type}")
    target_audience: Optional[str] = Field(None, max_length=100, description="Target audience")
    
    # Variation fields
    is_parent: Optional[bool] = Field(default=False)
    parent_sku: Optional[str] = Field(None, max_length=100)

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("SKU cannot be empty")
        v = re.sub(r'[<>"\'&]', '', v)
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Product name must be at least 2 characters")
        v = re.sub(r'[<>"\'&]', '', v)
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Price cannot be negative")
        # Allow 0 as placeholder — user can fill price later
        return v.quantize(Decimal("0.01"))


class ProductUpdate(BaseModel):
    """Schema for updating an existing product - relaxed validation for partial updates"""
    model_config = ConfigDict(protected_namespaces=(), extra='allow')
    seller_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    bullet_points: Optional[list[str]] = None
    bullet_points_ar: Optional[list[str]] = None
    bullet_points_en: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    price: Optional[Decimal] = Field(None, ge=0, lt=999999)  # ge=0 allows zero for partial updates
    compare_price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    quantity: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, ge=0)  # ge=0 allows zero

    # Sale pricing
    sale_price: Optional[Decimal] = Field(None, ge=0)  # ge=0 allows clearing sale price
    sale_start_date: Optional[str] = Field(None)
    sale_end_date: Optional[str] = Field(None)
    dimensions: Optional[dict[str, Any]] = None
    images: Optional[list[str]] = None
    attributes: Optional[dict[str, Any]] = None
    upc: Optional[str] = Field(None, max_length=50)
    ean: Optional[str] = Field(None, max_length=50)
    has_product_identifier: Optional[bool] = Field(None, description="GTIN exemption flag")
    condition: Optional[str] = Field(None, max_length=20)
    fulfillment_channel: Optional[str] = Field(None, max_length=20)
    handling_time: Optional[int] = Field(None, ge=0)
    product_type: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=200)
    model_number: Optional[str] = Field(None, max_length=100)
    country_of_origin: Optional[str] = Field(None, max_length=10)
    package_quantity: Optional[int] = Field(None, ge=1)
    browse_node_id: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    optimized_data: Optional[dict[str, Any]] = None
    optimized_data: Optional[str] = None
    # Additional fields from Page 2
    material: Optional[str] = Field(None, max_length=200)
    number_of_items: Optional[int] = Field(None, ge=1)
    unit_count: Optional[dict[str, Any]] = None
    target_audience: Optional[str] = Field(None, max_length=100)


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: str
    seller_id: str
    sku: str
    name: str
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Decimal
    compare_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    currency: str = "EGP"
    quantity: int
    weight: Optional[Decimal] = None

    # Sale pricing
    sale_price: Optional[Decimal] = None
    sale_start_date: Optional[str] = None
    sale_end_date: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    bullet_points: list[str] = []
    bullet_points_ar: list[str] = []
    bullet_points_en: list[str] = []
    keywords: list[str] = []
    dimensions: Optional[dict[str, Any]] = None
    images: list[str] = []
    attributes: dict[str, Any] = {}
    # Amazon-specific fields
    upc: Optional[str] = None
    ean: Optional[str] = None
    has_product_identifier: bool = False
    condition: str = "New"
    fulfillment_channel: str = "MFN"
    handling_time: int = 0
    product_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    country_of_origin: Optional[str] = None
    package_quantity: int = 1
    browse_node_id: Optional[str] = None
    material: Optional[str] = None
    number_of_items: int = 1
    unit_count: Optional[dict[str, Any]] = None
    target_audience: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated product list response"""
    items: list[ProductResponse]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool


# ============ Generic Response Schemas ============

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


# ============ Listing Schemas ============

class ListingCreate(BaseModel):
    """Schema for creating a listing submission"""
    product_id: str
    seller_id: str


class ListingResponse(BaseModel):
    """Schema for listing response"""
    id: str
    product_id: str
    seller_id: str
    feed_submission_id: Optional[str] = None
    status: str
    stage: Optional[str] = None
    amazon_asin: Optional[str] = None
    amazon_url: Optional[str] = None
    error_message: Optional[str] = None
    queue_position: Optional[int] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    retry_count: int = 0

    class Config:
        from_attributes = True
