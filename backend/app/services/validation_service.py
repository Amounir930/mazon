"""
Validation Service
Validates product data before submission to Amazon
"""
from typing import Optional
from dataclasses import dataclass, field
import re
from loguru import logger


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

        # Fulfillment Channel - FIXED to MFN (Merchant Fulfilled Network)
        # No validation needed since it's always "MFN"

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

    @staticmethod
    def check_specs_fidelity(original_specs: str, generated_content: str,
                           field_name: str, min_ratio: float = 0.85) -> tuple[bool, list[str]]:
        """
        Validate specs preservation with detailed feedback.
        Returns: (is_valid, list_of_missing_terms)
        """
        if not original_specs or not generated_content:
            return True, []

        # Extract meaningful terms (improved regex)
        spec_terms = re.findall(
            r'[\u0600-\u06FF]{2,}|[a-zA-Z]{2,}[\d\.]*|[\d\.]+\s*[ألف-يA-Za-z]{1,3}',
            original_specs
        )
        spec_terms = [t.strip().lower() for t in spec_terms if len(t.strip()) > 2]

        if not spec_terms:
            return True, []

        # Check presence
        missing = [t for t in spec_terms if t not in generated_content.lower()]
        ratio = 1 - (len(missing) / len(spec_terms))

        if ratio < min_ratio:
            logger.warning(
                f"Specs fidelity low in {field_name}: "
                f"{len(spec_terms)-len(missing)}/{len(spec_terms)} matched. "
                f"Missing: {missing[:5]}"  # Show first 5 missing
            )
            return False, missing
        return True, []

    @staticmethod
    def check_variant_isolation(variants: list[dict]) -> tuple[bool, str]:
        """Ensure variants don't contain each other's unique content"""
        if len(variants) < 2:
            return True, ""

        # Extract unique identifiers per variant
        signatures = []
        for v in variants:
            sig = set((v.get('name_ar') or '').split() + (v.get('description_ar') or '').split())
            signatures.append(sig)

        # Check pairwise overlap
        for i in range(len(signatures)):
            for j in range(i+1, len(signatures)):
                overlap = len(signatures[i] & signatures[j])
                total = len(signatures[i] | signatures[j])
                if total > 10 and overlap/total > 0.7:  # 70% overlap threshold
                    return False, f"Variants {i+1} and {j+1} show high content overlap ({overlap/total:.1%})"

        return True, ""

    @staticmethod
    def check_cross_product_contamination(product_name: str, specs: str, generated_content: str) -> tuple[bool, list[str]]:
        """Check for cross-product contamination (e.g., blender getting lantern content)"""
        # Define forbidden seeds based on known problematic products
        FORBIDDEN_SEEDS = {
            "خلاط": ["فانوس", "رمضان", "هلال", "ديكور إسلامي", "lantern", "ramadan", "crescent"],
            "منظم أحذية": ["مطبخ", "ستانلس", "5 سرعات", "kitchen", "stainless", "speeds"],
            "فرشاة تنظيف": ["LED", "إضاءة", "بطارية", "lighting", "battery"],
            # Add more as needed
        }

        found_contaminants = []
        product_lower = product_name.lower()
        specs_lower = specs.lower()
        content_lower = generated_content.lower()

        for product_type, forbidden in FORBIDDEN_SEEDS.items():
            if product_type in product_lower or product_type in specs_lower:
                for seed in forbidden:
                    if seed in content_lower and seed not in product_lower and seed not in specs_lower:
                        found_contaminants.append(f"'{seed}' (forbidden for {product_type})")

        if found_contaminants:
            logger.warning(f"Cross-product contamination detected: {found_contaminants}")
            return False, found_contaminants

        return True, []
