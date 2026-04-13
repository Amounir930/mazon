"""
SP-API — Try different item_package_dimensions formats
All other attributes are working — just need to fix dimensions!
"""
import os, sys, json, time
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
seller_id = 'A1DSHARRBRWYZW'

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
    'batteries_required': [{'value': False}],
}

# Try different dimension formats
dim_tests = [
    # Format 1: Separate entries with type
    {'sku': 'DIM-V1', 'dims': [
        {'length': {'value': 25.0, 'unit': 'centimeters'}},
        {'width': {'value': 10.0, 'unit': 'centimeters'}},
        {'height': {'value': 15.0, 'unit': 'centimeters'}},
    ]},
    # Format 2: Each with value+unit+type
    {'sku': 'DIM-V2', 'dims': [
        {'value': 25.0, 'unit': 'centimeters', 'type': 'length'},
        {'value': 10.0, 'unit': 'centimeters', 'type': 'width'},
        {'value': 15.0, 'unit': 'centimeters', 'type': 'height'},
    ]},
    # Format 3: Single entry with separate value objects for each
    {'sku': 'DIM-V3', 'dims': [{
        'length': {'value': 25.0, 'unit': 'centimeters'},
        'width': {'value': 10.0, 'unit': 'centimeters'},
        'height': {'value': 15.0, 'unit': 'centimeters'},
    }]},
    # Format 4: Separate simple entries
    {'sku': 'DIM-V4', 'dims': [
        {'length': 25.0, 'unit': 'centimeters'},
        {'width': 10.0, 'unit': 'centimeters'},
        {'height': 15.0, 'unit': 'centimeters'},
    ]},
    # Format 5: Nested value with just numbers
    {'sku': 'DIM-V5', 'dims': [{
        'value': {
            'length': 25.0,
            'width': 10.0,
            'height': 15.0,
            'unit': 'centimeters'
        }
    }]},
]

for test in dim_tests:
    sku = test['sku']
    payload = {
        'productType': 'HOME_ORGANIZERS_AND_STORAGE',
        'requirements': 'LISTING',
        'attributes': {**base_attrs, 'item_package_dimensions': test['dims']}
    }
    url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{sku}'
    params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
    headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
    aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)
    
    print(f"\n{'='*40}")
    print(f"Testing {sku} — dims format: {json.dumps(test['dims'], ensure_ascii=False)[:100]}", flush=True)
    
    try:
        response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
        result = response.json()
        issues = result.get('issues', [])
        status = result.get('status', 'N/A')
        
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        warnings = [i for i in issues if i.get('severity') == 'WARNING']
        
        print(f"  Status: {status} | Errors: {len(errors)} | Warnings: {len(warnings)}", flush=True)
        
        if errors:
            for e in errors:
                print(f"    ❌ {e.get('message', '')[:150]}", flush=True)
        else:
            print(f"    ✅✅✅ SUCCESS! No errors!", flush=True)
            break
        
        time.sleep(1)
    except Exception as e:
        print(f"  ❌ Exception: {e}")
