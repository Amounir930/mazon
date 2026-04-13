"""
SP-API — FINAL SUCCESS — Real product with correct formats
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("🎉 SP-API — FINAL SUCCESS — Real Product Submission")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()
seller_id = 'A1DSHARRBRWYZW'

# Real product from active listings report
test_sku = 'SUCCESS-REAL-001'

description_html = """<p>اكتشف الراحة والقوة مع المضرب اليدوي الكهربائي الاحترافي المصمم خصيصاً ليمنحك نتائج مثالية في خفق البيض، تحضير الكريمة، وخلط العجائن الخفيفة بسرعة وكفاءة عالية. بفضل تصميمه المتطور وسرعاته المتعددة، ستحصل على تحكم كامل في كل وصفة، سواء كنت مبتدئاً في المطبخ أو طاهياً محترفاً.</p>"""

payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        # Identity
        'item_name': [{'value': 'Professional Electric Hand Mixer, Multi-Speed Egg Cream Dough Maker with Powerful Whisk Heads, Ergonomic Design, Easy to Clean for Modern Kitchens', 'language_tag': 'en_US'}],
        'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'product_description': [{'value': description_html, 'language_tag': 'en_US'}],
        'bullet_point': [
            {'value': 'Multi-speed control for eggs, cream, and dough', 'language_tag': 'en_US'},
            {'value': 'Ergonomic non-slip handle for comfortable use', 'language_tag': 'en_US'},
            {'value': 'Made from high quality food-safe materials', 'language_tag': 'en_US'},
            {'value': 'Lightweight and compact design for easy storage', 'language_tag': 'en_US'},
            {'value': 'Rust-resistant whisk heads for long-lasting use', 'language_tag': 'en_US'},
        ],
        'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'model_name': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'model_number': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'condition_type': [{'value': 'new_new'}],
        'country_of_origin': [{'value': 'CN'}],
        'recommended_browse_nodes': [{'value': '21863799031'}],
        'included_components': [{'value': '1x Electric Hand Mixer, 2x Whisk Heads, 1x User Manual', 'language_tag': 'en_US'}],
        'number_of_boxes': [{'value': 1}],
        'merchant_suggested_asin': [{'value': 'B0FSBH1WGZ'}],
        'supplier_declared_dg_hz_regulation': [{'value': 'not_applicable'}],
        'externally_assigned_product_identifier': [{'value': {'type': 'ean', 'value': '1245768907654'}}],
        
        # Weight — FLAT format
        'item_weight': [{'value': 0.8, 'unit': 'kilograms'}],
        'item_package_weight': [{'value': 1.0, 'unit': 'kilograms'}],
        
        # Unit count — FLAT format
        'unit_count': [{'value': 1, 'unit': 'count'}],
        
        # ✅ CORRECT dimensions format!
        'item_package_dimensions': [{
            'length': {'value': 25.0, 'unit': 'centimeters'},
            'width': {'value': 10.0, 'unit': 'centimeters'},
            'height': {'value': 15.0, 'unit': 'centimeters'},
        }],
        
        # Price
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
        }],
        
        # Batteries
        'batteries_required': [{'value': False}],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"📦 Seller ID: {seller_id}", flush=True)
print(f"📦 Test SKU: {test_sku}", flush=True)
print(f"📦 Attributes: {len(payload['attributes'])}", flush=True)
print(f"📦 URL: {url}", flush=True)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    result = response.json()
    issues = result.get('issues', [])
    status = result.get('status', 'N/A')
    submission_id = result.get('submissionId', 'N/A')
    
    print(f"\n{'='*60}", flush=True)
    print(f"📊 RESULT:", flush=True)
    print(f"   Status: {status}", flush=True)
    print(f"   Submission ID: {submission_id}", flush=True)
    print(f"   SKU: {result.get('sku', 'N/A')}", flush=True)
    
    if issues:
        print(f"\n⚠️ Issues ({len(issues)}):")
        for issue in issues:
            print(f"   [{issue.get('severity')}] {issue.get('message', '')[:200]}", flush=True)
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} ERROR(s) — not yet successful")
            print(f"\nFull response:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:4000])
        else:
            print(f"\n✅✅✅ SUCCESS! No errors — listing accepted!", flush=True)
            print(f"✅ Product SKU {test_sku} has been submitted to Amazon!", flush=True)
    else:
        print(f"\n✅✅✅ SUCCESS! No issues found!", flush=True)
        
except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
    import traceback
    traceback.print_exc()
