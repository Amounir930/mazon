"""
Test SP-API — Correct payload format based on official docs
"""
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient

def main():
    print("=" * 60)
    print("SP-API Test — Correct Payload Format (per official docs)")
    print("=" * 60)
    
    client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU", country_code="eg")
    
    # Step 1: Get token
    print("\n1. Getting LWA token...")
    token = client._get_access_token()
    print(f"   ✅ Token: {token[:30]}...")
    
    # Step 2: Get seller info
    print("\n2. Getting seller info...")
    result = client.get_marketplace_participations()
    participations = result.get("payload", [])
    if not participations:
        print("❌ No participations")
        return
    marketplace = participations[0].get("marketplace", {})
    marketplace_id = marketplace.get("id", "")
    store_name = participations[0].get("storeName", "N/A")
    print(f"   ✅ Store: {store_name}")
    print(f"   ✅ Marketplace: {marketplace.get('name')} ({marketplace_id})")
    
    # The seller ID for the URL path — using marketplace_id since that's what we have
    seller_id = marketplace_id
    print(f"   ✅ Using seller_id: {seller_id}")
    
    # Step 3: Create listing with EXACT official format
    print("\n3. Creating test listing...")
    
    test_sku = "SPAPI-TEST-V3"
    
    # CORRECT format per official SP-API docs:
    # https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference
    sp_payload = {
        "productType": "HOME_ORGANIZERS_AND_STORAGE",
        "requirements": "LISTING",
        "attributes": {
            # String attributes — value + language_tag
            "item_name": [
                {"value": "Professional Electric Hand Mixer - 5 Speed Settings", "language_tag": "en_US"}
            ],
            "brand": [
                {"value": "Generic", "language_tag": "en_US"}
            ],
            "product_description": [
                {"value": "Professional hand mixer with 5 speeds and turbo boost function. Perfect for baking and cooking.", "language_tag": "en_US"}
            ],
            "bullet_point": [
                {"value": "5-speed settings with turbo boost for versatile mixing", "language_tag": "en_US"},
                {"value": "Stainless steel beaters included for durability", "language_tag": "en_US"},
                {"value": "250W powerful motor handles thick dough", "language_tag": "en_US"},
            ],
            "manufacturer": [
                {"value": "Generic", "language_tag": "en_US"}
            ],
            "model_name": [
                {"value": "HM-250W", "language_tag": "en_US"}
            ],
            
            # Enum attributes — just value
            "externally_assigned_product_identifier": [
                {"value": "5012345678901"}
            ],
            "condition_type": [
                {"value": "new_new"}
            ],
            "country_of_origin": [
                {"value": "CN"}
            ],
            "recommended_browse_nodes": [
                {"value": "21863799031"}
            ],
            
            # Integer attributes
            "fulfillment_availability": [
                {"value": 25}
            ],
            
            # Complex: purchasable_offer includes fulfillment_channel INSIDE it
            "purchasable_offer": [
                {
                    "our_price": [
                        {"schedule": [{"value_with_tax": 350.0}]}
                    ],
                    "currency": "EGP",
                    "fulfillment_channel": "MFN"
                }
            ],
            
            # SKU
            "item_sku": [
                {"value": test_sku}
            ],
        }
    }
    
    print(f"   Payload productType: {sp_payload['productType']}")
    print(f"   Payload requirements: {sp_payload['requirements']}")
    print(f"   Payload attributes ({len(sp_payload['attributes'])} keys):")
    for key in sp_payload['attributes']:
        val = sp_payload['attributes'][key]
        print(f"     - {key}: {json.dumps(val, ensure_ascii=False)[:80]}")
    
    try:
        result = client.put_listing_item(seller_id, test_sku, sp_payload)
        print(f"\n📊 Full Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
        
        # Check success
        issues = result.get("issues", [])
        status = result.get("status", "N/A")
        
        if not issues:
            print(f"\n✅✅✅ SUCCESS! Status: {status}")
        else:
            print(f"\n⚠️ Issues ({len(issues)}):")
            for issue in issues[:10]:
                print(f"   - [{issue.get('severity', 'N/A')}] {issue.get('code')}: {issue.get('message', '')[:100]}")
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
