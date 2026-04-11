"""Test SP-API with IAM Role"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.services.unified_auth import _sp_api_call_wrapper

# Credentials from .env
# NOTE: For SP-API to work, you need an IAM Role ARN that has SellingPartnerAPIFullAccess policy
# Get it from: AWS IAM Console -> Roles -> [Your SP-API Role] -> Role ARN

result = _sp_api_call_wrapper(
    lwa_client_id="amzn1.application-oa2-client.bc622c264b9c4158a55a8967ce93e1cc",
    lwa_client_secret="amzn1.oa2-cs.v1.83c5d141906aa1fc630f88b5870367d541bbb4162ce64cf8f1ad1721e6bcef04",
    refresh_token="Atzr|IwEBIA4A4xmWNxFTeais7mF3dC6OpShVZoIP0U4wIAATo-em7oLwEZ7emG1wAtAA-Y7zwsvUJ-q3Ndld9aQ8OeackmDJiyHZjH7bY9coobaFfCPODgGQTophDzL-igWSz3mN11gOWKAKI5yLeqqSD9x7a9qUK71ZqdT1qxQ0YZAEwASOJFnbDN0QU1CS_bJr9cSMowwtpOshCfBNoULZhVjNpi84JdIL06TXTubDyghy2UlfSz-N4lYU1TWMeKKD-NPHJYtGoR7SS7XVbcDVr5DaO_EC1xRLKRYzkzoyKnv41DQ2BF3_cBvAwOj3zLZuanl6UUIzvl8wRrrpEmNaYXeO4TA2",
    marketplace_id="ARBP9OOSHTCHU",
    aws_access_key="AKIA5AJTOJBXTBC7UQ72",
    aws_secret_key="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",
)

print(f"Success: {result.get('success')}")
if result.get('success'):
    print(f"✅ Seller Name: {result.get('seller_name')}")
    print(f"✅ Account Status: {result.get('account_status')}")
    print(f"✅ Marketplace: {result.get('marketplace_id')}")
else:
    print(f"❌ Error: {result.get('error')}")
    if result.get('details'):
        print(f"   Details: {result.get('details')}")
