"""
SP-API Login Script - Standalone process
بيعمل SP-API call وبيكتب النتيجة في JSON file
"""
import os
import sys
import json
import time
from pathlib import Path

def main():
    output_file = os.environ.get("SPAPI_OUTPUT", "")
    if not output_file:
        print("ERROR: SPAPI_OUTPUT not set")
        sys.exit(1)

    # Read credentials from environment
    lwa_client_id = os.environ.get("SPAPI_CLIENT_ID", "")
    lwa_client_secret = os.environ.get("SPAPI_CLIENT_SECRET", "")
    refresh_token = os.environ.get("SPAPI_REFRESH_TOKEN", "")
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    marketplace_id = os.environ.get("SPAPI_MARKETPLACE_ID", "ARBP9OOSHTCHU")

    result = {"success": False, "error": "unknown"}

    try:
        # Set environment variables for sp_api library
        os.environ['LWA_APP_ID'] = lwa_client_id
        os.environ['LWA_CLIENT_SECRET'] = lwa_client_secret
        os.environ['SP_API_REFRESH_TOKEN'] = refresh_token
        if aws_access_key:
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
        if aws_secret_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key

        from sp_api.api import Sellers
        from sp_api.base import SellingApiException, Marketplaces

        marketplace_map = {
            "ARBP9OOSHTCHU": Marketplaces.EG,
            "A1F83G8C2ARO7P": Marketplaces.GB,
            "ATVPDKIKX0DER": Marketplaces.US,
        }
        marketplace = marketplace_map.get(marketplace_id, Marketplaces.EG)

        # Create Sellers API instance
        sellers_api = Sellers(marketplace=marketplace)
        
        # Call SP-API
        response = sellers_api.get_account()
        payload = response.payload

        seller_name = payload.get("businessName", "Unknown")
        account_status = payload.get("status", "UNKNOWN")

        result = {
            "success": True,
            "seller_name": seller_name,
            "marketplace_id": marketplace_id,
            "account_status": account_status,
            "account_type": payload.get("accountType", ""),
        }

        print(f"✅ Success: {seller_name}")

    except SellingApiException as e:
        error_str = str(e).lower()
        print(f"❌ SP-API Error: {e}")
        if "401" in error_str or "unauthorized" in error_str:
            result = {"success": False, "error": "بيانات غير صحيحة - Amazon رفض الدخول"}
        elif "403" in error_str or "forbidden" in error_str:
            result = {"success": False, "error": "لا توجد صلاحيات - تأكد من IAM Role"}
        else:
            result = {"success": False, "error": f"خطأ من Amazon: {str(e)[:200]}"}

    except Exception as e:
        print(f"❌ Error: {e}")
        result = {"success": False, "error": str(e)}

    # Write result to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str)

    print(f"Result written to {output_file}")


if __name__ == "__main__":
    main()
