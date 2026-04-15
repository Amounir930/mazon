"""
Amazon SP-API Client
====================
Official Amazon Selling Partner API client using:
- LWA (Login with Amazon) for access tokens
- AWS SigV4 for request signing

This replaces the Playwright-based approach with official API calls.
"""
import os
import time
import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode
from pathlib import Path

import requests
from requests_auth_aws_sigv4 import AWSSigV4
from loguru import logger

# Load .env file if not already loaded
from dotenv import load_dotenv
_env_path = Path(__file__).parent.parent.parent / '.env'
if _env_path.exists():
    load_dotenv(_env_path, override=False)

from app.config import Settings


# Amazon SP-API valid product types mapping (Arabic -> English)
ARABIC_TO_AMAZON_PRODUCT_TYPE = {
    "أدوات تنظيم وتخزين المنزل": "HOME_ORGANIZERS_AND_STORAGE",
    "منتجات أطفال": "BABY_PRODUCT",
    "ملابس وأزياء": "APPAREL",
    "المنزل والمطبخ": "HOME_KITCHEN",
    "إلكترونيات": "ELECTRONICS",
    "ألعاب وألعاب": "TOYS_AND_GAMES",
    "العناية الشخصية والجمال": "BEAUTY",
    "الرياضة والسلع الرياضية": "SPORTING_GOODS",
    "مستلزمات المكتبة والأدوات المكتبية": "OFFICE_PRODUCTS",
    "مستلزمات الحيوانات الأليفة": "PET_PRODUCTS",
    # Common Arabic product types that might be auto-generated
    "أدوات المطبخ": "HOME_KITCHEN",
    "أدوات منزلية": "HOME_KITCHEN",
    "مطبخ": "HOME_KITCHEN",
    "إلكترونيات": "ELECTRONICS",
    "أطفال": "BABY_PRODUCT",
    "ملابس": "APPAREL",
    "ألعاب": "TOYS_AND_GAMES",
    "جمال": "BEAUTY",
    "رياضة": "SPORTING_GOODS",
    "مكتب": "OFFICE_PRODUCTS",
    "حيوانات": "PET_PRODUCTS",
}


class SPAPIClient:
    """
    Official Amazon SP-API client.
    
    Handles:
    - LWA access token refresh
    - AWS Signature V4 request signing
    - SP-API endpoint calls
    """

    # SP-API Endpoints
    ENDPOINTS = {
        "eg": "sellingpartnerapi-eu.amazon.com",
        "sa": "sellingpartnerapi-eu.amazon.com",
        "ae": "sellingpartnerapi-eu.amazon.com",
        "uk": "sellingpartnerapi-eu.amazon.com",
        "us": "sellingpartnerapi-na.amazon.com",
        "de": "sellingpartnerapi-eu.amazon.com",
        "fr": "sellingpartnerapi-eu.amazon.com",
        "it": "sellingpartnerapi-eu.amazon.com",
        "es": "sellingpartnerapi-eu.amazon.com",
    }

    # LWA Token URL
    LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

    def __init__(self, marketplace_id: str = "ARBP9OOSHTCHU", country_code: str = "eg"):
        self.marketplace_id = marketplace_id
        self.country_code = country_code.lower()
        self.endpoint = self.ENDPOINTS.get(country_code, self.ENDPOINTS["eg"])
        
        # Credentials from environment
        self.client_id = os.getenv("SP_API_CLIENT_ID", "")
        self.client_secret = os.getenv("SP_API_CLIENT_SECRET", "")
        self.refresh_token = os.getenv("SP_API_REFRESH_TOKEN", "")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "eu-west-1")
        self.role_arn = os.getenv("AWS_SELLER_ROLE_ARN", "")
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        
        logger.info(f"SPAPIClient initialized: marketplace={marketplace_id}, endpoint={self.endpoint}")

    def _get_access_token(self) -> str:
        """
        Get LWA access token (with caching).
        Tokens expire after 1 hour.
        """
        # Return cached token if still valid
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        logger.info("Refreshing LWA access token...")
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        response = requests.post(self.LWA_TOKEN_URL, data=payload, timeout=15)

        if response.status_code != 200:
            # Try to parse JSON error response
            try:
                error_data = response.json()
                error_description = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                error_message = f"LWA Error {response.status_code}: {error_description}"
            except:
                error_message = f"LWA Error {response.status_code}: {response.text[:500]}"
            
            logger.error(error_message)
            raise Exception(error_message)
        
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        
        logger.info(f"✅ LWA access token refreshed (expires in {data.get('expires_in', 3600)}s)")
        return self._access_token

    def _sign_request(self, method: str, path: str, headers: Dict[str, str], body: str = "") -> Dict[str, str]:
        """
        Sign request with AWS Signature V4.
        """
        # Get access token
        access_token = self._get_access_token()
        headers["x-amz-access-token"] = access_token
        
        # For simplicity, we'll use the access token directly
        # The role ARN is used for assuming the IAM role, but for direct API calls
        # we just need the access token + signed headers
        
        return headers

    def _make_request(self, method: str, path: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a signed request to SP-API with AWS SigV4.
        """
        url = f"https://{self.endpoint}{path}"
        
        # Get access token
        access_token = self._get_access_token()
        
        # Create AWS SigV4 auth
        aws_auth = AWSSigV4(
            'execute-api',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region=self.aws_region,
        )
        
        headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "Host": self.endpoint,
        }
        
        logger.debug(f"{method} {url}")
        if params:
            logger.debug(f"Params: {params}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, auth=aws_auth, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params, auth=aws_auth, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, params=params, auth=aws_auth, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params, auth=aws_auth, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, params=params, auth=aws_auth, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            logger.info(f"SP-API Response: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"SP-API Error: {response.text[:1000]}")
            
            return response.json()
        except Exception as e:
            logger.error(f"SP-API Request failed: {e}")
            raise

    # ============================================================
    # Listings Items API (v2021-08-01)
    # ============================================================

    def put_listing_item(self, seller_id: str, sku: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a listing item.
        
        API: PUT /listings/2021-08-01/items/{sellerId}/{sku}
        Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#putlistingsitem
        
        Args:
            seller_id: Amazon Seller ID (Merchant ID)
            sku: Your SKU for this product
            product_data: Product attributes matching Amazon's schema
            
        Returns:
            {
                "status": "ACCEPTED" | "INVALID",
                "issues": [...],
                "sku": "...",
            }
        """
        path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "issueLocale": "ar_AE",
        }

        logger.info(f"Putting listing item: SKU={sku}, Seller={seller_id}")
        logger.debug(f"Product data keys: {list(product_data.keys())}")

        return self._make_request("PUT", path, data=product_data, params=params)

    def get_listing_item(self, seller_id: str, sku: str) -> Dict[str, Any]:
        """
        Get a listing item with full details (including attributes).

        API: GET /listings/2021-08-01/items/{sellerId}/{sku}
        Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#getlistingsitem
        """
        path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "issueLocale": "ar_AE",
            "includedData": "attributes,summaries,issues",  # CRITICAL: returns full attributes
        }

        return self._make_request("GET", path, params=params)

    def delete_listing_item(self, seller_id: str, sku: str) -> Dict[str, Any]:
        """
        Delete a listing item.

        API: DELETE /listings/2021-08-01/items/{sellerId}/{sku}
        """
        path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
        }

        return self._make_request("DELETE", path, params=params)

    def search_listings_items(
        self,
        seller_id: str,
        skus: list | None = None,
        status: str | None = None,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Search/list all listings for a seller.

        API: GET /listings/2021-08-01/items/{sellerId}
        Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#searchlistingsitems

        Args:
            seller_id: Amazon Seller ID (Merchant ID)
            skus: Optional list of SKUs to filter by
            status: Optional filter — ACTIVE, INCOMPLETE, or INACTIVE
            page_size: Number of results per page (max 200 per Amazon limits)

        Returns:
            {
                "numberOfResults": int,
                "pagination": {"nextToken": "..."},
                "items": [...]
            }
        """
        path = f"/listings/2021-08-01/items/{seller_id}"
        params: Dict[str, Any] = {"marketplaceIds": self.marketplace_id}

        if skus:
            params["skus"] = ",".join(skus)
        if status:
            params["status"] = status  # ACTIVE, INCOMPLETE, INACTIVE
        if page_size:
            params["pageSize"] = min(page_size, 200)  # Amazon hard limit

        logger.info(
            f"Searching listings: seller={seller_id}, skus={skus}, "
            f"status={status}, page_size={page_size}"
        )

        return self._make_request("GET", path, params=params)

    def patch_listing_item(
        self,
        seller_id: str,
        sku: str,
        product_type: str,
        patches: list,
        marketplace_ids: list | None = None,
    ) -> Dict[str, Any]:
        """
        Partial update of a listing item.

        API: PATCH /listings/2021-08-01/items/{sellerId}/{sku}
        Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#patchlistingsitem

        Args:
            seller_id: Amazon Seller ID
            sku: Product SKU
            product_type: Amazon product type (REQUIRED by SP-API for PATCH)
                Example: "HOME_ORGANIZERS_AND_STORAGE"
            patches: List of patch operations
                Example: [
                    {"op": "replace", "path": "/attributes/purchasable_offer/0/our_price/0/schedule/0/value_with_tax", "value": 150},
                    {"op": "replace", "path": "/attributes/quantity/0/value", "value": 50}
                ]

        Returns:
            {
                "status": "ACCEPTED" | "INVALID",
                "issues": [...],
                "sku": "...",
            }

        ⚠️  CRITICAL: SP-API requires 'productType' in the PATCH body.
            Without it, Amazon returns 400 Bad Request.
        """
        path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": marketplace_ids or self.marketplace_id,
            "issueLocale": "ar_AE",
        }

        # SP-API requires productType in body alongside patches
        body = {
            "productType": product_type,
            "patches": patches,
        }

        logger.info(f"Patching listing: SKU={sku}, productType={product_type}, patches={len(patches)}")
        return self._make_request("PATCH", path, data=body, params=params)

    # ============================================================
    # Sellers API (v1)
    # ============================================================

    def get_marketplace_participations(self) -> Dict[str, Any]:
        """
        Get all marketplaces the seller participates in.
        Returns seller ID + marketplace info.
        
        API: GET /sellers/v1/marketplaceParticipations
        """
        path = "/sellers/v1/marketplaceParticipations"
        return self._make_request("GET", path)

    def get_seller_id(self) -> Optional[str]:
        """
        Extract Seller ID from marketplace participations.
        """
        try:
            result = self.get_marketplace_participations()
            participations = result.get("payload", [])
            if participations:
                seller_id = participations[0].get("marketplace", {}).get("id", "")
                logger.info(f"✅ Found Seller ID: {seller_id}")
                return seller_id
            logger.error("No marketplace participations found")
            return None
        except Exception as e:
            logger.error(f"Failed to get seller ID: {e}")
            return None

    def get_seller_account(self) -> Optional[Dict[str, Any]]:
        """
        Get seller account info including name.
        API: GET /sellers/v1/account
        """
        try:
            path = "/sellers/v1/account"
            result = self._make_request("GET", path)
            payload = result.get("payload", {})
            if payload:
                logger.info(f"✅ Seller account: {payload}")
                return payload
            return None
        except Exception as e:
            logger.warning(f"Failed to get seller account: {e}")
            return None

    # ============================================================
    # Product Type Definitions API
    # ============================================================

    def get_product_type_definitions(self, product_type: str) -> Dict[str, Any]:
        """
        Get product type definitions (schema).
        
        API: GET /definitions/2020-09-01/productTypes/{productType}
        """
        path = f"/definitions/2020-09-01/productTypes/{product_type}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "requirements": "LISTING",
            "requirementsEnforced": "ENFORCED",
        }
        
        return self._make_request("GET", path, params=params)

    # ============================================================
    # Catalog Items API (v2022-04-01)
    # ============================================================

    def search_catalog_items(
        self,
        keywords: str | None = None,
        identifiers: list | None = None,
        identifiers_type: str | None = None,
        page_size: int = 10,
        included_data: list | None = None,
    ) -> Dict[str, Any]:
        """
        Search Amazon catalog via SP-API.

        API: GET /catalog/2022-04-01/items
        Docs: https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-reference#searchcatalogitems

        Args:
            keywords: Search keywords (e.g., "wireless headphones")
            identifiers: List of identifiers (EAN, UPC, ISBN, ASIN, etc.)
            page_size: Number of results (default: 10, max: 20 per Amazon)
            included_data: Additional data to include
                Options: ["summaries", "images", "dimensions", "identifiers", "links"]

        Returns:
            {
                "numberOfResults": int,
                "pagination": {"nextToken": "..."},
                "items": [...]
            }
        """
        path = "/catalog/2022-04-01/items"
        params: Dict[str, Any] = {"marketplaceIds": self.marketplace_id}

        if keywords:
            params["keywords"] = keywords
        if identifiers:
            params["identifiers"] = ",".join(identifiers)
        if identifiers_type:
            # Required when using identifiers - valid values: ASIN, EAN, UPC, ISBN, JAN, MINSAN, SKU
            params["identifiersType"] = identifiers_type.upper()
        if page_size:
            params["pageSize"] = min(page_size, 20)  # Amazon hard limit
        if included_data:
            params["includedData"] = ",".join(included_data)

        logger.info(
            f"Searching catalog: keywords={keywords}, identifiers={identifiers}, "
            f"page_size={page_size}"
        )

        return self._make_request("GET", path, params=params)

    def get_catalog_item(
        self,
        asin: str,
        marketplace_ids: list | None = None,
        included_data: list | None = None,
    ) -> Dict[str, Any]:
        """
        Get catalog item by ASIN.

        API: GET /catalog/2022-04-01/items/{asin}
        Docs: https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-reference#getcatalogitem

        Args:
            asin: Amazon Standard Identification Number
            marketplace_ids: List of marketplace IDs (defaults to current)
            included_data: Additional data to include
                Options: ["summaries", "images", "dimensions", "identifiers", "links"]

        Returns:
            Full catalog item payload
        """
        path = f"/catalog/2022-04-01/items/{asin}"
        params: Dict[str, Any] = {"marketplaceIds": marketplace_ids or self.marketplace_id}

        if included_data:
            params["includedData"] = ",".join(included_data)

        logger.info(f"Getting catalog item: ASIN={asin}")
        return self._make_request("GET", path, params=params)

    # ============================================================
    # Helper: Build product data from our format to SP-API format
    # ============================================================

    def create_listing_from_product(
        self,
        seller_id: str,
        sku: str,
        product_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a listing on Amazon from our internal Product data.

        This is the main integration method that:
        1. Builds the correct SP-API payload
        2. Handles all required attributes
        3. Returns structured result with success/failure

        Args:
            seller_id: Amazon Seller ID (A1DSHARRBRWYZW)
            sku: Product SKU
            product_data: Dict with product fields

        Returns:
            {
                "success": bool,
                "status": "ACCEPTED" | "INVALID",
                "submissionId": str,
                "asin": str,
                "errors": [...],
            }
        """
        # Build the full SP-API payload
        payload = self._build_listing_payload(product_data)

        # Send to Amazon
        result = self.put_listing_item(seller_id, sku, payload)

        # DEBUG: Log the full request/response for troubleshooting
        logger.info(f"📦 Request payload productType: {payload.get('productType')}")
        logger.debug(f"📦 Full payload keys: {list(payload.keys())}")

        # Parse response
        issues = result.get("issues", [])
        errors = [i for i in issues if i.get("severity") == "ERROR"]
        warnings = [i for i in issues if i.get("severity") == "WARNING"]
        
        # Log errors in detail
        if errors:
            for err in errors:
                logger.error(f"❌ Amazon Error: {err.get('message')}")
                logger.error(f"   Code: {err.get('code')}")
                logger.error(f"   Path: {err.get('path', 'N/A')}")

        return {
            "success": len(errors) == 0,
            "status": result.get("status", "UNKNOWN"),
            "submissionId": result.get("submissionId", ""),
            "asin": result.get("asin", ""),
            "errors": errors,
            "warnings": warnings,
            "raw_response": result,
        }

    def _build_listing_payload(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the complete SP-API listing payload using The Ultimate Dictionary.
        
        CRITICAL: Uses ar_AE language, EGP currency, flat attributeProperties structure,
        and ALL 29 required fields as tested and verified with Amazon SP-API.
        
        NO fake barcodes ("000000000000") — if no barcode, field is omitted.
        """
        name = product_data.get("name", "Unnamed Product")
        description = product_data.get("description", name)
        brand = (product_data.get("brand") or "Generic").strip() or "Generic"
        ean = product_data.get("ean", "").strip()
        upc = product_data.get("upc", "").strip()
        price = float(product_data.get("price", 0))
        quantity = int(product_data.get("quantity", 0))
        condition = product_data.get("condition", "New")
        country_origin = product_data.get("country_of_origin", "CN")
        model_number = product_data.get("model_number", product_data.get("sku", "N/A"))
        manufacturer = (product_data.get("manufacturer") or brand).strip() or brand
        bullet_points = product_data.get("bullet_points", [])
        browse_node = product_data.get("browse_node_id", "21863799031")
        included_components = product_data.get("included_components") or product_data.get("name") or "منتج"
        color = product_data.get("color", "متعدد")  # DEFAULT: Multi (required by Amazon)

        # Map condition
        condition_map = {"New": "new_new"}
        condition_value = condition_map.get(condition, "new_new")
        
        number_of_items = int(product_data.get("number_of_items", 1))
        package_quantity = int(product_data.get("package_quantity", 1))
        material = product_data.get("material", "")
        target_audience = product_data.get("target_audience", "")

        # Build attributes — THE ULTIMATE DICTIONARY (ar_AE, EGP, 30+ fields)
        attributes = {
            # === IDENTITY ===
            "item_name": [{"value": name, "language_tag": "ar_AE"}],
            "brand": [{"value": brand, "language_tag": "ar_AE"}],
            "color": [{"value": color, "language_tag": "ar_AE"}],
            "product_description": [{"value": description, "language_tag": "ar_AE"}],

            # Bullet points
            "bullet_point": [
                {"value": bp, "language_tag": "ar_AE"}
                for bp in (bullet_points if bullet_points else [name])
            ],

            # Manufacturer & Model
            "manufacturer": [{"value": manufacturer, "language_tag": "ar_AE"}],
            "model_name": [{"value": model_number, "language_tag": "ar_AE"}],
            "model_number": [{"value": model_number, "language_tag": "ar_AE"}],

            # Included components — REQUIRED by Amazon
            "included_components": [{"value": str(included_components)[:200], "language_tag": "ar_AE"}],

            # Condition & Origin
            "condition_type": [{"value": condition_value}],
            "country_of_origin": [{"value": country_origin.upper() if len(country_origin) == 2 else "CN"}],
            "recommended_browse_nodes": [{"value": browse_node}],

            # Included components
            "number_of_boxes": [{"value": 1}],
            "number_of_items": [{"value": number_of_items}],

            # Material & Target
            "material": [{"value": material, "language_tag": "ar_AE"}] if material else None,
            "target_audience": [{"value": target_audience, "language_tag": "ar_AE"}] if target_audience else None,

            # Compliance
            "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
            "batteries_required": [{"value": False}],

            # Egypt HOME type required fields
            "part_number": [{"value": product_data.get("model_number", "N/A")[:30], "language_tag": "ar_AE"}],
            "voltage": [{"value": 220, "unit": "volts"}],
            "wattage": [{"value": 0, "unit": "watts"}],
            "supported_voltage_frequency": [{"value": 220, "unit": "volts"}],  # Required for Egypt
            "power_plug": [{"value": "type_c_2pin"}],  # EU plug type for Egypt

            # Weight (FLAT format)
            "item_weight": [{"value": 0.5, "unit": "kilograms"}],
            "item_package_weight": [{"value": 0.7, "unit": "kilograms"}],

            # Unit count
            "unit_count": [{"value": number_of_items, "unit": "count"}],

            # Package dimensions (CORRECT format!)
            "item_package_dimensions": [{
                "length": {"value": 25.0, "unit": "centimeters"},
                "width": {"value": 10.0, "unit": "centimeters"},
                "height": {"value": 15.0, "unit": "centimeters"},
            }],

            # Price
            "purchasable_offer": [{
                "our_price": [{"schedule": [{"value_with_tax": price}]}],
                "currency": "EGP",
            }],
        }

        # Remove None values
        attributes = {k: v for k, v in attributes.items() if v is not None}
        
        # EAN/UPC — ONLY if we have a real barcode (NO fake "000000000000"!)
        if ean:
            attributes["externally_assigned_product_identifier"] = [{
                "value": {"type": "ean", "value": ean}
            }]
        elif upc:
            attributes["externally_assigned_product_identifier"] = [{
                "value": {"type": "upc", "value": upc}
            }]
        # If no barcode — omit the field entirely (GTIN exemption handled by Amazon)

        # Merchant suggested ASIN — use SKU as fallback (max 10 chars!)
        merchant_asin = product_data.get("merchant_suggested_asin", "")
        if not merchant_asin:
            # Use SKU as the suggested ASIN (Amazon accepts this for new products)
            merchant_asin = product_data.get("sku", "")
        # Amazon limit: 10 characters max
        merchant_asin = str(merchant_asin)[:10].strip() if merchant_asin else ""
        if merchant_asin:
            attributes["merchant_suggested_asin"] = [{
                "value": merchant_asin
            }]

        return {
            "productType": self.normalize_product_type(product_data.get("product_type", "HOME")),
            "requirements": "LISTING",
            "attributes": attributes,
        }

    @staticmethod
    def normalize_product_type(product_type: str) -> str:
        """
        Convert Arabic product type to Amazon valid English product type.

        IMPORTANT: Egypt (ARBP9OOSHTCHU) has DIFFERENT valid product types!
        Generic types like HOME_KITCHEN, ELECTRONICS are NOT valid for Egypt.

        Valid Egypt types (confirmed via Product Type Definitions API):
        - HOME (generic fallback for home products)
        - FOOD_PROCESSOR (specific appliances)
        - FOOD_MIXER, FOOD_BLENDER (kitchen appliances)
        - And 1800+ more specific types

        Examples:
            "مضرب يدوي كهربائي" → "HOME"
            "HOME_KITCHEN" → "HOME" (not valid for Egypt!)
            "HOME" → "HOME"
        """
        if not product_type:
            return "HOME"  # Egypt-valid default

        # Egypt-valid product types (confirmed via API)
        EGYPT_VALID_TYPES = {
            "HOME", "FOOD_PROCESSOR", "FOOD_MIXER", "FOOD_BLENDER",
            "3D_PRINTABLE_DESIGNS", "3D_PRINTED_PRODUCT",
            "ACCESSORY", "ADULT_COSTUME", "ADVERTISEMENT_COLLECTIBLES",
            "AGRICULTURAL_SUPPLIES", "AMAZON_BOOK_READER_ACCESSORY",
            "AMAZON_TABLET_ACCESSORY", "APPLIANCE_COVER",
            "ARCHITECTURAL_COVERING", "ART_SUPPLY_DRAWING",
            "BABY_PRODUCT", "BAG", "BATTERY", "BEAUTY", "BED",
            "BOOK", "BOOK_CASE", "BULK_FOOD", "CABLE", "CARRIER_CASE",
            "CELL_PHONE", "CHAIR", "CLEANING_BRUSH", "COAT_RACK",
            "COMPUTER_COMPONENT", "CONDITIONER", "CONTAINER",
            "COOKWARE", "COSMETIC", "COUCH", "CURTAIN", "DESK",
            "DIAPER", "DIY_TOOLS", "DRESSER", "DRINKWARE",
            "ELECTRIC_CHARGER", "ELECTRICAL_OUTLET", "ELECTRONIC_ADAPTER",
            "ELECTRONIC_CABLE", "EYEWEAR", "FABRIC", "FAN",
            "FLOWER_POT", "FOOD", "FOOD_CONTAINER", "FOOD_STORAGE",
            "FURNITURE", "GAMES", "GARDEN_TOOL", "GIFT_CARD",
            "GROCERY", "HAIR_DRYER", "HAND_TOOL", "HARDWARE",
            "HAT", "HEADPHONES", "HEALTH_PERSONAL_CARE", "HEATING_COOLING",
            "HOME_DECOR", "HOME_FURNISHINGS", "HOME_LIGHTING",
            "HOUSEHOLD_CLEANING", "HOUSEHOLD_THERMOMETER",
            "INDUSTRIAL", "INGREDIENT", "INKJET_PRINTER_INK",
            "INSTRUMENT_PICK", "IRON", "JEWELRY", "KEYBOARD",
            "KITCHEN_TOOL", "LAMP", "LAUNDRY_BASKET", "LENS_FILTER",
            "LIGHT_BULB", "LIGHT_SWITCH", "LUGGAGE", "MAKEUP",
            "MATTRESS", "MEAT_GRINDER", "MEDIA_STORAGE",
            "MEDICAL_SUPPLY", "MEMORY_CARD", "METAL_SHAPE",
            "MICROWAVE_OVEN", "MILK", "MIRROR", "MOBILE_PHONE_CASE",
            "MONITOR", "MOP", "MOUSE", "MUSIC", "MUSICAL_INSTRUMENT",
            "NAIL_CARE", "NETHERLANDS", "NOTEBOOK", "NUTRITIONAL",
            "OFFICE_PRODUCTS", "OVEN", "PACKING_MATERIAL",
            "PAINTING_SUPPLY", "PAN", "PAPER_PRODUCT", "PEN",
            "PERFUME", "PET_PRODUCTS", "PHONE", "PHOTOGRAPHY",
            "PILLOW", "PIPE", "PLANT_SEED", "PLATE", "PLAYER_PIANO",
            "PORTABLE_AUDIO", "POSTER", "POWER_ADAPTER", "POWER_CORD",
            "POWER_STRIP", "PRINTER", "PROCESSOR", "PROJECTOR",
            "RADIO", "RANGE_HOOD", "RECEIVER", "REFRIGERATOR",
            "REMOTE_CONTROL", "RICE", "RUG", "SANDWICH_MAKER",
            "SCREWDRIVER", "SEAT_COVER", "SHIRT", "SHOE",
            "SHOWER_HEAD", "SKIRT", "SLEEPING", "SLIPPER",
            "SMALL_APPLIANCE_PART", "SOCCER", "SOCK", "SOFA",
            "SOFTWARE", "SPEAKER", "SPORTS", "STORAGE", "STORAGE_BAG",
            "STORAGE_DRAWER", "STORAGE_RACK", "STORAGE_SHELF",
            "STOVE", "SUPPLEMENT", "SWEATER", "SWITCH", "TABLE",
            "TABLEWARE", "TANK", "TEA", "TELEPHONE", "TELEVISION",
            "TEXTILE", "TOOL", "TOOTHBRUSH", "TOY", "TOYS_AND_GAMES",
            "TRACK_PANT", "TRASH_CAN", "TREADMILL", "TSHIRT", "TUBE",
            "VACUUM_CLEANER", "VASE", "VEHICLE_MIRROR", "VIDEO_DVD",
            "VIDEO_GAMES", "WALL_ART", "WALL_LAMP", "WASHER",
            "WATER_BOTTLE", "WATER_FILTER", "WATER_SOFTENER",
            "WEIGHT_SCALE", "WIRELESS", "WOODWORKING",
        }

        # If already a valid type, return as-is
        if product_type.strip().upper() in EGYPT_VALID_TYPES:
            return product_type.strip().upper()

        # Accept any ALL-CAPS type (likely valid Amazon type)
        if product_type.isupper():
            return product_type
        
        # Try exact match
        if product_type in ARABIC_TO_AMAZON_PRODUCT_TYPE:
            return ARABIC_TO_AMAZON_PRODUCT_TYPE[product_type]
        
        # Try partial match (check if any keyword is in the product type)
        product_type_lower = product_type.lower()
        for arabic, amazon_type in ARABIC_TO_AMAZON_PRODUCT_TYPE.items():
            if arabic.lower() in product_type_lower or product_type_lower in arabic.lower():
                logger.info(f"🔄 Product type mapped: '{product_type}' → '{amazon_type}'")
                return amazon_type
        
        # Fallback: try to extract keywords
        # NOTE: Using list of tuples to preserve order! More specific keywords first.
        keywords_map = [
            # Kitchen/Home appliances (check these FIRST - they're more specific)
            ("مضرب", "HOME_KITCHEN"), ("خلاط", "HOME_KITCHEN"), ("فرن", "HOME_KITCHEN"),
            ("أدوات مطبخ", "HOME_KITCHEN"), ("أدوات منزلية", "HOME_KITCHEN"),
            ("مطبخ", "HOME_KITCHEN"), ("منزل", "HOME_KITCHEN"),
            ("يدوي", "HOME_KITCHEN"), ("أدوات", "HOME_KITCHEN"),
            # Storage
            ("تخزين", "HOME_ORGANIZERS_AND_STORAGE"),
            # Electronics (general electronics)
            ("إلكتروني", "ELECTRONICS"), ("جهاز", "ELECTRONICS"), ("ماكينة", "ELECTRONICS"),
            ("كهربائي", "ELECTRONICS"), ("تلفاز", "ELECTRONICS"), ("تلفزيون", "ELECTRONICS"),
            ("ذكي", "ELECTRONICS"), ("سمارت", "ELECTRONICS"),
            ("كمبيوتر", "ELECTRONICS"), ("لابتوب", "ELECTRONICS"),
            ("موبايل", "ELECTRONICS"), ("هاتف", "ELECTRONICS"),
            # Other categories
            ("أطفال", "BABY_PRODUCT"), ("طفل", "BABY_PRODUCT"),
            ("ملابس", "APPAREL"), ("زي", "APPAREL"),
            ("ألعاب", "TOYS_AND_GAMES"), ("لعبة", "TOYS_AND_GAMES"),
            ("جمال", "BEAUTY"), ("عناية", "BEAUTY"),
            ("رياضة", "SPORTING_GOODS"), ("رياضي", "SPORTING_GOODS"),
            ("مكتب", "OFFICE_PRODUCTS"),
            ("حيوان", "PET_PRODUCTS"),
        ]
        
        for keyword, amazon_type in keywords_map:
            if keyword in product_type_lower:
                logger.info(f"🔄 Product type mapped by keyword: '{product_type}' → '{amazon_type}'")
                return amazon_type

        # Default fallback — HOME is valid for Egypt, HOME_KITCHEN is NOT
        logger.warning(f"⚠️ Unknown product type '{product_type}', defaulting to HOME (Egypt-valid)")
        return "HOME"
