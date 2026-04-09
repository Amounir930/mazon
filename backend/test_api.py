"""
Phase 8 — Amazon Integration Test Script
Tests all APIs with mock mode enabled
"""
import requests
import json
import time
import sys

BASE = "http://127.0.0.1:8765/api/v1"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0

def test(name, url, method="GET", data=None, expected_status=200):
    global passed, failed
    try:
        if method == "GET":
            r = requests.get(url)
        elif method == "POST":
            r = requests.post(url, params=data)
        elif method == "POST_JSON":
            r = requests.post(url, json=data)
        elif method == "DELETE":
            r = requests.delete(url)

        ok = r.status_code == expected_status
        status_str = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        if not ok:
            failed += 1
            print(f"  {status_str} {name} — Expected {expected_status}, got {r.status_code}")
            if r.status_code != 200:
                print(f"    Response: {r.text[:200]}")
        else:
            passed += 1
            print(f"  {status_str} {name}")

        return r
    except Exception as e:
        failed += 1
        print(f"  {RED}FAIL{RESET} {name} — {e}")
        return None

def main():
    global passed, failed
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"  {BOLD}Crazy Lister v3.0 — Phase 8 API Tests{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # 1. Health
    r = test("Health Check", "http://127.0.0.1:8765/health")
    if r and r.status_code == 200:
        print(f"    {json.dumps(r.json(), indent=2)}")

    # 2. Amazon Status (no seller yet)
    r = test("Amazon Status (empty)", f"{BASE}/amazon/status")

    # 3. Connect Amazon
    connect_data = {
        "lwa_client_id": "amzn1.app-123",
        "lwa_client_secret": "secret-abc",
        "lwa_refresh_token": "Atzr|mock-token",
        "amazon_seller_id": "A1B2C3D4E5F6G7",
        "display_name": "Test Store",
        "marketplace_id": "ARBP9OOSHTCHU",
    }
    r = test("Amazon Connect", f"{BASE}/amazon/connect", "POST_JSON", connect_data)
    if r and r.status_code == 200:
        print(f"    {json.dumps(r.json(), indent=2, default=str)}")

    # 4. Amazon Status (after connect)
    r = test("Amazon Status (after connect)", f"{BASE}/amazon/status")

    # 5. Verify Connection
    r = test("Amazon Verify", f"{BASE}/amazon/verify", "POST", None, 200)
    if r and r.status_code == 200:
        print(f"    {json.dumps(r.json(), indent=2, default=str)}")

    # 6. Status after verify
    r = test("Amazon Status (after verify)", f"{BASE}/amazon/status")
    if r and r.status_code == 200:
        data = r.json()
        print(f"    is_connected: {data.get('is_connected')}")

    # 7. Create a product
    product_data = {
        "sku": "TEST-001",
        "name": "Test Product Alpha",
        "price": 29.99,
        "quantity": 100,
        "category": "Electronics",
        "brand": "TestBrand",
        "description": "A test product for Phase 8 testing",
        "bullet_points": ["Point 1", "Point 2", "Point 3"],
        "images": ["https://example.com/test.jpg"],
    }
    r = test("Create Product", f"{BASE}/products", "POST_JSON", product_data, 201)
    if r and r.status_code == 201:
        print(f"    Created: {json.dumps(r.json(), indent=2, default=str)}")

    # 8. List products
    r = test("List Products", f"{BASE}/products")
    if r and r.status_code == 200:
        data = r.json()
        print(f"    Total: {data.get('total')}, Items: {len(data.get('items', []))}")

    # 9. Sync from Amazon (mock)
    r = test("Sync Products (mock)", f"{BASE}/sync/sync", "POST")
    if r and r.status_code == 200:
        print(f"    {json.dumps(r.json(), indent=2, default=str)}")

    # 10. List products after sync
    r = test("List Products (after sync)", f"{BASE}/products")
    if r and r.status_code == 200:
        data = r.json()
        print(f"    Total: {data.get('total')}")

    # 11. Submit a listing
    # Get first product ID
    r_products = requests.get(f"{BASE}/products")
    if r_products.status_code == 200:
        items = r_products.json().get("items", [])
        if items:
            product_id = items[0]["id"]
            r = test(f"Submit Listing (product {product_id[:8]}...)",
                     f"{BASE}/tasks/submit-listing", "POST",
                     {"product_id": product_id})
            if r and r.status_code == 200:
                task_id = r.json().get("task_id")
                print(f"    Task ID: {task_id}")

                # Wait for task to complete
                time.sleep(2)
                r_status = test(f"Task Status ({task_id[:8]}...)",
                               f"{BASE}/tasks/{task_id}")
                if r_status and r_status.status_code == 200:
                    print(f"    {json.dumps(r_status.json(), indent=2)}")

    # 12. List listings
    r = test("List Listings", f"{BASE}/listings")
    if r and r.status_code == 200:
        listings = r.json()
        print(f"    Total listings: {len(listings)}")
        for l in listings[:3]:
            print(f"      - {l.get('status')} | ASIN: {l.get('amazon_asin', 'N/A')}")

    # 13. List tasks
    r = test("List Tasks", f"{BASE}/tasks/")
    if r and r.status_code == 200:
        tasks = r.json()
        print(f"    Total tasks: {len(tasks)}")

    # Summary
    print(f"\n{BOLD}{'='*60}{RESET}")
    total = passed + failed
    print(f"  {BOLD}Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET} out of {total}")
    if failed == 0:
        print(f"\n  {GREEN}🎉 All tests passed! Phase 8 is complete.{RESET}")
    else:
        print(f"\n  {YELLOW}⚠️  {failed} test(s) failed. Review above.{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
