import sys, json, requests
sys.path.append('c:/Users/Dell/Desktop/learn/amazon/backend')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU")
resp = client._make_request("GET", "/definitions/2020-09-01/productTypes/KITCHEN", params={"marketplaceIds": "ARBP9OOSHTCHU"})
schema_url = resp.get("schema", {}).get("link", {}).get("resource")
schema = requests.get(schema_url).json()
props = schema.get("properties", {})

search_terms = ["care", "volt", "plug", "liquid", "power", "warn"]
print("Matched keys:")
for k in props.keys():
    if any(x in k.lower() for x in search_terms):
        print(f"- {k}")
