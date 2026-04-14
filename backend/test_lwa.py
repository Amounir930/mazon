"""
Quick test of Amazon LWA (Login With Amazon) credentials
"""
import requests
import json

# Read credentials from .env file
env_vars = {}
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, _, value = line.partition('=')
            env_vars[key.strip()] = value.strip()

client_id = env_vars.get('SP_API_CLIENT_ID', '')
client_secret = env_vars.get('SP_API_CLIENT_SECRET', '')
refresh_token = env_vars.get('SP_API_REFRESH_TOKEN', '')

print("=" * 80)
print("🔍 Testing Amazon LWA Credentials")
print("=" * 80)
print(f"Client ID: {client_id[:30]}...")
print(f"Client Secret: {client_secret[:30] if client_secret else 'EMPTY'}...")
print(f"Refresh Token: {refresh_token[:50]}...")
print("=" * 80)

# Try to get access token from LWA
LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

payload = {
    "grant_type": "refresh_token",
    "refresh_token": refresh_token,
    "client_id": client_id,
    "client_secret": client_secret,
}

print("\n🔄 Sending request to Amazon LWA...")
print(f"URL: {LWA_TOKEN_URL}")
print(f"Payload: grant_type=refresh_token, refresh_token={refresh_token[:30]}..., client_id={client_id[:30]}...")

try:
    response = requests.post(LWA_TOKEN_URL, data=payload, timeout=15)
    
    print(f"\n📡 Response Status: {response.status_code}")
    print(f"📡 Response Headers: {dict(response.headers)}")
    print(f"📡 Response Body (first 500 chars):")
    print(response.text[:500])
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! Access token obtained:")
        print(f"   Access Token: {data.get('access_token', 'N/A')[:50]}...")
        print(f"   Token Type: {data.get('token_type', 'N/A')}")
        print(f"   Expires In: {data.get('expires_in', 'N/A')} seconds")
    else:
        print(f"\n❌ FAILED! Status: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Raw error: {response.text}")

except Exception as e:
    print(f"\n❌ Exception occurred: {e}")

print("\n" + "=" * 80)
