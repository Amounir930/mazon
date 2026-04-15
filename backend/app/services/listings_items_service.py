"""
Listings Items Service — Amazon SP-API (JSON-based, modern approach)

This is the Amazon-approved way to send product listings.
XML feeds (POST_PRODUCT_DATA) are DEPRECATED since March 2024.

Reference: https://developer-docs.amazon.com/sp-api/docs/create-a-listing
Product Type Definitions API: GET /definitions/2020-09-01/productTypes/{productType}
"""
from typing import Optional
from loguru import logger


class ListingsItemsService:
    """
    Build JSON payloads for Amazon Listings Items API.
    
    CRITICAL NOTES (based on official Amazon SP-API documentation):
    ============================================================
    
    1. Endpoint: PUT /listings/2021-08-01/items/{sellerId}/{sku}
       (NOT /listings/2021-08-01/listings/ — that's wrong)
    
    2. NO "offer" root key exists in Listings Items API.
       Price, quantity, condition, fulfillment are ALL attributes
       inside the "attributes" object.
    
    3. Image attributes use: main_product_image_locator, 
       other_product_image_locator_1 through other_product_image_locator_8
       with "media_location" key (NOT "link" or "variant").
    
    4. Each bullet point is a SEPARATE object in the array,
       NOT an array of strings inside one value.
    
    5. Price uses: purchasable_offer → our_price → schedule → value_with_tax
    
    6. Quantity uses: fulfillment_availability → quantity + fulfillment_channel_code
    
    7. All attributes follow this pattern:
       "attribute_name": [{"value": ..., "marketplace_id": ..., "language_tag": ...}]
    """

    # Egypt marketplace config
    MARKETPLACE_ID = "ARBP9OOSHTCHU"
    LANGUAGE_TAG = "en_AE"  # English for Egypt/UAE marketplace

    @staticmethod
    def build_listing_payload(
        sku: str,
        name: str,
        brand: str,
        price: float,
        quantity: int,
        product_type: str,
        description: str = "",
        bullet_points: list = None,
        images: list = None,
        condition: str = "New",
        manufacturer: str = "",
        model_number: str = "",
        country_of_origin: str = "",
        material: str = "",
        target_audience: str = "",
        keywords: list = None,
        weight: float = None,
        weight_unit: str = "kilograms",
        dimensions: dict = None,
        handling_time: int = 1,
        package_quantity: int = 1,
        number_of_items: int = 1,
        browse_node_id: str = "",
        currency: str = "EGP",
        compare_price: float = None,
        sale_price: float = None,
    ) -> dict:
        """
        Build the EXACT JSON payload Amazon expects for Listings Items API.
        
        Endpoint: PUT /listings/2021-08-01/items/{sellerId}/{sku}
        
        This payload structure is based on the official Amazon SP-API documentation
        and has been validated against the Product Type Definitions API schema
        for HOME_ORGANIZERS_AND_STORAGE.
        """
        # Build attributes — EVERYTHING goes inside "attributes"
        attrs = {}

        # ===== REQUIRED ATTRIBUTES (Amazon will reject without these) =====
        
        # Title / Item Name
        attrs["item_name"] = [
            {"value": name, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
        ]

        # Brand
        attrs["brand"] = [
            {"value": brand or "Generic", "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
        ]

        # Manufacturer (required by Amazon for most categories)
        if manufacturer:
            attrs["manufacturer"] = [
                {"value": manufacturer, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
            ]

        # Country of Origin (required for most categories)
        if country_of_origin:
            attrs["country_of_origin"] = [
                {"value": country_of_origin, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
            ]

        # ===== RECOMMENDED ATTRIBUTES =====

        # Description
        if description:
            attrs["item_description"] = [
                {"value": description, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
            ]

        # Bullet Points (Key Product Features)
        # Each point is a SEPARATE object in the array
        if bullet_points:
            attrs["bullet_point"] = []
            for point in bullet_points[:5]:  # Amazon allows max 5
                attrs["bullet_point"].append({
                    "value": point,
                    "marketplace_id": ListingsItemsService.MARKETPLACE_ID,
                    "language_tag": ListingsItemsService.LANGUAGE_TAG
                })

        # Images
        # Amazon uses: main_product_image_locator + other_product_image_locator_1..8
        # Supports both public URLs AND Amazon upload destination IDs
        if images:
            for idx, img_ref in enumerate(images[:9]):  # Amazon allows max 9 images
                # Determine if this is a URL or Amazon image ID
                if img_ref.startswith("http://") or img_ref.startswith("https://"):
                    # Public URL - Amazon will fetch it
                    media_value = {"media_location": img_ref, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
                else:
                    # Amazon upload destination ID - stored on Amazon's servers
                    media_value = {"media_location": img_ref, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
                
                logger.info(f"🖼️ Image {idx}: {img_ref[:80]}...")
                
                if idx == 0:
                    # Main image
                    attrs["main_product_image_locator"] = [media_value]
                else:
                    # Additional images: other_product_image_locator_1, _2, ...
                    attrs[f"other_product_image_locator_{idx}"] = [media_value]

        # Material
        if material:
            attrs["material"] = [
                {"value": material, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
            ]

        # Target Audience
        if target_audience:
            attrs["target_audience_keyword"] = [
                {"value": target_audience, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
            ]

        # Search Terms (Keywords) — Max 250 bytes
        if keywords:
            search_terms = " ".join(keywords[:15])
            if len(search_terms) > 250:
                search_terms = search_terms[:247]
            attrs["generic_keyword"] = [
                {"value": search_terms, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
            ]

        # Model Number
        if model_number:
            attrs["model_number"] = [
                {"value": model_number, "marketplace_id": ListingsItemsService.MARKETPLACE_ID, "language_tag": ListingsItemsService.LANGUAGE_TAG}
            ]

        # Number of Items
        if number_of_items > 1:
            attrs["number_of_items"] = [
                {"value": number_of_items, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
            ]

        # Weight
        if weight:
            attrs["item_weight"] = [
                {"value": {"value": weight, "unit": weight_unit.lower()}, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
            ]

        # Dimensions
        if dimensions and isinstance(dimensions, dict):
            unit = dimensions.get("unit", "centimeters").lower()
            attrs["item_dimensions"] = [
                {
                    "value": {
                        "length": dimensions.get("length"),
                        "width": dimensions.get("width"),
                        "height": dimensions.get("height"),
                        "unit": unit
                    },
                    "marketplace_id": ListingsItemsService.MARKETPLACE_ID
                }
            ]

        # ===== OFFER ATTRIBUTES (Inside "attributes", NOT separate root key) =====

        # Condition Type
        condition_map = {
            "New": "new_new",
            "New - Open Box": "new_open_box",
            "New - OEM": "new_oem",
            "Refurbished": "refurbished_refurbished",
            "Used - Like New": "used_like_new",
            "Used - Very Good": "used_very_good",
            "Used - Good": "used_good",
            "Used - Acceptable": "used_acceptable",
        }
        attrs["condition_type"] = [
            {"value": condition_map.get(condition, "new_new"), "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
        ]

        # Price — uses purchasable_offer → our_price → schedule → value_with_tax
        # CRITICAL: Must be float (with decimal places) to avoid Amazon SP-API parsing issues
        if price > 0:
            attrs["purchasable_offer"] = [
                {
                    "currency": currency,
                    "our_price": [
                        {
                            "schedule": [
                                {"value_with_tax": float(price)}  # Always float (e.g. 150.00, not 150)
                            ]
                        }
                    ],
                    "marketplace_id": ListingsItemsService.MARKETPLACE_ID
                }
            ]

        # Compare Price (List Price / Was Price)
        if compare_price and compare_price > price:
            attrs["list_price"] = [
                {
                    "currency": currency,
                    "value": compare_price,
                    "marketplace_id": ListingsItemsService.MARKETPLACE_ID
                }
            ]

        # Sale Price
        if sale_price and sale_price > 0:
            attrs["sale_price"] = [
                {
                    "currency": currency,
                    "value": sale_price,
                    "marketplace_id": ListingsItemsService.MARKETPLACE_ID
                }
            ]

        # Fulfillment & Quantity — uses fulfillment_availability
        # CRITICAL: Must be properly formatted for Amazon to accept it
        # MFN (Merchant Fulfilled Network) = DEFAULT
        # AFN (Amazon Fulfilled / FBA) = AMAZON_NA (or similar)
        attrs["fulfillment_availability"] = [
            {
                "fulfillment_channel_code": "DEFAULT",
                "quantity": quantity,
                "marketplace_id": ListingsItemsService.MARKETPLACE_ID
            }
        ]

        # Handling Time (days)
        if handling_time and handling_time > 0:
            attrs["max_order_handling_time"] = [
                {"value": handling_time, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
            ]

        # Package Quantity
        if package_quantity and package_quantity > 1:
            attrs["unit_count"] = [
                {"value": package_quantity, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
            ]

        # Browse Node ID
        if browse_node_id:
            attrs["browse_node_id"] = [
                {"value": browse_node_id, "marketplace_id": ListingsItemsService.MARKETPLACE_ID}
            ]

        # Build the FINAL payload
        # NO "offer" root key — everything is inside "attributes"
        payload = {
            "productType": product_type,
            "requirements": "LISTING",  # Full listing (product + offer)
            "attributes": attrs,
        }

        return payload

    @staticmethod
    def get_endpoint() -> str:
        """
        Return the correct Amazon SP-API endpoint with query parameters.
        
        CRITICAL: marketplaceIds query parameter is REQUIRED.
        Without it, Amazon returns 400 Bad Request even if the JSON is valid.
        """
        return "PUT /listings/2021-08-01/items/{sellerId}/{sku}?marketplaceIds=ARBP9OOSHTCHU"

    @staticmethod
    def get_required_attributes(product_type: str = "HOME_ORGANIZERS_AND_STORAGE") -> list:
        """
        Return list of required attributes for a given product type.
        
        NOTE: In production, this should call the Product Type Definitions API:
        GET /definitions/2020-09-01/productTypes/{productType}?marketplaceIds={marketplace}&requirements=LISTING
        
        For now, using known required attributes for HOME_ORGANIZERS_AND_STORAGE.
        """
        return [
            "item_name",
            "brand",
            "manufacturer",
            "product_type",
            "main_product_image_locator",
            "country_of_origin",
            "purchasable_offer",
            "condition_type",
            "fulfillment_availability",
        ]
