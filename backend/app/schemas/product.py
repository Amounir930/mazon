"""
Pydantic Schemas for Product Validation
Request/Response models for API endpoints
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import re


# ============ Product Schemas ============

class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    name: str = Field(..., min_length=2, max_length=500, description="Product name")
    name_ar: Optional[str] = Field(None, max_length=500)
    name_en: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=200)
    price: Decimal = Field(..., gt=0, lt=999999, description="Product price")
    compare_price: Optional[Decimal] = Field(None, gt=0, lt=999999)
    cost: Optional[Decimal] = Field(None, gt=0)
    quantity: int = Field(default=0, ge=0, description="Available quantity")
    weight: Optional[Decimal] = Field(None, gt=0)
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
        if v <= 0:
            raise ValueError("Price must be positive")
        return v.quantize(Decimal("0.01"))


class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    name: Optional[str] = Field(None, min_length=2, max_length=500)
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
    price: Optional[Decimal] = Field(None, gt=0, lt=999999)
    compare_price: Optional[Decimal] = Field(None, gt=0)
    cost: Optional[Decimal] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions: Optional[dict[str, Any]] = None
    images: Optional[list[str]] = None
    attributes: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: str
    sku: str
    name: str
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Decimal
    compare_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    quantity: int
    weight: Optional[Decimal] = None
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
