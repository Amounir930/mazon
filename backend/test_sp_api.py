"""
Test SP-API Client — verifies credentials and token refresh
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient

def main():
    print("=" * 60)
    print("SP-API Client Test")
    print("=" * 60)
    
    # Check credentials loaded
    print("\n1. Checking credentials...")
    creds = {
        "SP_API_CLIENT_ID": os.getenv("SP_API_CLIENT_ID", "")[:20] + "...",
        "SP_API_CLIENT_SECRET": "*****" if os.getenv("SP_API_CLIENT_SECRET") else "MISSING",
        "SP_API_REFRESH_TOKEN": os.getenv("SP_API_REFRESH_TOKEN", "")[:20] + "..." if os.getenv("SP_API_REFRESH_TOKEN") else "MISSING",
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": "*****" if os.getenv("AWS_SECRET_ACCESS_KEY") else "MISSING",
        "AWS_SELLER_ROLE_ARN": os.getenv("AWS_SELLER_ROLE_ARN", ""),
    }
    
    for key, val in creds.items():
        status = "✅" if val and val != "MISSING" else "❌"
        print(f"   {status} {key}: {val}")
    
    # Initialize client
    print("\n2. Initializing SPAPIClient...")
    try:
        client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU", country_code="eg")
        print("   ✅ Client initialized")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Get access token
    print("\n3. Getting LWA access token...")
    try:
        token = client._get_access_token()
        print(f"   ✅ Token: {token[:30]}... ({len(token)} chars)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test: Get product type definitions
    print("\n4. Testing: Get product type definitions (HOME_ORGANIZERS_AND_STORAGE)...")
    try:
        result = client.get_product_type_definitions("HOME_ORGANIZERS_AND_STORAGE")
        print(f"   Status: {result.get('status', 'N/A')}")
        if 'errors' in result:
            print(f"   ❌ Errors: {json.dumps(result['errors'], indent=2)[:500]}")
        else:
            print(f"   ✅ Success! Keys: {list(result.keys())[:10]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    main()
