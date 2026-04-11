"""
Validation Service
Validates product data before submission to Amazon
"""
from typing import Optional
from dataclasses import dataclass, field


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
    ) -> ValidationResult:
        """
        Validate all product fields before submission.

        Rules:
        - SKU: len >= 3, no <>"'&
        - Name: len >= 5
        - Price: > 0
        - Images: at least 1
        - Brand: len >= 2
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
        )
