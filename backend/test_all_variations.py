"""
SP-API — Trying ALL format variations for the last 3 errors
"""
import os, sys, json, time
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API — Trying ALL dimension/fulfillment/battery formats")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
seller_id = 'A1DSHARRBRWYZW'

# Common attributes
base_attrs = {
    'item_name': [{'value': 'Test Mixer', 'language_tag': 'en_US'}],
    'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
    'product_description': [{'value': 'Test.', 'language_tag': 'en_US'}],
    'bullet_point': [{'value': 'Test bullet.', 'language_tag': 'en_US'}],
    'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
    'model_name': [{'value': 'TM-001', 'language_tag': 'en_US'}],
    'model_number': [{'value': 'TM-001', 'language_tag': 'en_US'}],
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
    'purchasable_offer': [{'our_price': [{'schedule': [{'value_with_tax': 100.0}]}], 'currency': 'EGP'}],
}

# Try different combinations
tests = [
    # Test 1: dimensions flat, batteries_required, fulfillment with MFN
    {
        'sku': 'TEST-V1',
        'attrs': {
            **base_attrs,
            'item_package_dimensions': [{'length': 25.0, 'width': 10.0, 'height': 15.0, 'unit': 'centimeters'}],
            'fulfillment_availability': [{'quantity': 10, 'fulfillment_channel_code': 'MFN'}],
            'batteries_required': [{'value': False}],
        }
    },
    # Test 2: dimensions with value object, batteries_required, fulfillment without channel
    {
        'sku': 'TEST-V2',
        'attrs': {
            **base_attrs,
            'item_package_dimensions': [{'value': {'length': 25.0, 'width': 10.0, 'height': 15.0, 'unit': 'centimeters'}}],
            'fulfillment_availability': [{'quantity': 10}],
            'batteries_required': [{'value': False}],
        }
    },
    # Test 3: dimensions each separate, batteries_required, fulfillment with DEFAULT
    {
        'sku': 'TEST-V3',
        'attrs': {
            **base_attrs,
            'item_package_dimensions': [
                {'length': 25.0, 'unit': 'centimeters'},
                {'width': 10.0, 'unit': 'centimeters'},
                {'height': 15.0, 'unit': 'centimeters'},
            ],
            'fulfillment_availability': [{'quantity': 10, 'fulfillment_channel_code': 'DEFAULT'}],
            'batteries_required': [{'value': False}],
        }
    },
    # Test 4: dimensions with nested value+unit for each, batteries_required, fulfillment with MERCHANT
    {
        'sku': 'TEST-V4',
        'attrs': {
            **base_attrs,
            'item_package_dimensions': [{
                'value': {
                    'length': {'value': 25.0, 'unit': 'centimeters'},
                    'width': {'value': 10.0, 'unit': 'centimeters'},
                    'height': {'value': 15.0, 'unit': 'centimeters'},
                }
            }],
            'fulfillment_availability': [{'quantity': 10, 'fulfillment_channel_code': 'MERCHANT_FULFILLED_NETWORK'}],
            'batteries_required': [{'value': False}],
        }
    },
    # Test 5: are_batteries_required instead of batteries_required
    {
        'sku': 'TEST-V5',
        'attrs': {
            **base_attrs,
            'item_package_dimensions': [{'length': 25.0, 'width': 10.0, 'height': 15.0, 'unit': 'centimeters'}],
            'fulfillment_availability': [{'quantity': 10, 'fulfillment_channel_code': 'MFN'}],
            'are_batteries_required': [{'value': False}],
        }
    },
]

for test in tests:
    sku = test['sku']
    payload = {'productType': 'HOME_ORGANIZERS_AND_STORAGE', 'requirements': 'LISTING', 'attributes': test['attrs']}
    url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{sku}'
    params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
    headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
    aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)
    
    print(f"\n{'='*40}")
    print(f"Testing {sku}", flush=True)
    
    try:
        response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
        result = response.json()
        issues = result.get('issues', [])
        status = result.get('status', 'N/A')
        
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        warnings = [i for i in issues if i.get('severity') == 'WARNING']
        
        print(f"  Status: {status}")
        print(f"  Errors: {len(errors)}, Warnings: {len(warnings)}")
        
        if errors:
            for e in errors:
                print(f"    ❌ [{e.get('severity')}] {e.get('message', '')[:120]}")
        else:
            print(f"    ✅✅✅ SUCCESS! No errors!", flush=True)
            
        if len(errors) <= 2:
            print(f"  Full response:")
            print(f"  {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        
        time.sleep(1)  # Rate limit
    except Exception as e:
        print(f"  ❌ Exception: {e}")
