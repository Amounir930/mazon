import json
from http.cookiejar import CookieJar, Cookie
from curl_cffi import requests as cffi_r
from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data

db = SessionLocal()
sess = db.query(AuthSession).filter(AuthSession.auth_method=='browser', AuthSession.is_active==True).first()
cookies = json.loads(decrypt_data(sess.cookies_json))
country = sess.country_code or 'eg'
db.close()

print(f"Session: {len(cookies)} cookies, country={country}")

base = 'https://sellercentral.amazon.eg'
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

headers_base = {
    'User-Agent': ua,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Origin': base,
    'Referer': f'{base}/home',
}

jar = CookieJar()
for c in cookies:
    name = c.get('name','')
    val = c.get('value','')
    if name and val is not None:
        try:
            http_c = Cookie(0, name, str(val), None, False, '.amazon.eg', True, True, c.get('path','/'), True, False, None, True, None, None, {'HttpOnly': c.get('httpOnly')}, False)
            jar.set_cookie(http_c)
        except:
            pass

s = cffi_r.Session(impersonate='chrome131')
s.cookies = jar

# Step 1: Warm up session - visit home page
print("\nStep 1: Visiting /home...")
r1 = s.get(f'{base}/home', timeout=15, allow_redirects=True)
print(f"  Status: {r1.status_code}, Final URL: {r1.url}")

# Step 2: Visit product search page
print("\nStep 2: Visiting /product-search/search...")
r2 = s.get(f'{base}/product-search/search', timeout=15)
print(f"  Status: {r2.status_code}")

# Step 3: Try different endpoint variations
print("\nStep 3: Testing API endpoints...")

tests = [
    # Test with different referers
    {'url': f'{base}/abis/ajax/create-listing', 'params': {'productType': 'HOME_ORGANIZERS_AND_STORAGE', 'listingLanguageCode': 'ar_AE'}, 'referer': f'{base}/product-search/search'},
    {'url': f'{base}/abis/ajax/create-listing', 'params': {'productType': 'HOME_ORGANIZERS_AND_STORAGE', 'listingLanguageCode': 'ar_AE'}, 'referer': f'{base}/home'},
    {'url': f'{base}/abis/ajax/create-listing', 'params': {'productType': 'HOME_ORGANIZERS_AND_STORAGE', 'listingLanguageCode': 'en_US'}, 'referer': f'{base}/product-search/search'},
    # Test without params
    {'url': f'{base}/abis/ajax/create-listing', 'params': None, 'referer': f'{base}/product-search/search'},
    # Test with POST instead of GET
    {'url': f'{base}/abis/ajax/create-listing', 'params': {'productType': 'HOME_ORGANIZERS_AND_STORAGE', 'listingLanguageCode': 'ar_AE'}, 'referer': f'{base}/product-search/search', 'method': 'POST'},
]

for i, t in enumerate(tests):
    h = headers_base.copy()
    if t.get('referer'):
        h['Referer'] = t['referer']
    
    method = t.get('method', 'GET')
    try:
        if method == 'POST':
            r = s.post(t['url'], params=t['params'], headers=h, timeout=10)
        else:
            r = s.get(t['url'], params=t['params'], headers=h, timeout=10)
        
        print(f"\n  Test {i+1}: {method} {t['url']} params={t['params']}")
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"    JSON keys: {list(data.keys())[:10]}")
                if 'listing' in data:
                    listing = data['listing']
                    details = listing.get('listingDetails', {})
                    print(f"    listingDetails keys: {list(details.keys())[:15]}")
                    # Save the template
                    with open('c:/Users/Dell/Desktop/learn/amazon/backend/template_response.json', 'w') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print("    Template saved!")
                    s.close()
                    exit(0)
            except:
                print(f"    Body: {r.text[:300]}")
        else:
            print(f"    Body: {r.text[:200]}")
    except Exception as e:
        print(f"\n  Test {i+1}: Error: {e}")

print("\nAll tests failed")
s.close()
