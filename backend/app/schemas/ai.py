"""
AI Product Generation — Pydantic Schemas
==========================================
Validation schemas for AI-generated product data.

Uses Base + Delta Pattern:
- base_product: Common fields shared across all variants
- variants: Per-product differences (name, description, SKU)
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class PriceEstimate(BaseModel):
    """Estimated price range in EGP"""
    min: float = Field(..., ge=0, description="Minimum price")
    max: float = Field(..., ge=0, description="Maximum price")


class BaseProductData(BaseModel):
    """
    Common product data shared across all variants.
    These fields are the same for every product generated.
    """
    brand: str = Field(default="Generic", min_length=1, max_length=200)
    manufacturer: str = Field(default="Generic", min_length=1, max_length=200)
    product_type: str = Field(..., min_length=1, max_length=100)
    price: Optional[float] = Field(default=None, description="Price in EGP - optional, AI leaves empty")
    ean: str = Field(..., min_length=13, max_length=13, description="EAN barcode - 13 digits, MANDATORY")
    upc: Optional[str] = Field(default="", max_length=12)
    bullet_points_ar: List[str] = Field(default_factory=list, min_items=5, max_items=5)
    bullet_points_en: List[str] = Field(default_factory=list, min_items=5, max_items=5)
    keywords: List[str] = Field(default_factory=list, max_items=50)
    material: str = Field(default="", max_length=200)
    target_audience: str = Field(default="", max_length=100)
    condition: str = Field(default="New", max_length=20)
    fulfillment_channel: str = Field(default="MFN", max_length=20)
    country_of_origin: str = Field(default="CN", max_length=10)
    model_number: str = Field(default="", max_length=100)
    included_components: str = Field(default="", max_length=200, description="Simple one-word component name")
    estimated_price_egp: Optional[PriceEstimate] = None

    @field_validator("ean")
    @classmethod
    def validate_ean(cls, v: str) -> str:
        """EAN must be 13 digits - MANDATORY"""
        if not v or not v.strip():
            raise ValueError("EAN is MANDATORY - AI must generate 13 digits")
        digits = v.strip().replace("-", "")
        if not digits.isdigit() or len(digits) != 13:
            raise ValueError("EAN must be exactly 13 digits")
        return v.strip()

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, v: str) -> str:
        """UPC must be 12 digits if provided"""
        if v and v.strip():
            digits = v.strip().replace("-", "")
            if not digits.isdigit() or len(digits) != 12:
                raise ValueError("UPC must be 12 digits")
        return v or ""


class ProductVariant(BaseModel):
    """
    Per-product variations.
    Only these fields differ between products.
    """
    variant_number: int = Field(..., ge=1, description="Variant index (1-based)")
    name_ar: str = Field(..., min_length=2, max_length=500, description="Arabic product name")
    name_en: str = Field(..., min_length=2, max_length=500, description="English product name")
    description_ar: str = Field(..., min_length=10, max_length=2000, description="Arabic description")
    description_en: str = Field(..., min_length=10, max_length=2000, description="English description")
    suggested_sku: str = Field(..., min_length=1, max_length=40, description="Auto-generated SKU")

    @field_validator("suggested_sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """SKU must be alphanumeric with hyphens"""
        if not v.strip():
            raise ValueError("SKU cannot be empty")
        return v.strip()


class AIProductResponse(BaseModel):
    """
    Full AI product generation response.
    
    Base + Delta Pattern:
    - base_product: Shared data (same for all variants)
    - variants: Per-product differences
    """
    base_product: BaseProductData
    variants: List[ProductVariant] = Field(..., min_items=1, max_items=10)


class AIProductRequest(BaseModel):
    """Request to generate products"""
    name: str = Field(..., min_length=2, max_length=200, description="Product name")
    specs: str = Field(..., min_length=5, max_length=2000, description="Product specifications")
    copies: int = Field(default=1, ge=1, le=10, description="Number of variants (1-10)")
    brand: Optional[str] = Field(default="Generic", max_length=200)
