#!/usr/bin/env python
"""Test payload building without network calls"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Build minimal product data
product_data = {
    'sku': '00-3A5S-1EYF',
    'name': 'Test Product',
    'description': 'Test',
    'brand': 'Generic',
    'manufacturer': 'Generic',
    'model_number': '00-3A5S-1EYF',
    'ean': '1245768907654',
    'upc': '',
    'price': 350.0,
    'quantity': 10,
    'condition': 'New',
    'country_of_origin': 'CN',
    'product_type': 'HOME_ORGANIZERS_AND_STORAGE',
    'bullet_points': [],
    'browse_node_id': '21863799031',
    'merchant_suggested_asin': '00-3A5S-1EYF',
}

print("Building payload...", flush=True)

# Import and build payload
from app.services.sp_api_client import SPAPIClient
client = SPAPIClient()
payload = client._build_listing_payload(product_data)

# Print key fields
attrs = payload.get('attributes', {})
print(f'externally_assigned_product_identifier:', flush=True)
print(f'  {attrs.get("externally_assigned_product_identifier")}', flush=True)
print(f'merchant_suggested_asin:', flush=True)
print(f'  {attrs.get("merchant_suggested_asin")}', flush=True)
print(f'productType: {payload.get("productType")}', flush=True)
print(f'requirements: {payload.get("requirements")}', flush=True)
print("Done!", flush=True)
