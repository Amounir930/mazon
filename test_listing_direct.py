"""
Direct test of ListingSubmitter - runs outside the server for debugging
"""
import asyncio
import json
import logging
import sys
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}")

from backend.app.services.listing_submitter import ListingSubmitter

async def test_listing_submit():
    print("=" * 60)
    print("DIRECT TEST: ListingSubmitter")
    print("=" * 60)

    submitter = ListingSubmitter(country_code="eg", debug=True)

    product_data = {
        "sku": "TEST-DIRECT-001",
        "name": "Direct Test Product - Electric Mixer",
        "description": "Test product for direct submission via Playwright",
        "price": 200.0,
        "quantity": 10,
        "brand": "Generic",
        "ean": "1234567890123",
        "condition": "New",
        "fulfillment_channel": "MFN",
        "product_type": "HOME_ORGANIZERS_AND_STORAGE",
        "bullet_points": ["Test bullet point"],
        "manufacturer": "Generic",
        "model_number": "TM-001",
        "country_of_origin": "CN",
    }

    print(f"\nSubmitting product: {product_data['sku']}")
    print(f"Name: {product_data['name']}")
    print(f"Price: {product_data['price']} EGP")
    print(f"Quantity: {product_data['quantity']}")
    print("\nStarting submission...\n")

    try:
        result = await submitter.submit_listing(product_data)
        print(f"\n{'=' * 60}")
        print(f"RESULT: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"{'=' * 60}")
    except Exception as e:
        print(f"\nEXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await submitter.close()

if __name__ == "__main__":
    asyncio.run(test_listing_submit())
