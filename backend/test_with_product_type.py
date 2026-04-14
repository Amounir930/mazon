"""
Test: Submit listing WITH product_type to Amazon SP-API
============================================================
Verify that adding productType makes the request succeed.
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
print("🧪 Test: Submit listing WITH product_type")
print("=" * 80)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
seller_id = os.getenv("SP_API_SELLER_ID", "A1DSHARRBRWYZW")
sku = f"TEST-WITH-TYPE-{os.getpid()}"

# Use the normal _build_listing_payload which includes productType
product_data = {
    "sku": sku,
    "name": "Test Product With Type",
    "name_ar": "منتج اختبار بالنوع",
    "description": "This is a test product with product_type",
    "price": 150.0,
    "quantity": 5,
    "brand": "Generic",
    "ean": "6289876543210",
    "condition": "New",
    "product_type": "HOME_KITCHEN",  # ← WITH product_type!
    "fulfillment_channel": "MFN",
    "country_of_origin": "CN",
    "model_number": "TEST-001",
    "manufacturer": "Generic",
    "bullet_points": ["نقطة بيعية أولى كاملة وواضحة", "نقطة ثانية مهمة", "نقطة ثالثة مفيدة", "نقطة رابعة رائعة", "نقطة خامسة ممتازة"],
    "browse_node_id": "21863799031",
    "included_components": "منتج اختبار",
    "number_of_items": 1,
    "package_quantity": 1,
}

print(f"\n📦 SKU: {sku}")
print(f"📦 Seller: {seller_id}")
print(f"📦 product_type: {product_data['product_type']}")
print(f"\n🔄 Sending to Amazon...")

try:
    result = client.create_listing_from_product(seller_id, sku, product_data)
    print(f"\n📊 Success: {result.get('success')}")
    print(f"📊 Status: {result.get('status')}")
    print(f"📊 ASIN: {result.get('asin')}")
    
    if result.get('errors'):
        print(f"\n❌ ERRORS ({len(result['errors'])}):")
        for err in result['errors']:
            print(f"  Code: {err.get('code')}")
            print(f"  Message: {err.get('message')}")
            print(f"  Path: {err.get('path', 'N/A')}")
    else:
        print(f"\n✅ No errors!")
        
    if result.get('warnings'):
        print(f"\n⚠️ WARNINGS ({len(result['warnings'])}):")
        for warn in result['warnings']:
            print(f"  Message: {warn.get('message')}")
            
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
