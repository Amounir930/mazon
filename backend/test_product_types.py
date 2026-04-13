import json
from http.cookiejar import CookieJar, Cookie
from curl_cffi import requests as cffi_r
from app.database import SessionLocal
from app.models.session import Session as AuthSession
from app.services.session_store import decrypt_data

db = SessionLocal()
sess = db.query(AuthSession).filter(AuthSession.auth_method=='browser', AuthSession.is_active==True).first()
if not sess:
    print("No active session!")
    exit(1)
cookies = json.loads(decrypt_data(sess.cookies_json))
country = sess.country_code or 'eg'
db.close()

print(f"Session: {len(cookies)} cookies, country={country}")

product_types = [
    'HOME_ORGANIZERS_AND_STORAGE',
    'PRODUCT',
    'HOME',
    'HOME_IMPROVEMENT',
    'KITCHEN',
    'SMALL_APPLIANCES',
    'GENERAL_PRODUCT',
]

base = 'https://sellercentral.amazon.eg'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
}

jar = CookieJar()
for c in cookies:
    name = c.get('name','')
    val = c.get('value','')
    if name and val is not None:
        try:
            http_c = Cookie(0, name, str(val), None, False, '.amazon.eg', True, True, c.get('path','/'), True, False, None, True, None, None, {'HttpOnly': c.get('httpOnly')}, False)
            jar.set_cookie(http_c)
        except Exception as e:
            print(f"  Skip cookie {name}: {e}")

s = cffi_r.Session(impersonate='chrome131')
s.cookies = jar

for pt in product_types:
    params = {'productType': pt, 'listingLanguageCode': 'ar_AE'}
    url = f'{base}/abis/ajax/create-listing'
    try:
        r = s.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            try:
                data = r.json()
                print(f'OK {pt}: keys={list(data.keys())[:5]}')
                if 'listing' in data:
                    listing = data['listing']
                    details = listing.get('listingDetails', {})
                    print(f'   listingDetails: {list(details.keys())[:10]}')
                s.close()
                exit(0)
            except:
                print(f'WARN {pt}: 200 but not JSON, body={r.text[:200]}')
        else:
            print(f'FAIL {pt}: {r.status_code}, body={r.text[:150]}')
    except Exception as e:
        print(f'ERR {pt}: {e}')

print("All product types failed")
s.close()
