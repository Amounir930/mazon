#!/usr/bin/env python
"""Test AI Product Generation via Cerebras API"""
import asyncio, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

async def test():
    from app.services.ai_product_assistant import AIProductAssistant
    
    assistant = AIProductAssistant()
    
    print("🧪 Testing AI generation with Cerebras API...", flush=True)
    print(f"Model: llama3.1-8b", flush=True)
    print(f"Endpoint: api.cerebras.ai", flush=True)
    print("", flush=True)
    
    try:
        result = await assistant.generate_products(
            name="خلاط كهربائي 300 واط",
            specs="5 سرعات، ستانلس ستيل، سهل التنظيف",
            copies=2
        )
        
        print("✅ SUCCESS!", flush=True)
        print(f"Base product:", flush=True)
        print(f"  Brand: {result.base_product.brand}", flush=True)
        print(f"  Type: {result.base_product.product_type}", flush=True)
        print(f"  Price: {result.base_product.price} EGP", flush=True)
        print(f"  Bullets AR: {len(result.base_product.bullet_points_ar)} items", flush=True)
        print(f"  Keywords: {len(result.base_product.keywords)} items", flush=True)
        
        print(f"\nVariants: {len(result.variants)}", flush=True)
        for v in result.variants:
            print(f"\n  [{v.variant_number}] SKU={v.suggested_sku}", flush=True)
            print(f"      AR: {v.name_ar[:60]}", flush=True)
            print(f"      EN: {v.name_en[:60]}", flush=True)
        
    except Exception as e:
        print(f"❌ FAILED: {e}", flush=True)
        import traceback
        traceback.print_exc()

asyncio.run(test())
