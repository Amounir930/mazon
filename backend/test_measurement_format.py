"""
SP-API — Correct measurement format (flat not nested)
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API — Measurement Attributes: FLAT format (not nested)")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()

seller_id = 'A1DSHARRBRWYZW'
test_sku = 'MEASUREMENT-FIXED-001'

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
        
        # FLAT measurement format — NOT nested!
        'item_weight': [{'value': 0.8, 'unit': 'kilograms'}],
        
        'item_package_dimensions': [{
            'length': 25.0,
            'width': 10.0,
            'height': 15.0,
            'unit': 'centimeters'
        }],
        
        'item_package_weight': [{'value': 1.0, 'unit': 'kilograms'}],
        
        'unit_count': [{'value': 1, 'unit': 'count'}],
        
        # Fulfillment — try different values
        'fulfillment_availability': [{'quantity': 19}],
        
        # Price
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
        }],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    print(f"Status: {response.status_code}", flush=True)
    
    result = response.json()
    issues = result.get('issues', [])
    status = result.get('status', 'N/A')
    
    print(f"Response status: {status}", flush=True)
    
    if issues:
        print(f"Issues ({len(issues)}):")
        for issue in issues:
            print(f"  [{issue.get('severity')}] {issue.get('message', '')[:150]}", flush=True)
        
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} ERROR(s)")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:4000])
        else:
            print(f"\n✅✅✅ SUCCESS! No errors — listing accepted!", flush=True)
    else:
        print(f"\n✅✅✅ SUCCESS! No issues!", flush=True)
        
except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
