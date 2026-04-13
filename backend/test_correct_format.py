"""
Test SP-API — Corrected complex attribute formats
Fixes: dimensions format, weight format, fulfillment channel
"""
import os, sys, json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.services.sp_api_client import SPAPIClient
import requests
from requests_auth_aws_sigv4 import AWSSigV4

print("=" * 60)
print("SP-API Test — Corrected complex attribute formats")
print("=" * 60, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
token = client._get_access_token()

seller_id = 'A1DSHARRBRWYZW'
test_sku = 'REAL-CORRECT-001'

description_html = """<p>Professional electric hand mixer with multi-speed control. Perfect for eggs, cream, and dough. Ergonomic design, easy to clean. Made from high quality food-safe materials with rust-resistant whisk heads.</p>"""

# Based on real TSV report values:
# fulfillment-channel: DEFAULT (not MFN!)
# item-condition: 11
# product-id-type: 1 (EAN)
payload = {
    'productType': 'HOME_ORGANIZERS_AND_STORAGE',
    'requirements': 'LISTING',
    'attributes': {
        # Identity
        'item_name': [{'value': 'Professional Electric Hand Mixer, Multi-Speed Egg Cream Dough Maker with Powerful Whisk Heads', 'language_tag': 'en_US'}],
        'brand': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'product_description': [{'value': description_html, 'language_tag': 'en_US'}],
        'bullet_point': [
            {'value': 'Multi-speed control for eggs, cream, and dough', 'language_tag': 'en_US'},
            {'value': 'Ergonomic non-slip handle for comfortable use', 'language_tag': 'en_US'},
            {'value': 'Made from high quality food-safe materials', 'language_tag': 'en_US'},
        ],
        'manufacturer': [{'value': 'Generic', 'language_tag': 'en_US'}],
        'model_name': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'model_number': [{'value': 'HM-001', 'language_tag': 'en_US'}],
        'condition_type': [{'value': 'new_new'}],
        'country_of_origin': [{'value': 'CN'}],
        'recommended_browse_nodes': [{'value': '21863799031'}],
        
        # Fulfillment — try DEFAULT instead of MFN
        'fulfillment_availability': [{
            'value': 19,
            'fulfillment_channel_code': 'DEFAULT'
        }],
        
        # Price
        'purchasable_offer': [{
            'our_price': [{'schedule': [{'value_with_tax': 350.0}]}],
            'currency': 'EGP',
        }],
        
        # EAN — try simple value first
        'externally_assigned_product_identifier': [{'value': '1245768907654'}],
        
        # Weight — simple number value (Amazon might auto-detect unit)
        'item_weight': [{'value': 800}],  # in grams?
        
        # Package dimensions — try flat structure
        'item_package_dimensions': [{
            'length': 25.0,
            'width': 10.0,
            'height': 15.0,
            'unit': 'centimeters'
        }],
        
        # Package weight — simple number
        'item_package_weight': [{'value': 1000}],  # in grams
        
        # Unit count — simple number
        'unit_count': [{'value': 1}],
        
        # Included components
        'included_components': [{'value': '1x Electric Hand Mixer, 2x Whisk Heads', 'language_tag': 'en_US'}],
        
        # Number of boxes
        'number_of_boxes': [{'value': 1}],
        
        # Merchant suggested ASIN
        'merchant_suggested_asin': [{'value': 'B0FSBH1WGZ'}],
        
        # Supplier declared DG HZ regulation
        'supplier_declared_dg_hz_regulation': [{'value': 'not_applicable'}],
    }
}

url = f'https://{client.endpoint}/listings/2021-08-01/items/{seller_id}/{test_sku}'
params = {'marketplaceIds': client.marketplace_id, 'issueLocale': 'en_US'}
headers = {'x-amz-access-token': token, 'Content-Type': 'application/json', 'Host': client.endpoint}
aws_auth = AWSSigV4('execute-api', aws_access_key_id=client.aws_access_key, aws_secret_access_key=client.aws_secret_key, region=client.aws_region)

print(f"Attributes count: {len(payload['attributes'])}", flush=True)
print(f"Fulfillment channel: DEFAULT", flush=True)

try:
    response = requests.put(url, headers=headers, json=payload, params=params, auth=aws_auth, timeout=30)
    print(f"\nStatus: {response.status_code}", flush=True)
    
    result = response.json()
    issues = result.get('issues', [])
    
    if issues:
        print(f"\nIssues ({len(issues)}):")
        for issue in issues:
            print(f"  [{issue.get('severity', 'N/A')}] {issue.get('message', '')[:150]}", flush=True)
        
        errors = [i for i in issues if i.get('severity') == 'ERROR']
        if errors:
            print(f"\n❌ {len(errors)} ERROR(s)")
            # Print full response for debugging
            print(f"\nFull response (first 3000 chars):")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
        else:
            print(f"\n✅ No errors — listing accepted!")
    else:
        print(f"\n✅✅✅ SUCCESS! No issues found!", flush=True)
        
except Exception as e:
    print(f"\n❌ Exception: {e}", flush=True)
    import traceback
    traceback.print_exc()
