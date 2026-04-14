#!/usr/bin/env python
"""Check and fix listing status after server reload killed the polling task"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.database import SessionLocal
from app.models.listing import Listing
from app.services.sp_api_client import SPAPIClient
from datetime import datetime

db = SessionLocal()

# Find the latest listing for product prod-0923F1ECDX0
listing = db.query(Listing).filter(
    Listing.product_id == 'prod-0923F1ECDX0',
    Listing.status == 'processing'
).order_by(Listing.created_at.desc()).first()

if not listing:
    print("No processing listing found", flush=True)
    db.close()
    sys.exit(0)

print(f"Found listing: {listing.id}", flush=True)
print(f"  Status: {listing.status}", flush=True)
print(f"  Stage: {listing.stage}", flush=True)
print(f"  SKU: 00-3A5S-1EYF", flush=True)
print(f"  SP-API Status: {listing.sp_api_status or 'N/A'}", flush=True)

# Poll Amazon directly
client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
result = client.get_listing_item('A1DSHARRBRWYZW', '00-3A5S-1EYF')

status = result.get('status', 'UNKNOWN')
asin = result.get('asin', '')
issues = result.get('issues', [])
errors = [i for i in issues if i.get('severity') == 'ERROR']

print(f"\nAmazon Response:", flush=True)
print(f"  Status: {status}", flush=True)
print(f"  ASIN: {asin}", flush=True)
print(f"  Issues: {len(issues)} (Errors: {len(errors)})", flush=True)

if errors:
    for e in errors:
        print(f"  ❌ {e.get('message', '')[:200]}", flush=True)

# Update the listing
listing.sp_api_status = status
listing.sp_api_last_polled_at = datetime.utcnow()

if status == 'ACTIVE' or asin:
    listing.status = 'success'
    listing.stage = 'active'
    listing.amazon_asin = asin
    listing.completed_at = datetime.utcnow()
    print(f"\n✅ Listing ACTIVE → ASIN {asin}", flush=True)
elif status == 'INVALID' and errors:
    listing.status = 'failed'
    listing.stage = 'rejected'
    listing.error_message = '\n'.join([e.get('message', '')[:200] for e in errors])[:500]
    listing.completed_at = datetime.utcnow()
    print(f"\n❌ Listing INVALID", flush=True)
else:
    print(f"\n⏳ Still processing...", flush=True)

db.commit()

# Show final state
print(f"\nDB Updated:", flush=True)
print(f"  Status: {listing.status}", flush=True)
print(f"  Stage: {listing.stage}", flush=True)
print(f"  ASIN: {listing.amazon_asin or 'N/A'}", flush=True)

db.close()
