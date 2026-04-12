"""
Product Auto-Fill Service
يولد البيانات التلقائية للمنتجات بناءً على قواعد منطقية (بدون AI)
"""
import time
from typing import Dict, Any, List, Optional


class ProductAutoFill:
    """يملأ الحقول تلقائياً بناءً على القوالب والقواعد"""

    # قوالب جاهزة حسب نوع المنتج
    TEMPLATES: Dict[str, Dict[str, Any]] = {
        "HOME_ORGANIZERS_AND_STORAGE": {
            "brand": "Generic",
            "condition": "New",
            "fulfillment_channel": "MFN",
            "browse_node": "85363278031",
            "country_of_origin": "CN",
        },
        "BABY_PRODUCT": {
            "brand": "Generic",
            "condition": "New",
            "fulfillment_channel": "MFN",
            "browse_node": "85363290031",
            "country_of_origin": "CN",
        },
        "APPAREL": {
            "brand": "Generic",
            "condition": "New",
            "fulfillment_channel": "MFN",
            "browse_node": "85363295031",
            "country_of_origin": "CN",
        },
    }

    @staticmethod
    def generate_sku() -> str:
        """يولد SKU فريد"""
        return f"AUTO-{int(time.time())}"

    @staticmethod
    def extract_bullets(description: str, max_count: int = 5) -> List[str]:
        """يستخرج bullet points من الوصف"""
        sentences = description.replace('\n', '.').split('.')
        bullets = [s.strip() for s in sentences if len(s.strip()) > 10]
        return bullets[:max_count]

    @staticmethod
    def extract_keywords(name: str, product_type: str) -> List[str]:
        """يستخرج كلمات بحث من الاسم والفئة"""
        words = name.split()
        keywords = words + [product_type.replace('_', ' ').lower()]
        return keywords[:5]

    @staticmethod
    def build_payload(
        name: str,
        product_type: str,
        price: float,
        quantity: int,
        description: str,
        brand: str = "Generic",
        condition: str = "New",
        fulfillment_channel: str = "MFN",
        country_of_origin: str = "CN",
        upc: Optional[str] = None,
        ean: Optional[str] = None,
        asin: Optional[str] = None,
        gtin_exempt: bool = False,
        images: Optional[List[str]] = None,
        model_number: Optional[str] = None,
        manufacturer: Optional[str] = None,
        weight: Optional[float] = None,
        weight_unit: Optional[str] = None,
        dimensions: Optional[Dict[str, Any]] = None,
        listing_copies: int = 1,
    ) -> Dict[str, Any]:
        """يبني JSON payload كامل لإرساله لـ Amazon"""

        template = ProductAutoFill.TEMPLATES.get(product_type, {})
        sku = ProductAutoFill.generate_sku()
        bullets = ProductAutoFill.extract_bullets(description)
        keywords = ProductAutoFill.extract_keywords(name, product_type)

        payload: Dict[str, Any] = {
            "sku": sku,
            "name": name,
            "brand": brand or template.get("brand", "Generic"),
            "price": float(price),
            "quantity": int(quantity),
            "description": description,
            "product_type": product_type,
            "condition": condition or template.get("condition", "New"),
            "fulfillment_channel": fulfillment_channel or template.get("fulfillment_channel", "MFN"),
            "country_of_origin": country_of_origin or template.get("country_of_origin", "CN"),
            "bullet_points": bullets,
            "keywords": keywords,
            "images": images or [],
            "listing_copies": listing_copies,
            "browse_node_id": template.get("browse_node", ""),
        }

        # UPC/EAN/ASIN
        if not gtin_exempt:
            if upc:
                payload["upc"] = upc
            elif ean:
                payload["ean"] = ean
            elif asin:
                payload["attributes"] = {"asin": asin}

        # Optional fields
        extras = {}
        if model_number:
            extras["model_number"] = model_number
        if manufacturer:
            extras["manufacturer"] = manufacturer
        if weight:
            extras["weight"] = weight
        if weight_unit:
            extras["weight_unit"] = weight_unit
        if dimensions:
            extras["dimensions"] = dimensions

        if extras:
            payload["attributes"] = {**payload.get("attributes", {}), **extras}

        return payload
