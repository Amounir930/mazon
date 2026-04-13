"""
Debug SP-API — try different payload formats to find what works
"""
import os, json
from dotenv import load_dotenv
load_dotenv('.env')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()

seller_id = 'ARBP9OOSHTCHU'  # marketplace ID as fallback
test_sku = 'DEBUG-TEST-001'

# Try different formats
formats = {
    'format_A': {
        'productType': 'HOME_ORGANIZERS_AND_STORAGE',
        'attributes': {
            'item_name': [{'value': 'Test Product A', 'language_tag': 'en_US'}],
            'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
            'product_description': [{'value': 'Test description', 'language_tag': 'en_US'}],
            'bullet_point': [{'value': 'Test bullet', 'language_tag': 'en_US'}],
            'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
            'model_name': [{'value': 'TM-001', 'language_tag': 'en_US'}],
            'condition_type': [{'value': 'new_new'}],
            'country_of_origin': [{'value': 'CN'}],
            'recommended_browse_nodes': [{'value': '21863799031'}],
            'fulfillment_availability': [{'value': 10}],
            'purchasable_offer': [{'our_price': [{'schedule': [{'value_with_tax': 100.0}]}], 'currency': 'EGP', 'fulfillment_channel': 'MFN'}],
            'item_sku': [{'value': test_sku}],
        }
    },
    'format_B': {
        'productType': 'HOME_ORGANIZERS_AND_STORAGE',
        'requirements': 'LISTING',
        'attributes': {
            'item_name': [{'value': 'Test Product B', 'language_tag': 'en_US'}],
            'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
            'product_description': [{'value': 'Test description', 'language_tag': 'en_US'}],
            'bullet_point': [{'value': 'Test bullet', 'language_tag': 'en_US'}],
            'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
            'model_name': [{'value': 'TM-001', 'language_tag': 'en_US'}],
            'condition_type': [{'value': 'new_new'}],
            'country_of_origin': [{'value': 'CN'}],
            'recommended_browse_nodes': [{'value': '21863799031'}],
            'fulfillment_availability': [{'value': 10}],
            'purchasable_offer': [{'our_price': [{'schedule': [{'value_with_tax': 100.0}]}], 'currency': 'EGP', 'fulfillment_channel': 'MFN'}],
            'item_sku': [{'value': test_sku}],
            # Different: externally_assigned_product_identifier with type/value inside value object
            'externally_assigned_product_identifier': [{'value': {'type': 'ean', 'value': '5012345678901'}}],
        }
    },
    'format_C': {
        'productType': 'HOME_ORGANIZERS_AND_STORAGE',
        'requirements': 'LISTING',
        'attributes': {
            'item_name': [{'value': 'Test Product C', 'language_tag': 'en_US'}],
            'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
            'product_description': [{'value': 'Test description', 'language_tag': 'en_US'}],
            'bullet_point': [{'value': 'Test bullet', 'language_tag': 'en_US'}],
            'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
            'model_name': [{'value': 'TM-001', 'language_tag': 'en_US'}],
            'condition_type': [{'value': 'new_new'}],
            'country_of_origin': [{'value': 'CN'}],
            'recommended_browse_nodes': [{'value': '21863799031'}],
            'fulfillment_availability': [{'value': 10}],
            'purchasable_offer': [{'our_price': [{'schedule': [{'value_with_tax': 100.0}]}], 'currency': 'EGP', 'fulfillment_channel': 'MFN'}],
            # No item_sku - let the URL path SKU handle it
        }
    },
}

for name, payload in formats.items():
    print(f"\n{'='*50}")
    print(f"Testing {name}")
    print(f"{'='*50}")
    
    try:
        import requests
        from requests_auth_aws_sigv4 import AWSSigV4
        
        url = f"https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}"
        params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
        headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
        aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)
        
        response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text[:1000]}")
    except Exception as e:
        print(f"Exception: {e}")
