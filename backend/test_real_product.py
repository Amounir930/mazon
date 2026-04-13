"""
Test SP-API with REAL product from active listings report
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API Test — Real product from active listings report")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
print(f"Token: {token[:30]}...", flush=True)

# Real Seller ID
seller_id = 'A1DSHARRBRWYZW'

# Real product from تقرير العروض المفعلة (first entry)
# SKU: 00-3A5S-1EYF | ASIN: B0FSBH1WGZ | Price: 350 | Qty: 19
test_sku = 'REAL-TEST-001'

description_html = """<p>اكتشف الراحة والقوة مع المضرب اليدوي الكهربائي الاحترافي المصمم خصيصاً ليمنحك نتائج مثالية في خفق البيض، تحضير الكريمة، وخلط العجائن الخفيفة بسرعة وكفاءة عالية. بفضل تصميمه المتطور وسرعاته المتعددة، ستحصل على تحكم كامل في كل وصفة. مصنوع من مواد عالية الجودة وآمنة للطعام، مع هيكل متين ورؤوس خفق مقاومة للصدأ.</p>"""

payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        # Identity — REAL product name from the report
        'item_name': [{
            'value': 'Professional Electric Hand Mixer, Multi-Speed Egg Cream Dough Maker with Powerful Whisk Heads, Ergonomic Design, Easy to Clean for Modern Kitchens',
            'language_tag': 'en_US'
        }],
        'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
        
        # Description
        'product_description': [{'value': description_html, 'language_tag': 'en_US'}],
        
        # Bullet points (extracted from description)
        'bullet_point': [
            {'value': 'Multi-speed control for eggs, cream, and dough', 'language_tag': 'en_US'},
            {'value': 'Ergonomic non-slip handle for comfortable use', 'language_tag': 'en_US'},
            {'value': 'Made from high quality food-safe materials', 'language_tag': 'en_US'},
            {'value': 'Lightweight and compact design for easy storage', 'language_tag': 'en_US'},
            {'value': 'Rust-resistant whisk heads for long-lasting use', 'language_tag': 'en_US'},
        ],
        
        # Manufacturer & Model
        'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'model_name': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        
        # Condition (11 = New in the report)
        'condition_type': [{'value': 'new_new'}],
        
        # Country of origin
        'country_of_origin': [{'value': 'CN'}],
        
        # Browse node (from active listing: HOME_ORGANIZERS_AND_STORAGE)
        'recommended_browse_nodes': [{'value': '21863799031'}],
        
        # Quantity (19 in the report)
        'fulfillment_availability': [{'value': 19}],
        
        # Price (350 in the report) + fulfillment channel (DEFAULT = MFN)
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
            'fulfillment_channel': 'MFN'
        }],
        
        # EAN (the real product has product-id-type=1 which is EAN, but product-id is empty in report)
        # We'll use a placeholder EAN since the real one isn't in the TSV
        'externally_assigned_product_identifier': [{'value': '1245768907654'}],
        
        # Weight (required)
        'item_weight': [{'value': {'value': 0.8, 'unit': 'kilograms'}}],
        
        # Package dimensions (required)
        'item_package_dimensions': [{
            'value': {
                'length': {'value': 25.0, 'unit': 'centimeters'},
                'width': {'value': 10.0, 'unit': 'centimeters'},
                'height': {'value': 15.0, 'unit': 'centimeters'},
                'unit': 'centimeters'
            }
        }],
        
        # Package weight (required)
        'item_package_weight': [{'value': {'value': 1.0, 'unit': 'kilograms'}}],
        
        # Unit count (required)
        'unit_count': [{'value': {'value': 1, 'unit': 'count'}}],
        
        # Unit count type
        'unit_count_type': [{'value': 'count'}],
        
        # Number of items
        'number_of_items': [{'value': 1}],
        
        # Supplier declared DG HZ regulation (required)
        'supplier_declared_dg_hz_regulation': [{'value': 'not_applicable'}],
        
        # Handling time
        'handling_time': [{'value': 1}],
        
        # Target audience
        'target_audience': [{'value': 'adult'}],
        
        # Package quantity
        'package_quantity': [{'value': 1}],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"\nSeller ID: {seller_id}")
print(f"Marketplace ID: {client.marketplace_id}")
print(f"Test SKU: {test_sku}")
print(f"URL: {url}", flush=True)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    print(f"\nStatus: {response.status_code}", flush=True)
    
    result = response.json()
    print(f"\n📊 Full Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:5000], flush=True)
    
    # Check if there are issues
    issues = result.get('issues', [])
    if issues:
        print(f"\n⚠️ Issues ({len(issues)}):")
        for issue in issues:
            print(f"   - [{issue.get('severity', 'N/A')}] {issue.get('code')}: {issue.get('message', '')[:150]}", flush=True)
        
        # Check if there are any ERROR severity issues
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} ERROR(s) — listing not accepted")
        else:
            print(f"\n✅ No errors — listing accepted (warnings only)")
    else:
        print(f"\n✅✅✅ SUCCESS! No issues found!", flush=True)
        
except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
    import traceback
    traceback.print_exc()
