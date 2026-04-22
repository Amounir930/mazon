import requests
import json
import time
from datetime import datetime, timedelta

# SP-API Credentials from your .env
CLIENT_ID = "amzn1.application-oa2-client.bc622c264b9c4158a55a8967ce93e1cc"
CLIENT_SECRET = "amzn1.oa2-cs.v1.0764260f6ec7be3a1d6d14c6a5bca5bb90fece2007a5f81b32d98f4c582f5f3e"
REFRESH_TOKEN = "Atzr|IwEBIGXWrHaDMOftZcNNd7a533cmGj2MVpSu7LA7sHMHFXctvmpEYRQL4T4oBrX6PN-B5_SVnUyLZc9kaK993dBznMFZl_Hs6N2G_qMEngEhutJOzoo5sXXiqJUIEGqIK1pqnoE90av97tPFhyn67m2oCYD0CX3sHOafXKcTY9XP5MQLIg-7eOKehMm9nNeF2eegMWfAHV9Lxu-vCtG6edM_fgPZfFyLXEcgQJ2fla6ardKnnmN2Ofh-HfEEIdQWcq3Kx6_-RFrRi_qeojEsXdHRf9mP2feA229HJSUKXkYDy-uY2F1pF6Tdh5q-EbKahZRcvqhTki_GQqXodEPm6knAkZTW"
MARKETPLACE_ID = "ARBP9OOSHTCHU"
REGION_ENDPOINT = "sellingpartnerapi-eu.amazon.com" # for EG/EU

def get_lwa_token():
    print("🔄 Step 1: Requesting LWA Access Token...")
    url = "https://api.amazon.com/auth/o2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ LWA Token obtained successfully! (Starts with: {token[:10]}...)")
        return token
    else:
        print(f"❌ Failed to get LWA Token: {response.status_code}")
        print(response.text)
        return None

def test_sales_api(access_token):
    print("\n🔄 Step 2: Testing Sales API (orderMetrics)...")
    
    # Define time interval (Last 24 hours)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    
    # Format: 2024-01-01T00:00:00Z--2024-01-02T00:00:00Z
    interval = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}--{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    url = f"https://{REGION_ENDPOINT}/sales/v1/orderMetrics"
    params = {
        "marketplaceIds": MARKETPLACE_ID,
        "interval": interval,
        "granularity": "Day"
    }
    headers = {
        "x-amz-access-token": access_token,
        "Accept": "application/json"
    }
    
    print(f"📡 Requesting: {url}")
    print(f"Interval: {interval}")
    
    response = requests.get(url, headers=headers, params=params)
    
    print(f"\n📥 Amazon Response Code: {response.status_code}")
    
    if response.status_code == 200:
        print("🎉 SUCCESS! Sales data retrieved successfully.")
        print(json.dumps(response.json(), indent=2))
    elif response.status_code == 403:
        print("🚫 403 FORBIDDEN: Access is still denied.")
        print("Possible reason: 'Inventory and Order Tracking' role is NOT active or Re-Auth is missing.")
        print(response.text)
    else:
        print(f"⚠️ Unexpected Response: {response.status_code}")
        print(response.text)

def test_catalog_api(access_token):
    print("\n🔄 Step 3: Testing Catalog API (Search)...")
    url = f"https://{REGION_ENDPOINT}/catalog/2022-04-01/items"
    params = {
        "marketplaceIds": MARKETPLACE_ID,
        "keywords": "iPhone", # Generic high-volume keyword
        "includedData": "summaries,salesRanks"
    }
    headers = {
        "x-amz-access-token": access_token,
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers, params=params)
    print(f"📥 Catalog Response Code: {response.status_code}")
    
    if response.status_code == 200:
        items = response.json().get("items", [])
        print(f"🎉 SUCCESS! Found {len(items)} items in catalog.")
        if items:
            print(f"Sample Item: {items[0].get('summaries', [{}])[0].get('itemName')}")
    else:
        print(f"🚫 Catalog API Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("=== Amazon SP-API Direct Connectivity Test ===\n")
    token = get_lwa_token()
    if token:
        test_sales_api(token)
        test_catalog_api(token)
    print("\n=== Test Finished ===")
