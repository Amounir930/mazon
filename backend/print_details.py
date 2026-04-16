import sys, json, requests
sys.path.append('c:/Users/Dell/Desktop/learn/amazon/backend')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU")
resp = client._make_request("GET", "/definitions/2020-09-01/productTypes/VASE", params={"marketplaceIds": "ARBP9OOSHTCHU"})
schema_url = resp.get("schema", {}).get("link", {}).get("resource")
schema = requests.get(schema_url).json()
props = schema.get("properties", {})

print(json.dumps(props.get("item_length_width_height"), indent=2))
