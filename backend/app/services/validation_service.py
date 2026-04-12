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
    severity: str = "error"  # "error" = blocks submission, "warning" = recommended


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, message: str):
        self.valid = False
        self.errors.append(ValidationError(field=field, message=message, severity="error"))

    def add_warning(self, field: str, message: str):
        """Warning doesn't block submission but is recommended"""
        self.warnings.append(ValidationError(field=field, message=message, severity="warning"))

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": [
                {"field": e.field, "message": e.message, "severity": e.severity}
                for e in self.errors
            ],
            "warnings": [
                {"field": e.field, "message": e.message, "severity": e.severity}
                for e in self.warnings
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
        Validate all product data before submission.

        Amazon Requirements (based on official SP-API documentation):
        ===========================================================

        ❌ ABSOLUTELY REQUIRED (Amazon will REJECT without these):
        ---------------------------------------------------------
        - SKU (unique per seller)
        - Product Name / Title
        - Price
        - Product Type (category)
        - Condition Type
        - Fulfillment Channel (MFN/AFN)
        - Product ID (UPC/EAN/ISBN) OR GTIN Exemption

        ⚠️ STRONGLY RECOMMENDED (Amazon won't reject but listing will be poor):
        -----------------------------------------------------------------------
        - Brand (can use "Generic" for unbranded products - accepted by Amazon)
        - Bullet Points (key features - at least 1, ideally 5)
        - Description
        - At least 1 Image (listings without images convert poorly)

        ✅ OPTIONAL (nice to have):
        ----------------------------
        - Manufacturer
        - Model Number
        - Country of Origin
        - Weight
        - Dimensions
        - Search Terms (keywords)
        - Browse Node ID
        """
        result = ValidationResult()

        # ===== ERRORS (will block submission) =====

        # SKU
        if sku is None or len(sku.strip()) < 3:
            result.add_error("sku", "SKU must be at least 3 characters")
        else:
            if any(c in sku for c in '<>"\'&'):
                result.add_error("sku", "SKU contains invalid characters")

        # Name
        if name is None or len(name.strip()) < 5:
            result.add_error("name", "Product name must be at least 5 characters")

        # Price
        if price is None or price <= 0:
            result.add_error("price", "Price must be greater than 0")

        # Product Type (required by Amazon)
        if product_type is None or len(product_type.strip()) < 1:
            result.add_error("product_type", "Product Type is required by Amazon")

        # Condition (required by Amazon)
        valid_conditions = ["New", "UsedLikeNew", "UsedVeryGood", "UsedGood", "UsedAcceptable", "Refurbished", "CollectibleLikeNew", "CollectibleVeryGood", "CollectibleGood", "CollectibleAcceptable", "Club"]
        if condition is None or condition not in valid_conditions:
            result.add_error("condition", f"Condition is required and must be one of: {', '.join(valid_conditions[:5])}...")

        # Fulfillment Channel (required by Amazon)
        valid_fulfillment = ["MFN", "AFN"]
        if fulfillment_channel is None or fulfillment_channel not in valid_fulfillment:
            result.add_error("fulfillment_channel", f"Fulfillment channel is required and must be one of: {', '.join(valid_fulfillment)}")

        # UPC/EAN validation
        if upc is not None and upc.strip():
            upc_clean = upc.strip()
            if not re.match(r'^\d{12}$', upc_clean):
                result.add_error("upc", "UPC must be exactly 12 digits")

        if ean is not None and ean.strip():
            ean_clean = ean.strip()
            if not re.match(r'^\d{13}$', ean_clean):
                result.add_error("ean", "EAN must be exactly 13 digits")

        # ===== WARNINGS (won't block but recommended) =====

        # Images - Amazon technically accepts listings without images
        if images is None or len(images) < 1:
            result.add_warning("images", "No images - listing will perform poorly")
        elif len(images) < 3:
            result.add_warning("images", f"Only {len(images)} image(s) - Amazon recommends 3-6 images")

        # Brand - "Generic" is ACCEPTABLE and VALID per Amazon policy
        # Used for unbranded/white-label products
        if brand is None or len(brand.strip()) < 2:
            result.add_warning("brand", "No brand - will default to 'Generic' (acceptable)")
        elif brand.strip().lower() == "generic":
            # "Generic" is perfectly valid - Amazon explicitly allows it
            pass  # No error, no warning

        # Bullet Points - NOT required by Amazon (contrary to previous implementation)
        # Amazon accepts listings without bullet points, they just convert poorly
        if bullet_points is None or len(bullet_points) < 1:
            result.add_warning("bullet_points", "No bullet points - listings with bullet points convert better")
        elif len(bullet_points) < 3:
            result.add_warning("bullet_points", f"Only {len(bullet_points)} bullet point(s) - Amazon recommends 3-5")

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
