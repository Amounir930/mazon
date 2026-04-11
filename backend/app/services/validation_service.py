"""
Validation Service
Validates product data before submission to Amazon
"""
from typing import Optional
from dataclasses import dataclass, field
import re


@dataclass
class ValidationError:
    """A single validation error"""
    field: str
    message: str


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str):
        self.valid = False
        self.errors.append(ValidationError(field=field, message=message))

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": [
                {"field": e.field, "message": e.message}
                for e in self.errors
            ],
        }


class ValidationService:
    """Validate product data before Amazon submission"""

    @staticmethod
    def validate_product(
        sku: Optional[str] = None,
        name: Optional[str] = None,
        price: Optional[float] = None,
        images: Optional[list] = None,
        brand: Optional[str] = None,
        product_type: Optional[str] = None,
        condition: Optional[str] = None,
        fulfillment_channel: Optional[str] = None,
        upc: Optional[str] = None,
        ean: Optional[str] = None,
        bullet_points: Optional[list] = None,
    ) -> ValidationResult:
        """
        Validate all product fields before submission.

        Rules:
        - SKU: len >= 3, no <>"'&
        - Name: len >= 5
        - Price: > 0
        - Images: at least 1
        - Brand: len >= 2
        - Product Type: required (Amazon rejects without it)
        - Condition: required (Amazon rejects without it)
        - Fulfillment Channel: required (Amazon rejects without it)
        - UPC: 12 digits if provided
        - EAN: 13 digits if provided
        - Bullet Points: at least 1 required
        """
        result = ValidationResult()

        # SKU validation
        if sku is None or len(sku.strip()) < 3:
            result.add_error("sku", "SKU must be at least 3 characters")
        else:
            if any(c in sku for c in '<>"\'&'):
                result.add_error("sku", "SKU contains invalid characters")

        # Name validation
        if name is None or len(name.strip()) < 5:
            result.add_error("name", "Product name must be at least 5 characters")

        # Price validation
        if price is None or price <= 0:
            result.add_error("price", "Price must be greater than 0")

        # Images validation
        if images is None or len(images) < 1:
            result.add_error("images", "At least one image is required")

        # Brand validation
        if brand is None or len(brand.strip()) < 2:
            result.add_error("brand", "Brand name is required")

        # Product Type validation (required by Amazon)
        if product_type is None or len(product_type.strip()) < 1:
            result.add_error("product_type", "Product Type is required by Amazon")

        # Condition validation (required by Amazon)
        valid_conditions = ["New", "UsedLikeNew", "UsedVeryGood", "UsedGood", "UsedAcceptable", "Refurbished", "CollectibleLikeNew", "CollectibleVeryGood", "CollectibleGood", "CollectibleAcceptable", "Club"]
        if condition is None or condition not in valid_conditions:
            result.add_error("condition", f"Condition is required and must be one of: {', '.join(valid_conditions[:5])}...")

        # Fulfillment Channel validation (required by Amazon)
        valid_fulfillment = ["MFN", "AFN"]
        if fulfillment_channel is None or fulfillment_channel not in valid_fulfillment:
            result.add_error("fulfillment_channel", f"Fulfillment channel is required and must be one of: {', '.join(valid_fulfillment)}")

        # UPC validation (12 digits if provided)
        if upc is not None and upc.strip():
            upc_clean = upc.strip()
            if not re.match(r'^\d{12}$', upc_clean):
                result.add_error("upc", "UPC must be exactly 12 digits")

        # EAN validation (13 digits if provided)
        if ean is not None and ean.strip():
            ean_clean = ean.strip()
            if not re.match(r'^\d{13}$', ean_clean):
                result.add_error("ean", "EAN must be exactly 13 digits")

        # At least one of UPC or EAN should be provided
        if (upc is None or not upc.strip()) and (ean is None or not ean.strip()):
            result.add_error("upc_ean", "At least one of UPC or EAN is required for Amazon listing")

        # Bullet Points validation (at least 1 required by Amazon)
        if bullet_points is None or len(bullet_points) < 1:
            result.add_error("bullet_points", "At least one bullet point is required by Amazon")

        return result

    @staticmethod
    def validate_product_dict(product: dict) -> ValidationResult:
        """Validate a product dictionary"""
        return ValidationService.validate_product(
            sku=product.get("sku"),
            name=product.get("name"),
            price=product.get("price"),
            images=product.get("images", []),
            brand=product.get("brand"),
            product_type=product.get("product_type"),
            condition=product.get("condition"),
            fulfillment_channel=product.get("fulfillment_channel"),
            upc=product.get("upc"),
            ean=product.get("ean"),
            bullet_points=product.get("bullet_points", []),
        )
