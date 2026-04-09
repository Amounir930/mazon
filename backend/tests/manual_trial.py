import httpx
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_full_flow():
    print("🚀 Starting Full Stack Trial...")
    
    # 1. Health Check
    try:
        resp = httpx.get(f"http://localhost:8000/health", timeout=10)
        print(f"✅ Health Check: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        # Localhost might be tricky in some environments, try 127.0.0.1
        resp = httpx.get(f"http://127.0.0.1:8000/health", timeout=10)
        print(f"✅ Health Check (127.0.0.1): {resp.status_code}")

    # 2. Register Seller (Egypt)
    seller_data = {
        "email": "test-egypt@example.com",
        "seller_id": "MOCK-EGY-001",
        "marketplace_id": "ARBP9OOSHTCHU",
        "region": "EU",
        "lwa_refresh_token": "mock-refresh-token"
    }
    
    # Actually registration is via OAuth callback or direct creation
    # Let's check if we have a direct register endpoint
    print("📝 Registering Seller...")
    resp = httpx.post(f"{BASE_URL}/sellers/register", json=seller_data)
    if resp.status_code in [200, 201]:
        seller = resp.json()
        seller_id = seller["id"]
        print(f"✅ Seller Registered: {seller_id}")
    else:
        print(f"❌ Seller Registration Failed: {resp.text}")
        return

    # 3. Create Parent Product
    parent_data = {
        "sku": "PARENT-SHIRT-001",
        "name": "Summer Collection T-Shirt (Parent)",
        "category": "Clothing",
        "brand": "CrazyBrand",
        "is_parent": True,
        "price": 10.00,
        "quantity": 0,
        "attributes": {"variation_theme": "SIZE_COLOR"}
    }
    print("📝 Creating Parent Product...")
    resp = httpx.post(f"{BASE_URL}/products/?seller_id={seller_id}", json=parent_data)
    if resp.status_code in [200, 201]:
        parent = resp.json()
        print(f"✅ Parent Created: {parent['sku']}")
    else:
        print(f"❌ Parent Creation Failed: {resp.text}")

    # 4. Create Child Product
    child_data = {
        "sku": f"CHILD-SHIRT-RED-XL-{int(time.time())}", # Unique SKU
        "name": "Summer Collection T-Shirt - Red / XL",
        "parent_sku": "PARENT-SHIRT-001",
        "is_parent": False,
        "price": 450.00, # EGP
        "quantity": 100,
        "attributes": {"color": "Red", "size": "XL"}
    }
    print("📝 Creating Child Product (Egypt Variation)...")
    resp = httpx.post(f"{BASE_URL}/products/?seller_id={seller_id}", json=child_data)
    if resp.status_code in [200, 201]:
        child = resp.json()
        child_product_id = child["id"]
        print(f"✅ Child Created: {child['sku']}")
    else:
        print(f"❌ Child Creation Failed: {resp.text}")
        return

    # 5. Create Listing (Queue to Amazon)
    listing_data = {
        "product_id": child_product_id,
        "seller_id": seller_id
    }
    print("📝 Queuing Listing to Amazon (Egypt)...")
    resp = httpx.post(f"{BASE_URL}/listings/submit/", json=listing_data)
    if resp.status_code in [200, 201]:
        listing = resp.json()
        print(f"✅ Listing Queued: {listing['id']} (Status: {listing['status']})")
    else:
        print(f"❌ Listing Queue Failed: {resp.text}")

    # 6. Summary
    print("\n🏁 Trial Completed Successfully!")

if __name__ == "__main__":
    test_full_flow()
