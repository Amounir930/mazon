"""
Test script for CookieScraper
"""
import asyncio
from app.services.cookie_scraper import CookieScraper


async def test_products_sync():
    print("=" * 60)
    print("Testing Products Sync")
    print("=" * 60)
    
    scraper = CookieScraper()
    
    # Debug: Get page content
    from app.services.cookie_scraper import CookieScraper
    import asyncio
    from playwright.async_api import async_playwright
    from app.database import SessionLocal
    from app.models.session import Session as AuthSession
    from app.services.session_store import decrypt_data
    import json
    
    # Get session
    db = SessionLocal()
    session = db.query(AuthSession).filter(
        AuthSession.auth_method == "browser",
        AuthSession.is_active == True,
    ).first()
    
    if session:
        cookies = json.loads(decrypt_data(session.cookies_json))
        print(f"Using {len(cookies)} cookies from {session.email}")
        print(f"Country: {session.country_code}")
    db.close()
    
    result = await scraper.sync_products("amazon_eg")
    
    print(f"Success: {result['success']}")
    print(f"Total: {result['total']}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    if result.get('products'):
        print(f"First product: {result['products'][0]}")
    
    await scraper.close()
    return result


async def test_orders_sync():
    print("\n" + "=" * 60)
    print("Testing Orders Sync")
    print("=" * 60)
    
    scraper = CookieScraper()
    result = await scraper.sync_orders("amazon_eg", days=30)
    
    print(f"Success: {result['success']}")
    print(f"Total: {result['total']}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    if result.get('orders'):
        print(f"First order: {result['orders'][0]}")
    
    await scraper.close()
    return result


async def test_inventory_sync():
    print("\n" + "=" * 60)
    print("Testing Inventory Sync")
    print("=" * 60)
    
    scraper = CookieScraper()
    result = await scraper.sync_inventory("amazon_eg")
    
    print(f"Success: {result['success']}")
    print(f"Total: {result['total']}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    if result.get('inventory'):
        print(f"First item: {result['inventory'][0]}")
    
    await scraper.close()
    return result


async def main():
    print("Starting CookieScraper tests...")
    
    # Test products
    await test_products_sync()
    
    # Test orders
    await test_orders_sync()
    
    # Test inventory
    await test_inventory_sync()


if __name__ == "__main__":
    asyncio.run(main())
