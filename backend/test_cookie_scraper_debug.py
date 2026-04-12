"""
Enhanced test for CookieScraper with debug mode
"""
import asyncio
from app.services.cookie_scraper import CookieScraper


async def test_with_debug():
    print("=" * 80)
    print("Testing CookieScraper with DEBUG mode")
    print("=" * 80)
    
    scraper = CookieScraper(debug=True)
    
    # Test products
    print("\n📦 Testing Products Sync...")
    result = await scraper.sync_products("amazon_eg")
    
    print(f"✅ Success: {result['success']}")
    print(f"📊 Total: {result['total']}")
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
    if result.get('products'):
        print(f"📝 First product: {result['products'][0]}")
    
    await scraper.close()
    
    print("\n" + "=" * 80)
    print("Check debug HTML files in:")
    print("  %TEMP%/crazy_lister/sync_debug/")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_with_debug())
