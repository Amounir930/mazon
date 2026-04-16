import sys, json, requests, jsonschema
sys.path.append('c:/Users/Dell/Desktop/learn/amazon/backend')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU")
resp = client._make_request("GET", "/definitions/2020-09-01/productTypes/VASE", params={"marketplaceIds": "ARBP9OOSHTCHU"})
schema_url = resp.get("schema", {}).get("link", {}).get("resource")
schema = requests.get(schema_url).json()
props = schema.get("properties", {})

unit_count_payload = [{"value": 1.0, "type": "count"}]
try:
    jsonschema.validate(unit_count_payload, props["unit_count"])
    print("unit_count (string format) is valid")
except Exception as e:
    print("unit_count (string format) err:", str(e).split('\n')[0])

unit_count_payload2 = [{"value": 1.0, "type": {"value": "count", "language_tag": "ar_AE"} }]
try:
    jsonschema.validate(unit_count_payload2, props["unit_count"])
    print("unit_count (object format) is valid")
except Exception as e:
    print("unit_count (object format) err:", str(e).split('\n')[0])


dim_payload = [{
    "length": {"value": 24.0, "unit": "centimeters"},
    "width": {"value": 9.0, "unit": "centimeters"},
    "height": {"value": 14.0, "unit": "centimeters"},
}]
if "item_dimensions" in props:
    try:
        jsonschema.validate(dim_payload, props["item_dimensions"])
        print("item_dimensions is valid")
    except Exception as e:
        print("item_dimensions err:", str(e).split('\n')[0])
else:
    print("item_dimensions not in schema!")
