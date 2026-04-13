"""
SP-API — Fixing last 3 errors:
1. batteries_required (try both names)
2. fulfillment_channel_code (inside value object)
3. item_package_dimensions (each dim has value+unit inside)
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API — Fixing final 3 errors")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()

seller_id = 'A1DSHARRBRWYZW'
test_sku = 'NEARLY-THERE-001'

payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        'item_name': [{'value': 'Professional Electric Hand Mixer', 'language_tag': 'en_US'}],
        'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'product_description': [{'value': 'Professional hand mixer.', 'language_tag': 'en_US'}],
        'bullet_point': [{'value': 'Multi-speed control.', 'language_tag': 'en_US'}],
        'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'model_name': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'model_number': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'condition_type': [{'value': 'new_new'}],
        'country_of_origin': [{'value': 'CN'}],
        'recommended_browse_nodes': [{'value': '21863799031'}],
        'included_components': [{'value': '1x Mixer', 'language_tag': 'en_US'}],
        'number_of_boxes': [{'value': 1}],
        'merchant_suggested_asin': [{'value': 'B0FSBH1WGZ'}],
        'supplier_declared_dg_hz_regulation': [{'value': 'not_applicable'}],
        'externally_assigned_product_identifier': [{'value': {'type': 'ean', 'value': '1245768907654'}}],
        'item_weight': [{'value': 0.8, 'unit': 'kilograms'}],
        'item_package_weight': [{'value': 1.0, 'unit': 'kilograms'}],
        'unit_count': [{'value': 1, 'unit': 'count'}],
        
        # Dimensions — each dimension is a SEPARATE entry!
        'item_package_dimensions': [
            {'length': {'value': 25.0, 'unit': 'centimeters'}},
            {'width': {'value': 10.0, 'unit': 'centimeters'}},
            {'height': {'value': 15.0, 'unit': 'centimeters'}},
        ],
        
        # Fulfillment — quantity at top level, channel_code inside?
        'fulfillment_availability': [{
            'quantity': 19,
            'fulfillment_channel_code': 'MFN'
        }],
        
        # Price
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
        }],
        
        # Batteries required (try BOTH attribute names)
        'batteries_required': [{'value': False}],
        'are_batteries_required': [{'value': False}],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    result = response.json()
    issues = result.get('issues', [])
    status = result.get('status', 'N/A')
    
    print(f"Status: {status}", flush=True)
    
    if issues:
        print(f"Issues ({len(issues)}):")
        for issue in issues:
            print(f"  [{issue.get('severity')}] {issue.get('message', '')[:200]}", flush=True)
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} errors")
        else:
            print(f"\n✅ SUCCESS!")
    else:
        print(f"\n✅✅✅ SUCCESS!")

except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
