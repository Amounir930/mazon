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

import requests
from requests_auth_aws_sigv4 import AWSSigV4
from loguru import logger

from app.config import Settings


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
            logger.error(f"LWA token refresh failed: {response.status_code} — {response.text[:200]}")
            raise Exception(f"LWA token refresh failed: {response.text[:200]}")
        
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
            "issueLocale": "en_US",
        }
        
        logger.info(f"Putting listing item: SKU={sku}, Seller={seller_id}")
        logger.debug(f"Product data keys: {list(product_data.keys())}")
        
        return self._make_request("PUT", path, data=product_data, params=params)

    def get_listing_item(self, seller_id: str, sku: str) -> Dict[str, Any]:
        """
        Get a listing item.
        
        API: GET /listings/2021-08-01/items/{sellerId}/{sku}
        """
        path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "issueLocale": "en_US",
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
    # Helper: Build product data from our format to SP-API format
    # ============================================================

    @staticmethod
    def build_product_payload(product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert our internal product format to SP-API Listings Items format.
        
        SP-API expects attributes in a specific nested structure.
        """
        # Build the attributes object
        attributes = {}
        
        # Identity
        if product_data.get("name"):
            attributes["item_name"] = [{"language_tag": "en_US", "value": product_data["name"]}]
        
        if product_data.get("brand"):
            attributes["brand"] = [{"language_tag": "en_US", "value": product_data["brand"]}]
        
        if product_data.get("description"):
            attributes["product_description"] = [{"language_tag": "en_US", "value": product_data["description"]}]
        
        if product_data.get("bullet_points"):
            attributes["bullet_point"] = [
                {"language_tag": "en_US", "value": bp} for bp in product_data["bullet_points"]
            ]
        
        # EAN/UPC
        if product_data.get("ean"):
            attributes["externally_assigned_product_identifier"] = [{
                "type": "ean",
                "value": product_data["ean"],
            }]
        elif product_data.get("upc"):
            attributes["externally_assigned_product_identifier"] = [{
                "type": "upc",
                "value": product_data["upc"],
            }]
        
        # Pricing
        if product_data.get("price"):
            attributes["purchasable_offer"] = [{
                "our_price": [{
                    "schedule": [{"value_with_tax": float(product_data["price"])}],
                }],
                "currency": "EGP",
            }]
        
        # Quantity
        if product_data.get("quantity") is not None:
            attributes["fulfillment_availability"] = [{
                "quantity": int(product_data["quantity"]),
            }]
        
        # Condition
        if product_data.get("condition"):
            condition_map = {"New": "new_new"}
            attributes["condition_type"] = [{"value": condition_map.get(product_data["condition"], "new_new")}]
        
        # Fulfillment
        if product_data.get("fulfillment_channel"):
            attributes["fulfillment_channel"] = product_data["fulfillment_channel"]
        
        # Manufacturer
        if product_data.get("manufacturer"):
            attributes["manufacturer"] = [{"language_tag": "en_US", "value": product_data["manufacturer"]}]
        
        # Model
        if product_data.get("model_number"):
            attributes["model_name"] = [{"language_tag": "en_US", "value": product_data["model_number"]}]
        
        # Country of origin
        if product_data.get("country_of_origin"):
            attributes["country_of_origin"] = [{"value": product_data["country_of_origin"]}]
        
        # Browse node
        if product_data.get("browse_node_id"):
            attributes["recommended_browse_nodes"] = [{"value": product_data["browse_node_id"]}]
        
        return {
            "productType": product_data.get("product_type", "HOME_ORGANIZERS_AND_STORAGE"),
            "attributes": attributes,
        }
