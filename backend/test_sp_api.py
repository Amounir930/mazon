import sys, json, requests
sys.path.append('c:/Users/Dell/Desktop/learn/amazon/backend')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU")
try:
    resp = client._make_request("GET", "/definitions/2020-09-01/productTypes/VASE", params={"marketplaceIds": "ARBP9OOSHTCHU"})
    schema_url = resp.get("schema", {}).get("link", {}).get("resource")
    if schema_url:
        print("Fetching schema...")
        schema = requests.get(schema_url).json()
        props = schema.get("properties", {})
        
        # Look for dimension related keys
        dim_keys = [k for k in props.keys() if "dimension" in k.lower() or "length" in k.lower() or "width" in k.lower() or "height" in k.lower()]
        print("Dimension keys:", dim_keys)
        
        if "item_dimensions" in props:
            print("item_dimensions schema:", json.dumps(props["item_dimensions"], indent=2))
        
        if "unit_count" in props:
            print("unit_count schema:", json.dumps(props["unit_count"], indent=2))
    else:
        print("NO SCHEMA URL")
except Exception as e:
    print(f"Error: {e}")
