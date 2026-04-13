"""
SP-API — Get exact schema for the 2 failing attributes
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()

# Get full schema
import requests
from requests_auth_aws_sigv4 import AWSSigV4

url = f'https://{client.endpoint}/definitions/2020-09-01/productTypes/HOME_ORGANIZERS_AND_STORAGE'
params = {'marketplaceIds': 'ARBP9OOSHTCHU', 'requirements': 'LISTING', 'requirementsEnforced': 'ENFORCED'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

response = requests.get(url, headers=headers, params=params, auth=aws_auth, timeout=30)
schema = response.json()

# Save full schema
with open('sp_api_schema.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print(f"Schema keys: {list(schema.keys())}")

# Look for item_package_dimensions schema
props = schema.get('properties', schema.get('schema', {}).get('properties', {}))
if not props:
    # Try nested structure
    if 'schema' in schema:
        props = schema['schema'].get('properties', {})
    elif 'propertyGroups' in schema:
        props = schema

print(f"Properties keys (first 20): {list(props.keys())[:20]}")

# Search for the specific attributes
search_attrs = ['item_package_dimensions', 'fulfillment_availability', 'batteries_required']
for attr in search_attrs:
    # Search in the schema
    if attr in json.dumps(props):
        print(f"\n✅ Found {attr} in schema")
        # Extract the definition
        def find_in_schema(data, key, path=""):
            if isinstance(data, dict):
                if key in data:
                    print(f"  Path: {path}/{key}")
                    print(f"  Def: {json.dumps(data[key], indent=2, ensure_ascii=False)[:500]}")
                for k, v in data.items():
                    find_in_schema(v, key, f"{path}/{k}")
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    find_in_schema(item, key, f"{path}[{i}]")
        
        find_in_schema(schema, attr)
    else:
        print(f"\n❌ {attr} not found in schema")

# Also check requirements
reqs = schema.get('requirements', {})
listing_reqs = reqs.get('LISTING', {})
print(f"\nRequired attributes for LISTING ({len(listing_reqs)}):")
for attr_name, attr_def in list(listing_reqs.items())[:30]:
    if attr_def.get('required', False):
        print(f"  ✅ {attr_name}")
