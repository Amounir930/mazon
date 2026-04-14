#!/usr/bin/env python
"""Direct Amazon SP-API query - get FULL response for last accepted listing"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.database import SessionLocal
from app.models.listing import Listing
from app.services.sp_api_client import SPAPIClient

db = SessionLocal()

# Get the latest listing
listing = db.query(Listing).filter(
    Listing.product_id == 'prod-0923F1ECDX0'
).order_by(Listing.created_at.desc()).first()

if not listing:
    print("No listing found", flush=True)
    db.close()
    sys.exit(0)

print("=" * 70, flush=True)
print("📋 LISTING RECORD (from DB)", flush=True)
print("=" * 70, flush=True)
print(f"  ID:             {listing.id}", flush=True)
print(f"  Status:         {listing.status}", flush=True)
print(f"  Stage:          {listing.stage}", flush=True)
print(f"  SP-API Status:  {listing.sp_api_status or 'N/A'}", flush=True)
print(f"  Amazon ASIN:    {listing.amazon_asin or 'N/A'}", flush=True)
print(f"  Error Message:  {listing.error_message or 'N/A'}", flush=True)
print(f"  Created:        {listing.created_at}", flush=True)
print(f"  Submitted:      {listing.submitted_at}", flush=True)
print(f"  Completed:      {listing.completed_at or 'N/A'}", flush=True)

# Query Amazon directly
print("\n" + "=" * 70, flush=True)
print("🔍 AMAZON SP-API DIRECT QUERY", flush=True)
print("=" * 70, flush=True)

client = SPAPIClient(marketplace_id='ARBP9OOSHTCHU', country_code='eg')
result = client.get_listing_item('A1DSHARRBRWYZW', '00-3A5S-1EYF')

print(f"\n📦 Full Amazon Response:", flush=True)
print(json.dumps(result, indent=2, default=str, ensure_ascii=False), flush=True)

# Parse the response
status = result.get('status', 'UNKNOWN')
asin = result.get('asin', '')
issues = result.get('issues', [])
summaries = result.get('summaries', [])
errors = [i for i in issues if i.get('severity') == 'ERROR']
warnings = [i for i in issues if i.get('severity') == 'WARNING']

print("\n" + "=" * 70, flush=True)
print("📊 INTERPRETED STATUS", flush=True)
print("=" * 70, flush=True)
print(f"  Amazon Status:     {status}", flush=True)
print(f"  ASIN Assigned:     {'Yes - ' + asin if asin else 'No'}", flush=True)
print(f"  Issues:            {len(issues)} (Errors: {len(errors)}, Warnings: {len(warnings)})", flush=True)
print(f"  Summaries:         {len(summaries)}", flush=True)

if errors:
    print(f"\n❌ ERRORS:", flush=True)
    for e in errors:
        print(f"   - {e.get('message', '')[:300]}", flush=True)

if warnings:
    print(f"\n⚠️  WARNINGS:", flush=True)
    for w in warnings:
        print(f"   - {w.get('message', '')[:300]}", flush=True)

if summaries:
    print(f"\n📝 SUMMARIES:", flush=True)
    for s in summaries:
        print(f"   - Marketplace: {s.get('marketplaceId', 'N/A')}", flush=True)
        print(f"   - ASIN: {s.get('asin', 'N/A')}", flush=True)
        print(f"   - Status: {s.get('status', 'N/A')}", flush=True)

# Determine actual state
print("\n" + "=" * 70, flush=True)
print("🎯 FINAL DETERMINATION", flush=True)
print("=" * 70, flush=True)

if asin or (summaries and summaries[0].get('asin')):
    final_asin = asin or summaries[0].get('asin', '')
    print(f"✅ LISTING IS ACTIVE — ASIN: {final_asin}", flush=True)
    # Update DB
    listing.status = 'success'
    listing.stage = 'active'
    listing.amazon_asin = final_asin
    from datetime import datetime
    listing.completed_at = datetime.utcnow()
    listing.sp_api_status = status
    db.commit()
    print(f"   DB updated: status=success, asin={final_asin}", flush=True)
elif errors:
    print(f"❌ LISTING IS INVALID — Rejected by Amazon", flush=True)
    listing.status = 'failed'
    listing.stage = 'rejected'
    listing.error_message = '\n'.join([e.get('message', '')[:200] for e in errors])[:500]
    from datetime import datetime
    listing.completed_at = datetime.utcnow()
    listing.sp_api_status = status
    db.commit()
    print(f"   DB updated: status=failed", flush=True)
elif status == 'UNKNOWN' or status == 'NOT_FOUND':
    print(f"⏳ LISTING NOT FOUND ON AMAZON", flush=True)
    print(f"   Possible causes:", flush=True)
    print(f"   1. The listing was cancelled/removed after ACCEPTED", flush=True)
    print(f"   2. Amazon rejected it silently (background rejection)", flush=True)
    print(f"   3. The SKU was never actually created (ACCEPTED = received, not approved)", flush=True)
    print(f"", flush=True)
    print(f"   💡 ACCEPTED means Amazon received the data — NOT that it's live!", flush=True)
    # Update DB
    listing.status = 'failed'
    listing.stage = 'cancelled'
    listing.error_message = 'Listing not found on Amazon — may have been cancelled or rejected silently'
    from datetime import datetime
    listing.completed_at = datetime.utcnow()
    listing.sp_api_status = status
    db.commit()
    print(f"   DB updated: status=failed, stage=cancelled", flush=True)
else:
    print(f"⏳ STILL PROCESSING — Status: {status}", flush=True)

db.close()
