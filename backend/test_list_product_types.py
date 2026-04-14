"""
Test: List ALL available product types for Egypt marketplace
=============================================================
Use the Product Type Definitions API to enumerate valid types.
"""
import os
import sys
import json
from pathlib import Path

# Load .env
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

from app.services.sp_api_client import SPAPIClient

print("=" * 80)
print("📋 Listing ALL available product types for Egypt (ARBP9OOSHTCHU)")
print("=" * 80)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')

# Method 1: List all product types
print("\n🔄 Method 1: GET /definitions/2020-09-01/productTypes")
try:
    path = "/definitions/2020-09-01/productTypes"
    params = {"marketplaceIds": "ARBP9OOSHTCHU"}
    
    result = client._make_request("GET", path, params=params)
    
    if "errors" in result:
        print(f"  ❌ Error: {json.dumps(result['errors'], indent=2)}")
    else:
        product_types = result.get("productTypes", [])
        print(f"  ✅ Found {len(product_types)} product types:")
        for pt in product_types[:50]:  # Show first 50
            print(f"    - {pt.get('productType', 'N/A')} ({pt.get('displayName', 'N/A')})")
        if len(product_types) > 50:
            print(f"    ... and {len(product_types) - 50} more")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Method 2: Test a simple listing with HOME_KITCHEN and check detailed errors
print("\n\n🔄 Method 2: Submit minimal listing with HOME_KITCHEN and check detailed errors")

seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")
sku = f"TEST-MINIMAL-{os.getpid()}"

# Minimal payload with only required fields
attributes = {
    "item_name": [{"value": "Test Product", "language_tag": "ar_AE"}],
    "brand": [{"value": "Generic", "language_tag": "ar_AE"}],
    "product_description": [{"value": "Test description for validation", "language_tag": "ar_AE"}],
    "bullet_point": [{"value": "Test bullet point one for validation purposes", "language_tag": "ar_AE"}],
    "manufacturer": [{"value": "Generic", "language_tag": "ar_AE"}],
    "model_name": [{"value": "TEST", "language_tag": "ar_AE"}],
    "model_number": [{"value": "TEST-001", "language_tag": "ar_AE"}],
    "condition_type": [{"value": "new_new"}],
    "country_of_origin": [{"value": "CN"}],
    "recommended_browse_nodes": [{"value": "21863799031"}],
    "included_components": [{"value": "Test Product", "language_tag": "ar_AE"}],
    "number_of_boxes": [{"value": 1}],
    "number_of_items": [{"value": 1}],
    "package_quantity": [{"value": 1}],
    "supplier_declared_dg_hz_regulation": [{"value": "not_applicable"}],
    "batteries_required": [{"value": False}],
    "safety_warning": [{"value": "No warning", "language_tag": "ar_AE"}],
    "item_weight": [{"value": 0.5, "unit": "kilograms"}],
    "item_package_weight": [{"value": 0.7, "unit": "kilograms"}],
    "unit_count": [{"value": 1, "unit": "count"}],
    "item_package_dimensions": [{
        "length": {"value": 25.0, "unit": "centimeters"},
        "width": {"value": 10.0, "unit": "centimeters"},
        "height": {"value": 15.0, "unit": "centimeters"},
    }],
    "purchasable_offer": [{
        "our_price": [{"schedule": [{"value_with_tax": 100.0}]}],
        "currency": "EGP",
    }],
    "externally_assigned_product_identifier": [{
        "value": {"type": "ean", "value": "6281234567890"}
    }],
}

payload = {
    "productType": "HOME_KITCHEN",
    "requirements": "LISTING",
    "attributes": attributes,
}

try:
    result = client.put_listing_item(seller_id, sku, payload)
    print(f"\n  Response Status: {result.get('status', 'UNKNOWN')}")
    
    issues = result.get("issues", [])
    errors = [i for i in issues if i.get("severity") == "ERROR"]
    
    if errors:
        print(f"\n  ❌ ERRORS ({len(errors)}):")
        for err in errors:
            print(f"    Code: {err.get('code')}")
            print(f"    Message: {err.get('message')}")
            print(f"    Path: {err.get('path', 'N/A')}")
            print(f"    ---")
    else:
        print(f"\n  ✅ No errors!")
        print(f"  Full response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
        
except Exception as e:
    print(f"\n  ❌ Exception: {e}")

print("\n" + "=" * 80)
