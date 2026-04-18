"""
AI Product Generation — Pydantic Schemas
==========================================
Validation schemas for AI-generated product data.

Uses Base + Delta Pattern:
- base_product: Common fields shared across all variants
- variants: Per-product differences (name, description, SKU)
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, ClassVar


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
    
    # MANDATORY: Amazon SP-API product type — must be one of the official English values
    amazon_product_type: str = Field(
        default="HOME_ORGANIZERS_AND_STORAGE",
        description="Amazon SP-API product type (English only, e.g., SKIN_CLEANING_WIPE, SMALL_HOME_APPLIANCES)"
    )
    browse_node_id: str = Field(
        default="",
        description="Amazon Browse Node ID (e.g. 21863799031)"
    )
    product_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Amazon SP-API product type (English only, e.g., HOME_KITCHEN, ELECTRONICS)"
    )
    price: Optional[float] = Field(default=None, description="Price in EGP - optional, AI leaves empty")
    ean: str = Field(default="", max_length=13, description="EAN barcode - 13 digits or empty for GTIN exemption")
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

    # Valid Amazon SP-API product types
    VALID_PRODUCT_TYPES: ClassVar[set] = {
        "HOME_KITCHEN", "HOME_ORGANIZERS_AND_STORAGE", "ELECTRONICS",
        "BABY_PRODUCT", "APPAREL", "TOYS_AND_GAMES", "BEAUTY",
        "SPORTING_GOODS", "OFFICE_PRODUCTS", "PET_PRODUCTS",
        "LUGGAGE", "FURNITURE", "WIRELESS", "JEWELRY", "SPORTS",
        "LAWN_AND_GARDEN", "AUTOMOTIVE", "INDUSTRIAL", "MUSICAL_INSTRUMENTS",
        "VIDEO_GAMES", "SOFTWARE", "BOOKS", "DVD", "MUSIC",
        "GROCERY", "HEALTH_PERSONAL_CARE", "GIFT_CARD",
    }

    @field_validator("product_type")
    @classmethod
    def validate_product_type(cls, v: str) -> str:
        """Product type must not contain Arabic characters"""
        if not v or not v.strip():
            raise ValueError("product_type is MANDATORY")
        v_stripped = v.strip()
        # Reject if it contains Arabic characters
        if any('\u0600' <= c <= '\u06FF' for c in v_stripped):
            raise ValueError(
                f"product_type '{v_stripped}' contains Arabic characters. "
                f"Use English values only: HOME_KITCHEN, ELECTRONICS, BABY_PRODUCT, etc."
            )
        # Accept any non-Arabic value — backend normalizer will handle conversion
        return v_stripped

    @field_validator("ean")
    @classmethod
    def validate_ean(cls, v: str) -> str:
        """EAN must be 13 digits or empty for GTIN exemption"""
        if not v or not v.strip():
            return ""
        digits = v.strip().replace("-", "")
        if not digits.isdigit() or len(digits) != 13:
            raise ValueError("EAN must be exactly 13 digits if provided")
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
    model_name: str = Field(default="AH-0001", max_length=100, description="Sequential model name")

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
