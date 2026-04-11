"""Test SP-API Self-authorized credentials - v2"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

print("Testing SP-API Self-authorized credentials...")

# Try using the library's default credential loading (from env vars)
os.environ['SP_API_REFRESH_TOKEN'] = "Atzr|IwEBIA4A4xmWNxFTeais7mF3dC6OpShVZoIP0U4wIAATo-em7oLwEZ7emG1wAtAA-Y7zwsvUJ-q3Ndld9aQ8OeackmDJiyHZjH7bY9coobaFfCPODgGQTophDzL-igWSz3mN11gOWKAKI5yLeqqSD9x7a9qUK71ZqdT1qxQ0YZAEwASOJFnbDN0QU1CS_bJr9cSMowwtpOshCfBNoULZhVjNpi84JdIL06TXTubDyghy2UlfSz-N4lYU1TWMeKKD-NPHJYtGoR7SS7XVbcDVr5DaO_EC1xRLKRYzkzoyKnv41DQ2BF3_cBvAwOj3zLZuanl6UUIzvl8wRrrpEmNaYXeO4TA2"
os.environ['SP_API_LWA_APP_ID'] = "amzn1.application-oa2-client.bc622c264b9c4158a55a8967ce93e1cc"
os.environ['SP_API_LWA_CLIENT_SECRET'] = "amzn1.oa2-cs.v1.83c5d141906aa1fc630f88b5870367d541bbb4162ce64cf8f1ad1721e6bcef04"
os.environ['SP_API_AWS_ACCESS_KEY'] = "AKIA5AJTOJBXTBC7UQ72"
os.environ['SP_API_AWS_SECRET_KEY'] = "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"

from sp_api.api import Sellers
from sp_api.base import SellingApiException, Marketplaces

print("Environment variables set")

try:
    # Create Sellers API for Egypt marketplace
    sellers_api = Sellers(marketplace=Marketplaces.EG)
    print("Sellers API instance created")
    
    # Try to get account info
    response = sellers_api.get_account()
    print(f"✅ Response: {response}")
    print(f"✅ Payload: {response.payload}")
    
except SellingApiException as e:
    print(f"❌ SP-API Error: {e}")
    print(f"   Response: {getattr(e, 'response', None)}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
