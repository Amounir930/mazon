"""
ABIS Client — Phase 6: Build payload from Amazon's own template
Instead of GETting template (which returns 403), we build it ourselves
using the exact structure from Amazon's template (temp.txt).
"""
import json
from typing import Dict, Any, Optional, List
from loguru import logger

from app.services.amazon_http_client import AmazonHTTPClient, SessionExpiredError, AMAZON_USER_AGENT

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}


class ABISClient:
    """Clone & Inject pattern — builds payload from Amazon template."""

    def __init__(self, cookies: List[Dict[str, Any]], country_code: str = "eg"):
        self.country_code = country_code.lower()
        self.base_url = SELLER_CENTRAL_BASE.get(self.country_code, SELLER_CENTRAL_BASE["eg"])
        self.cookies = cookies
        self.csrf_token: Optional[str] = None
        self._client: Optional[AmazonHTTPClient] = None

    def _get_client(self) -> AmazonHTTPClient:
        if self._client is None:
            self._client = AmazonHTTPClient(self.cookies, self.country_code)
        return self._client

    def fetch_csrf_from_page(self) -> Optional[str]:
        client = self._get_client()
        urls = [
            f"{self.base_url}/product-search/search",
            f"{self.base_url}/home",
        ]
        for url in urls:
            try:
                logger.info(f"Fetching CSRF from: {url}")
                response = client.session.get(url, allow_redirects=True, timeout=15)
                if response.status_code == 200:
                    token = client.extract_csrf_from_response(response.text)
                    if token:
                        self.csrf_token = token
                        logger.info(f"CSRF fetched: {token[:20]}... ({len(token)} chars)")
                        return token
            except SessionExpiredError:
                raise
            except Exception as e:
                logger.debug(f"CSRF fetch failed from {url}: {e}")
        logger.error("Failed to fetch CSRF token!")
        return None

    def _build_full_payload(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the COMPLETE listing payload matching Amazon's template exactly."""
        
        name = product_data.get("name", "Unknown Product")
        description = product_data.get("description", name)
        brand = (product_data.get("brand") or "Generic").strip() or "Generic"
        ean = product_data.get("ean", "")
        sku = product_data.get("sku", "")
        price = float(product_data.get("price", 0))
        quantity = int(product_data.get("quantity", 0))
        condition = product_data.get("condition", "New")
        fulfillment = product_data.get("fulfillment_channel", "MFN")
        country_origin = product_data.get("country_of_origin", "CN")
        model_name = product_data.get("model_number", sku)
        manufacturer = (product_data.get("manufacturer") or brand).strip() or brand
        bullet_points = product_data.get("bullet_points", [])
        
        # Map condition to Amazon values
        condition_map = {"New": "new_new", "Used": "used_used", "Refurbished": "refurbished_refurbished"}
        condition_value = condition_map.get(condition, "new_new")
        
        # Map fulfillment
        fulfillment_value = "MFN" if fulfillment == "MFN" else "AFN"
        
        # Build the payload matching Amazon's attributePropertiesImsV3 structure
        attribute_properties = {}
        
        # === IDENTITY ===
        attribute_properties["item_name"] = [{
            "language_tag": "en_US",
            "value": name,
        }]
        
        attribute_properties["product_type"] = [{
            "value": "HOME_ORGANIZERS_AND_STORAGE",
        }]
        
        # Browse node - use default for HOME_ORGANIZERS_AND_STORAGE
        attribute_properties["recommended_browse_nodes"] = [{
            "value": "21863799031",  # المنزل والمطبخ > التخزين والتنظيم المنزلي
        }]
        
        attribute_properties["brand"] = [{
            "language_tag": "en_US",
            "value": brand,
        }]
        
        # External product ID (EAN/UPC/GTIN)
        if ean:
            attribute_properties["externally_assigned_product_identifier"] = [{
                "type": "upc/ean/gtin",
                "value": str(ean),
            }]
        
        attribute_properties["product_description"] = [{
            "language_tag": "en_US",
            "value": description,
        }]
        
        # Bullet points - at least one required
        if bullet_points and isinstance(bullet_points, list) and len(bullet_points) > 0:
            attribute_properties["bullet_point"] = [{
                "language_tag": "en_US",
                "value": str(bullet_points[0]),
            }]
        else:
            attribute_properties["bullet_point"] = [{
                "language_tag": "en_US",
                "value": name,
            }]
        
        attribute_properties["model_name"] = [{
            "language_tag": "en_US",
            "value": model_name,
        }]
        
        attribute_properties["manufacturer"] = [{
            "language_tag": "en_US",
            "value": manufacturer,
        }]
        
        attribute_properties["unit_count"] = [{
            "type": {"language_tag": "en_US", "value": "العد"},
            "value": 1.0,
        }]
        
        attribute_properties["included_components"] = [{
            "language_tag": "en_US",
            "value": name,
        }]
        
        # === OFFER ===
        attribute_properties["fulfillment_availability"] = [{
            "quantity": quantity,
        }]
        
        attribute_properties["purchasable_offer"] = [{
            "our_price": [{
                "schedule": [{
                    "value_with_tax": price,
                }]
            }],
            "maximum_retail_price": [{
                "schedule": [{
                    "value_with_tax": price,
                }]
            }],
            "currency": "EGP",
        }]
        
        attribute_properties["condition_type"] = [{
            "value": condition_value,
        }]
        
        attribute_properties["automated_pricing_rule_type"] = [{
            "value": "disabled",
        }]
        
        attribute_properties["offerFulfillment"] = fulfillment_value
        
        attribute_properties["country_of_origin"] = [{
            "value": country_origin.upper() if len(country_origin) == 2 else "CN",
        }]
        
        attribute_properties["supplier_declared_dg_hz_regulation"] = [{
            "value": "not_applicable",
        }]
        
        # Build the full listing structure
        payload = {
            "listing": {
                "listingDetails": {
                    "attributePropertiesImsV3": json.dumps(attribute_properties, ensure_ascii=False),
                    "listingLanguageCode": "en_US",
                    "marketplaceId": self._get_marketplace_id(),
                    "sku": sku,
                    "productType": "HOME_ORGANIZERS_AND_STORAGE",
                },
                "metadata": {
                    "menus": [{"attributeGroups": []}],
                    "metadataNamespace": "UMP",
                },
                "offerOnly": {},
            },
        }
        
        return payload

    def create_listing(self, product_data: Dict[str, Any], csrf_token: Optional[str] = None) -> Dict[str, Any]:
        """Create listing with full payload built from template."""
        token = csrf_token or self.csrf_token
        if not token:
            logger.error("No CSRF token! Fetching...")
            token = self.fetch_csrf_from_page()
            if not token:
                return {"success": False, "error": "Missing CSRF Token", "session_expired": False}

        client = self._get_client()
        url = f"{self.base_url}/abis/ajax/create-listing"

        # Build the complete payload
        payload = self._build_full_payload(product_data)
        
        # Log the full payload for debugging
        logger.info(f"Full payload size: {len(json.dumps(payload))} chars")
        logger.info(f"Attribute properties keys: {list(json.loads(payload['listing']['listingDetails']['attributePropertiesImsV3']).keys())}")

        form_data = {
            "data": json.dumps(payload, ensure_ascii=False),
        }
        if token:
            form_data["anti-csrftoken-a2z"] = token

        headers = {
            "User-Agent": AMAZON_USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/product-search/search",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        if token:
            headers["anti-csrftoken-a2z"] = token
            headers["x-csrf-token"] = token

        logger.info(f"POST {url}")
        logger.info(f"  CSRF: {token[:20]}... ({len(token)} chars)")
        logger.info(f"  Cookies: {len([c for c in self.cookies if c.get('name') and c.get('value') is not None])}")

        try:
            response = client.session.post(url, data=form_data, headers=headers, timeout=30)
            logger.info(f"  Response status: {response.status_code}")

            if response.status_code == 403:
                logger.error(f"  403 Body: {response.text[:1500]}")
                try:
                    logger.error(f"  403 JSON: {json.dumps(response.json(), indent=2)}")
                except:
                    pass
                return {"success": False, "status": "403_FORBIDDEN", "error": f"403: {response.text[:200]}"}

            if "/ap/signin" in str(response.url):
                return {"success": False, "status": "SESSION_EXPIRED", "error": "Session expired"}

            try:
                result = response.json()
                if response.status_code >= 400 or result.get("status") != "SUCCESS":
                    logger.error(f"JSON Response (status {response.status_code}):")
                    logger.error(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
            except Exception:
                if "<html" in response.text[:200].lower():
                    return {"success": False, "status": "HTML_RESPONSE", "error": "HTML response"}
                result = {"raw": response.text[:500]}

            if result.get("status") == "SUCCESS":
                logger.info(f"SUCCESS! listing_id={result.get('listingId')}, asin={result.get('asin')}")
                return {
                    "success": True, "status": "SUCCESS",
                    "listing_id": result.get("listingId", ""),
                    "asin": result.get("asin", ""),
                }
            else:
                return {
                    "success": False,
                    "status": result.get("status", "ERROR"),
                    "error": result.get("message", result.get("error", "Unknown")),
                    "response": result,
                }

        except SessionExpiredError:
            return {"success": False, "status": "SESSION_EXPIRED", "error": "Session expired"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {"success": False, "status": "UNEXPECTED_ERROR", "error": str(e)}

    def _get_marketplace_id(self) -> str:
        ids = {"eg": "ARBP9OOSHTCHU", "sa": "A17E79C6D8DWNP", "ae": "A2VIGQ35RCS4UG"}
        return ids.get(self.country_code, "ARBP9OOSHTCHU")

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
