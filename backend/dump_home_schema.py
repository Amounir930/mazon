"""
Dump full HOME schema to JSON file for inspection
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

from app.services.sp_api_client import SPAPIClient

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')

path = "/definitions/2020-09-01/productTypes/HOME"
params = {
    "marketplaceIds": "ARBP9OOSHTCHU",
    "requirements": "LISTING",
    "requirementsEnforced": "ENFORCED",
}

result = client._make_request("GET", path, params=params)

# Save full response
output_file = Path(__file__).parent / "home_schema.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Schema saved to: {output_file}")
print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")

# Quick summary
schema = result.get("schema", {})
print(f"\nSchema keys: {list(schema.keys())}")

# Look for required at top level
required = schema.get("required", [])
print(f"Required at root level: {required}")

# Look in properties
properties = schema.get("properties", {})
print(f"\nTotal properties: {len(properties)}")

# Find anything with "plug", "voltage", "frequency", "power" in the name
print("\n🔍 Power-related properties:")
for name, prop in properties.items():
    if any(kw in name.lower() for kw in ['plug', 'voltage', 'frequency', 'power', 'hertz', 'watt']):
        print(f"  - {name}")
        print(f"    Title: {prop.get('title', 'N/A')}")
        print(f"    Type: {prop.get('type', 'N/A')}")
        print(f"    Required: {prop.get('required', False)}")
        
        # Check nested for enum values
        if 'items' in prop:
            print(f"    Items type: {prop['items'].get('type', 'N/A')}")
