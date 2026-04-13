"""
Test SP-API — Full flow: Get Seller ID + Get Schema + Create Listing
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient

def main():
    print("=" * 60)
    print("SP-API Full Test — Schema + Create Listing")
    print("=" * 60)
    
    client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU", country_code="eg")
    
    # Step 1: Get Seller ID
    print("\n" + "=" * 60)
    print("STEP 1: Getting Seller ID")
    print("=" * 60)
    try:
        result = client.get_marketplace_participations()
        participations = result.get("payload", [])
        if participations:
            marketplace = participations[0].get("marketplace", {})
            store_name = participations[0].get("storeName", "N/A")
            marketplace_id = marketplace.get("id", "")
            print(f"✅ Store: {store_name}")
            print(f"✅ Marketplace: {marketplace.get('name')} ({marketplace_id})")
            print(f"✅ Country: {marketplace.get('countryCode')}")
        else:
            print("❌ No participations found")
            return
    except Exception as e:
        print(f"❌ Failed: {e}")
        return
    
    # Step 2: Get product type schema
    print("\n" + "=" * 60)
    print("STEP 2: Getting product type schema")
    print("=" * 60)
    try:
        schema_result = client.get_product_type_definitions("HOME_ORGANIZERS_AND_STORAGE")
        
        # Extract required attributes
        requirements = schema_result.get("requirements", {})
        listing_reqs = requirements.get("LISTING", {})
        
        required_attrs = []
        for attr_name, attr_info in listing_reqs.items():
            if attr_info.get("required", False):
                required_attrs.append(attr_name)
        
        print(f"✅ Schema received")
        print(f"📋 Required attributes for LISTING ({len(required_attrs)}):")
        for attr in required_attrs[:20]:
            print(f"   - {attr}")
        if len(required_attrs) > 20:
            print(f"   ... and {len(required_attrs) - 20} more")
    except Exception as e:
        print(f"⚠️ Schema fetch failed (non-fatal): {e}")
    
    # Step 3: Create listing with CORRECT SP-API format
    print("\n" + "=" * 60)
    print("STEP 3: Creating test listing")
    print("=" * 60)
    
    test_sku = "SPAPI-TEST-003"
    
    # Build payload in CORRECT SP-API Listings Items format
    # Based on official SP-API docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference
    sp_payload = {
        "productType": "HOME_ORGANIZERS_AND_STORAGE",
        "attributes": {
            "item_name": [
                {"language_tag": "en_US", "value": "Professional Electric Hand Mixer - 5 Speed Settings"}
            ],
            "brand": [
                {"language_tag": "en_US", "value": "Generic"}
            ],
            "product_description": [
                {"language_tag": "en_US", "value": "Professional hand mixer with 5 speeds and turbo boost function. Perfect for baking and cooking."}
            ],
            "bullet_point": [
                {"language_tag": "en_US", "value": "5-speed settings with turbo boost for versatile mixing"},
                {"language_tag": "en_US", "value": "Stainless steel beaters included for durability"},
                {"language_tag": "en_US", "value": "250W powerful motor handles thick dough"},
            ],
            "externally_assigned_product_identifier": [
                {"type": "ean", "value": "5012345678901"}
            ],
            "purchasable_offer": [
                {
                    "our_price": [
                        {"schedule": [{"value_with_tax": 350.0}]}
                    ],
                    "currency": "EGP",
                    "fulfillment_channel": "MFN"
                }
            ],
            "fulfillment_availability": [
                {"quantity": 25}
            ],
            "condition_type": [
                {"value": "new_new"}
            ],
            "manufacturer": [
                {"language_tag": "en_US", "value": "Generic"}
            ],
            "model_name": [
                {"language_tag": "en_US", "value": "HM-250W"}
            ],
            "country_of_origin": [
                {"value": "CN"}
            ],
            "item_sku": [
                {"value": test_sku}
            ],
            "recommended_browse_nodes": [
                {"value": "21863799031"}
            ],
        }
    }
    
    print(f"Payload keys: {list(sp_payload.keys())}")
    print(f"Attribute keys: {list(sp_payload['attributes'].keys())}")
    
    # Use marketplace_id as seller_id (since that's what we have)
    seller_id = marketplace_id
    
    try:
        result = client.put_listing_item(seller_id, test_sku, sp_payload)
        print(f"\n📊 Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
        
        # Check for success
        issues = result.get("issues", [])
        status = result.get("status", "N/A")
        
        if not issues or all(i.get("severity") != "ERROR" for i in issues):
            print(f"\n✅✅✅ LISTING CREATED! Status: {status}")
        else:
            print(f"\n⚠️ Issues found:")
            for issue in issues[:5]:
                print(f"   - [{issue.get('severity')}] {issue.get('message', issue.get('code'))}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
