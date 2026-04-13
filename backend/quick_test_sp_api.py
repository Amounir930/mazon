"""Quick SP-API test with correct Seller ID"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("Starting SP-API test with Seller ID: A1DSHARRBRWYZW", flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
print(f"Token: {token[:30]}...", flush=True)

seller_id = 'A1DSHARRBRWYZW'
test_sku = 'SPAPI-REAL-002'

payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        'item_name': [{'value': 'Test Hand Mixer', 'language_tag': 'en_US'}],
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
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"PUT {url}", flush=True)
try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    print(f"Status: {response.status_code}", flush=True)
    print(f"Body: {response.text[:2000]}", flush=True)
except Exception as e:
    print(f"Exception: {e}", flush=True)
    import traceback
    traceback.print_exc()
