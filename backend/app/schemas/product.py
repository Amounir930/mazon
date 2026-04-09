"""
Pydantic Schemas for Product Validation
Request/Response models for API endpoints
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ============ Product Schemas ============

class ProductBase(BaseModel):
    """Base product schema with common fields"""
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    parent_sku: Optional[str] = Field(None, max_length=100)
    is_parent: bool = Field(False)
    name: str = Field(..., min_length=2, max_length=500, description="Product name")
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=200)
    upc: Optional[str] = Field(None, max_length=50)
    ean: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    bullet_points: list[str] = Field(default=[], max_length=5)
    keywords: list[str] = Field(default=[])
    
    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("SKU cannot be empty")
        # Remove potentially harmful characters
        import re
        v = re.sub(r'[<>"\'&]', '', v)
        return v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Product name must be at least 2 characters")
        import re
        v = re.sub(r'[<>"\'&]', '', v)
        return v


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    price: Decimal = Field(..., gt=0, lt=999999, description="Product price")
    compare_price: Optional[Decimal] = Field(None, gt=0, lt=999999)
    cost: Optional[Decimal] = Field(None, gt=0)
    quantity: int = Field(default=0, ge=0, description="Available quantity")
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions: Optional[dict[str, Any]] = None
    images: list[str] = Field(default=[])
    attributes: dict[str, Any] = Field(default={})
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be positive")
        return v.quantize(Decimal("0.01"))
    
    @field_validator("compare_price")
    @classmethod
    def validate_compare_price(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        if v is not None:
            return v.quantize(Decimal("0.01"))
        return v


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    name: Optional[str] = Field(None, min_length=2, max_length=500)
    category: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    bullet_points: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    price: Optional[Decimal] = Field(None, gt=0, lt=999999)
    compare_price: Optional[Decimal] = Field(None, gt=0)
    cost: Optional[Decimal] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions: Optional[dict[str, Any]] = None
    images: Optional[list[str]] = None
    attributes: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: UUID
    seller_id: UUID
    price: Decimal
    compare_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    quantity: int
    weight: Optional[Decimal] = None
    dimensions: Optional[dict[str, Any]] = None
    images: list[str] = []
    attributes: dict[str, Any] = {}
    status: str
    optimized_data: Optional[dict[str, Any]] = None
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


# ============ Listing Schemas ============

class ListingCreate(BaseModel):
    """Schema for creating a listing submission"""
    product_id: UUID
    seller_id: UUID


class ListingResponse(BaseModel):
    """Schema for listing response"""
    id: UUID
    product_id: UUID
    seller_id: UUID
    feed_submission_id: Optional[str] = None
    status: str
    amazon_asin: Optional[str] = None
    amazon_url: Optional[str] = None
    error_message: Optional[str] = None
    queue_position: Optional[int] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Seller Schemas ============

class SellerCreate(BaseModel):
    """Schema for seller registration"""
    email: EmailStr
    seller_id: str = Field(..., min_length=1, max_length=100)
    marketplace_id: str = Field(..., min_length=1, max_length=20)
    region: str = Field(..., pattern="^(NA|EU|FE|ME)$")
    lwa_refresh_token: str
    mws_auth_token: Optional[str] = None


class SellerResponse(BaseModel):
    """Schema for seller response"""
    id: UUID
    email: str
    seller_id: str
    marketplace_id: str
    region: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Task Schemas ============

class TaskResponse(BaseModel):
    """Schema for task response"""
    id: UUID
    celery_task_id: Optional[str] = None
    task_type: str
    status: str
    payload: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    retries: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Generic Response Schemas ============

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
