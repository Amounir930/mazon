"""
Verify the listing was created
"""
import os, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
seller_id = 'A1DSHARRBRWYZW'

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/SUCCESS-REAL-001'
params = {'marketplaceIds': 'ARBP9OOSHTCHU', 'locale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"GET {url}")
response = requests.get(url, headers=headers, params=params, auth=aws_auth, timeout=30)
print(f"Status: {response.status_code}")
print(f"Body: {response.text[:2000]}")

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ Product exists!")
    print(f"Status: {result.get('status', 'N/A')}")
    attrs = result.get('attributes', {})
    if 'item_name' in attrs:
        print(f"Name: {attrs['item_name'][0].get('value', 'N/A')}")
    if 'brand' in attrs:
        print(f"Brand: {attrs['brand'][0].get('value', 'N/A')}")
elif response.status_code == 404:
    print(f"\n❌ Product not found — might need time to process")
else:
    print(f"\n⚠️ Unexpected status: {response.status_code}")
