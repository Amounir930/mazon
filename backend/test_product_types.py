"""
Test: Discover valid product types for Egypt marketplace (ARBP9OOSHTCHU)
========================================================================
Use the Product Type Definitions API to find what Amazon accepts.
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
print("🔍 Discovering valid product types for Egypt (ARBP9OOSHTCHU)")
print("=" * 80)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')

# Test common product types
product_types_to_test = [
    "HOME_KITCHEN",
    "HOME_ORGANIZERS_AND_STORAGE",
    "ELECTRONICS",
    "BABY_PRODUCT",
    "APPAREL",
    "TOYS_AND_GAMES",
    "BEAUTY",
    "SPORTING_GOODS",
    "OFFICE_PRODUCTS",
    "PET_PRODUCTS",
    "LUGGAGE",
    "FURNITURE",
    "GROCERY",
    "HEALTH_PERSONAL_CARE",
    "PRODUCT",  # Universal fallback?
]

print(f"\n🔄 Testing {len(product_types_to_test)} product types...\n")

results = {}

for pt in product_types_to_test:
    try:
        # Try to get product type definition
        path = f"/definitions/2020-09-01/productTypes/{pt}"
        params = {
            "marketplaceIds": "ARBP9OOSHTCHU",
            "requirements": "LISTING",
            "requirementsEnforced": "ENFORCED",
        }
        
        result = client._make_request("GET", path, params=params)
        
        if "errors" in result:
            errors = result.get("errors", [])
            error_msg = errors[0].get("message", "Unknown") if errors else "Unknown"
            results[pt] = f"❌ {error_msg}"
            print(f"  ❌ {pt}: {error_msg[:80]}")
        else:
            results[pt] = "✅ VALID"
            print(f"  ✅ {pt}: ACCEPTED")
            
    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "Not Found" in error_str:
            results[pt] = "❌ Not Found (404)"
            print(f"  ❌ {pt}: Not Found")
        elif "400" in error_str or "Invalid" in error_str:
            results[pt] = "❌ Invalid"
            print(f"  ❌ {pt}: Invalid")
        else:
            results[pt] = f"⚠️ Error: {error_str[:50]}"
            print(f"  ⚠️ {pt}: {error_str[:80]}")

print("\n" + "=" * 80)
print("📊 SUMMARY:")
print("=" * 80)

valid = [pt for pt, status in results.items() if "✅" in status]
invalid = [pt for pt, status in results.items() if "❌" in status]

print(f"\n✅ Valid ({len(valid)}): {valid if valid else 'NONE'}")
print(f"\n❌ Invalid ({len(invalid)}): {invalid if invalid else 'NONE'}")

if not valid:
    print("\n💡 RECOMMENDATION:")
    print("   Try using the Product Type Definitions API to list ALL available types:")
    print("   GET /definitions/2020-09-01/productTypes?marketplaceIds=ARBP9OOSHTCHU")

print("\n" + "=" * 80)
