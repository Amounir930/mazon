"""
Test SP-API — Fixed payload with ALL required attributes
Based on actual error messages from Amazon
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API Test — FIXED payload with all required attributes")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
print(f"Token: {token[:30]}...", flush=True)

seller_id = 'A1DSHARRBRWYZW'
test_sku = 'REAL-FIXED-001'

description_html = """<p>اكتشف الراحة والقوة مع المضرب اليدوي الكهربائي الاحترافي المصمم خصيصاً ليمنحك نتائج مثالية في خفق البيض، تحضير الكريمة، وخلط العجائن الخفيفة بسرعة وكفاءة عالية. بفضل تصميمه المتطور وسرعاته المتعددة، ستحصل على تحكم كامل في كل وصفة. مصنوع من مواد عالية الجودة وآمنة للطعام، مع هيكل متين ورؤوس خفق مقاومة للصدأ.</p>"""

payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        # Identity
        'item_name': [{
            'value': 'Professional Electric Hand Mixer, Multi-Speed Egg Cream Dough Maker with Powerful Whisk Heads, Ergonomic Design, Easy to Clean for Modern Kitchens',
            'language_tag': 'en_US'
        }],
        'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
        
        # Description
        'product_description': [{'value': description_html, 'language_tag': 'en_US'}],
        
        # Bullet points
        'bullet_point': [
            {'value': 'Multi-speed control for eggs, cream, and dough', 'language_tag': 'en_US'},
            {'value': 'Ergonomic non-slip handle for comfortable use', 'language_tag': 'en_US'},
            {'value': 'Made from high quality food-safe materials', 'language_tag': 'en_US'},
            {'value': 'Lightweight and compact design for easy storage', 'language_tag': 'en_US'},
            {'value': 'Rust-resistant whisk heads for long-lasting use', 'language_tag': 'en_US'},
        ],
        
        # Manufacturer & Model Number (NOT model_name!)
        'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'model_number': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        
        # Condition
        'condition_type': [{'value': 'new_new'}],
        
        # Country of origin
        'country_of_origin': [{'value': 'CN'}],
        
        # Browse node
        'recommended_browse_nodes': [{'value': '21863799031'}],
        
        # Fulfillment — NEEDS fulfillment_channel_code inside!
        'fulfillment_availability': [{
            'value': 19,
            'fulfillment_channel_code': 'MFN'
        }],
        
        # Price
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
        }],
        
        # EAN — needs to be type+value inside value object
        'externally_assigned_product_identifier': [{
            'value': {'type': 'ean', 'value': '1245768907654'}
        }],
        
        # Weight — value must contain unit inside!
        'item_weight': [{
            'value': {'value': 0.8, 'unit': 'kilograms'}
        }],
        
        # Package dimensions — each dimension is a separate array item!
        'item_package_dimensions': [
            {'value': {'value': 25.0, 'unit': 'centimeters'}, 'type': 'length'},
            {'value': {'value': 10.0, 'unit': 'centimeters'}, 'type': 'width'},
            {'value': {'value': 15.0, 'unit': 'centimeters'}, 'type': 'height'},
            {'value': {'value': 25.0, 'unit': 'centimeters'}, 'type': 'unit'},
        ],
        
        # Package weight — value must contain unit inside!
        'item_package_weight': [{
            'value': {'value': 1.0, 'unit': 'kilograms'}
        }],
        
        # Unit count — value must contain unit inside!
        'unit_count': [{
            'value': {'value': 1, 'unit': 'count'}
        }],
        
        # Included components
        'included_components': [{
            'value': '1x Electric Hand Mixer, 2x Whisk Heads, 1x User Manual',
            'language_tag': 'en_US'
        }],
        
        # Number of boxes
        'number_of_boxes': [{'value': 1}],
        
        # Merchant suggested ASIN (using the real ASIN from the report)
        'merchant_suggested_asin': [{'value': 'B0FSBH1WGZ'}],
        
        # Are batteries required
        'are_batteries_required': [{'value': False}],
        
        # Supplier declared DG HZ regulation
        'supplier_declared_dg_hz_regulation': [{'value': 'not_applicable'}],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"\nSeller ID: {seller_id}")
print(f"Test SKU: {test_sku}")
print(f"Attributes count: {len(payload['attributes'])}", flush=True)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    print(f"\nStatus: {response.status_code}", flush=True)
    
    result = response.json()
    print(f"\n📊 Full Response:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:5000], flush=True)
    
    issues = result.get('issues', [])
    if issues:
        print(f"\n⚠️ Issues ({len(issues)}):")
        for issue in issues:
            print(f"   - [{issue.get('severity', 'N/A')}] {issue.get('code')}: {issue.get('message', '')[:150]}", flush=True)
        
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} ERROR(s)")
        else:
            print(f"\n✅ No errors — listing accepted (warnings only)")
    else:
        print(f"\n✅✅✅ SUCCESS! No issues found!", flush=True)
        
except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
    import traceback
    traceback.print_exc()
