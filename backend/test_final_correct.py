"""
SP-API — Final corrected payload with ALL formats fixed
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API — Final Corrected Payload (All formats fixed)")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()

seller_id = 'A1DSHARRBRWYZW'
test_sku = 'FINAL-CORRECT-001'

# CORRECT format for ALL complex attributes per SP-API schema
payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        # Identity
        'item_name': [{'value': 'Professional Electric Hand Mixer, Multi-Speed Egg Cream Dough Maker with Powerful Whisk Heads', 'language_tag': 'en_US'}],
        'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'product_description': [{'value': 'Professional electric hand mixer with multi-speed control. Perfect for eggs, cream, and dough. Ergonomic design, easy to clean.', 'language_tag': 'en_US'}],
        'bullet_point': [
            {'value': 'Multi-speed control for eggs, cream, and dough', 'language_tag': 'en_US'},
            {'value': 'Ergonomic non-slip handle for comfortable use', 'language_tag': 'en_US'},
            {'value': 'Made from high quality food-safe materials', 'language_tag': 'en_US'},
        ],
        'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'model_name': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'model_number': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'condition_type': [{'value': 'new_new'}],
        'country_of_origin': [{'value': 'CN'}],
        'recommended_browse_nodes': [{'value': '21863799031'}],
        
        # Fulfillment — correct format: quantity + fulfillment_channel_code as separate keys
        'fulfillment_availability': [{
            'quantity': 19,
            'fulfillment_channel_code': 'MFN'
        }],
        
        # Price
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
        }],
        
        # EAN — value must contain type+value inside!
        'externally_assigned_product_identifier': [{
            'value': {'type': 'ean', 'value': '1245768907654'}
        }],
        
        # Weight — value must be an object with value+unit!
        'item_weight': [{
            'value': {'value': 0.8, 'unit': 'kilograms'}
        }],
        
        # Package dimensions — value must be an object with nested value+unit for each dimension!
        'item_package_dimensions': [{
            'value': {
                'length': {'value': 25.0, 'unit': 'centimeters'},
                'width': {'value': 10.0, 'unit': 'centimeters'},
                'height': {'value': 15.0, 'unit': 'centimeters'}
            }
        }],
        
        # Package weight — value must be an object with value+unit!
        'item_package_weight': [{
            'value': {'value': 1.0, 'unit': 'kilograms'}
        }],
        
        # Unit count — value must be an object with value+unit!
        'unit_count': [{
            'value': {'value': 1, 'unit': 'count'}
        }],
        
        # Included components
        'included_components': [{'value': '1x Electric Hand Mixer, 2x Whisk Heads', 'language_tag': 'en_US'}],
        
        # Number of boxes
        'number_of_boxes': [{'value': 1}],
        
        # Merchant suggested ASIN
        'merchant_suggested_asin': [{'value': 'B0FSBH1WGZ'}],
        
        # Supplier declared DG HZ regulation
        'supplier_declared_dg_hz_regulation': [{'value': 'not_applicable'}],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"Seller ID: {seller_id}")
print(f"Test SKU: {test_sku}")
print(f"Attributes: {len(payload['attributes'])}", flush=True)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    print(f"\nStatus: {response.status_code}", flush=True)
    
    result = response.json()
    issues = result.get('issues', [])
    status = result.get('status', 'N/A')
    
    print(f"Status: {status}", flush=True)
    print(f"Submission ID: {result.get('submissionId', 'N/A')}", flush=True)
    
    if issues:
        print(f"\nIssues ({len(issues)}):")
        for issue in issues:
            print(f"  [{issue.get('severity', 'N/A')}] {issue.get('message', '')[:150]}", flush=True)
        
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} ERROR(s) — still failing")
            print(f"\nFull response:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:4000])
        else:
            print(f"\n✅✅✅ SUCCESS! No errors — listing accepted!", flush=True)
    else:
        print(f"\n✅✅✅ SUCCESS! No issues found!", flush=True)
        
except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
    import traceback
    traceback.print_exc()
