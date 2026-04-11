import niquests, json, time

time.sleep(3)

print("Testing browser-login endpoint...")
try:
    r = niquests.post(
        'http://127.0.0.1:8765/api/v1/auth/browser-login',
        json={'email': 'test@example.com', 'password': 'test123', 'country_code': 'eg'},
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
