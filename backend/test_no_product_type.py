"""
Test: Submit listing WITHOUT product_type to Amazon SP-API
============================================================
What error does Amazon return when product_type is missing?
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
print("🧪 Test: Submit listing WITHOUT product_type")
print("=" * 80)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")
sku = f"TEST-NO-TYPE-{os.getpid()}"

# Build payload WITHOUT product_type
product_data = {
    "sku": sku,
    "name": "Test Product - No Type",
    "description": "This is a test product without product_type",
    "price": 100.0,
    "quantity": 10,
    "brand": "Generic",
    "ean": "6281234567890",
    "condition": "New",
    # NO product_type!
}

# Build raw SP-API payload (skip _build_listing_payload which adds productType)
attributes = {
    "item_name": [{"value": product_data["name"], "language_tag": "ar_AE"}],
    "brand": [{"value": product_data["brand"], "language_tag": "ar_AE"}],
    "product_description": [{"value": product_data["description"], "language_tag": "ar_AE"}],
    "bullet_point": [{"value": product_data["name"], "language_tag": "ar_AE"}],
    "manufacturer": [{"value": product_data["brand"], "language_tag": "ar_AE"}],
    "model_name": [{"value": "TEST", "language_tag": "ar_AE"}],
    "model_number": [{"value": "TEST", "language_tag": "ar_AE"}],
    "condition_type": [{"value": "new_new"}],
    "country_of_origin": [{"value": "CN"}],
    "recommended_browse_nodes": [{"value": "21863799031"}],
    "included_components": [{"value": product_data["name"], "language_tag": "ar_AE"}],
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
        "our_price": [{"schedule": [{"value_with_tax": product_data["price"]}]}],
        "currency": "EGP",
    }],
    "externally_assigned_product_identifier": [{
        "value": {"type": "ean", "value": product_data["ean"]}
    }],
}

# Payload WITHOUT productType!
payload = {
    "requirements": "LISTING",
    "attributes": attributes,
    # NO productType field!
}

print(f"\n📦 SKU: {sku}")
print(f"📦 Seller: {seller_id}")
print(f"📦 Payload keys: {list(payload.keys())}")
print(f"📦 productType present: {'productType' in payload}")
print(f"\n🔄 Sending to Amazon...")

try:
    result = client.put_listing_item(seller_id, sku, payload)
    print(f"\n📊 Response Status: {result.get('status', 'UNKNOWN')}")
    print(f"\n📊 Full Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    issues = result.get("issues", [])
    errors = [i for i in issues if i.get("severity") == "ERROR"]
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  Code: {err.get('code')}")
            print(f"  Message: {err.get('message')}")
            print(f"  Path: {err.get('path', 'N/A')}")
            print(f"  Severity: {err.get('severity')}")
            print(f"  ---")
    else:
        print(f"\n✅ No errors returned!")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
