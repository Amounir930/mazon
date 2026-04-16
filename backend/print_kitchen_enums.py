import sys, json, requests
sys.path.append('c:/Users/Dell/Desktop/learn/amazon/backend')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU")
resp = client._make_request("GET", "/definitions/2020-09-01/productTypes/KITCHEN", params={"marketplaceIds": "ARBP9OOSHTCHU"})
schema_url = resp.get("schema", {}).get("link", {}).get("resource")
schema = requests.get(schema_url).json()
props = schema.get("properties", {})

keys = ["care_instructions", "accepted_voltage_frequency", "power_plug_type", "contains_liquid_contents"]
res = {}
for k in keys:
    res[k] = props.get(k)
print(json.dumps(res, indent=2)[:3000])
