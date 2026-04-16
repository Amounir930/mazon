import sys
sys.path.append('c:/Users/Dell/Desktop/learn/amazon/backend')
from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id="ARBP9OOSHTCHU")
product = {
    "sku": "ART-DEC-100",
    "amazon_product_type": "VASE",
    "name": "Testing Enum Vase",
    "description": "Test",
    "brand": "Generic",
    "price": 100,
    "quantity": 10,
    "unit_count": "1",
    "unit_count_type": "count"
}
res = client.create_listing_from_product("A1DSHARRBRWYZW", product)
if res["success"]:
    print("SUCCESS!")
else:
    print("ERRORS:", res["errors"])
    for x in res.get("raw_response", {}).get("issues", []):
         print("-", x.get("message"))
