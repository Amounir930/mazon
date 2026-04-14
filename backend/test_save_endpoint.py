"""
Test the save_sp_credentials endpoint directly
"""
import requests
import json

BASE_URL = "http://localhost:8766/api/v1"

data = {
    "seller_id": "A1DSHARRBRWYZW",
    "client_id": "amzn1.application-oa2-client.bc622c264b9c4158a55a8967ce93e1cc",
    "client_secret": "amzn1.oa2-cs.v1.83c5d141906aa1fc630f88b5870367d541bbb4162ce64cf8f1ad1721e6bcef04",
    "refresh_token": "Atzr|IwEBIH-umwf-JKNrQkySRMU_nLNDorsC-8xytRE2Vit0w63_VdeyK5SOAA3poCC8301zmOzJxCodx9d4zyoAR6e-ikIeF_8WC4IH7MYRKUFqA5V4doC9qpVXOVTJMLr3wdaz3F1MOJI8uiZRxxkRk2W1UeLohX-7E0WzpiGeWWFPz3ymMQ-FbPrNrafEfuDsYF2MQvGiNKklZr1A_FS1MgypAIjQNlcrTYHheyTYdSnMCWtAwIzdPxlYbYOO4VFX3kYc3LXpOxwaJvrJi4AjVY1aAM-W455zjW5Qh8MvaWYx0sjHFhSX8mF-dSWpYcpxzyeTfVa0rlLpyph5tftvmJS35c6r"
}

print("=" * 80)
print("🔍 Testing /settings/sp-credentials endpoint")
print("=" * 80)
print(f"URL: {BASE_URL}/settings/sp-credentials")
print(f"Payload: seller_id={data['seller_id']}, client_id={data['client_id'][:30]}...")
print("=" * 80)

try:
    response = requests.post(f"{BASE_URL}/settings/sp-credentials", json=data, timeout=30)
    
    print(f"\n📡 Response Status: {response.status_code}")
    print(f"📡 Response Headers: {dict(response.headers)}")
    print(f"\n📡 Response Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "=" * 80)
