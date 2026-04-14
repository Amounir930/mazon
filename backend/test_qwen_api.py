#!/usr/bin/env python
"""Test Qwen API connection and basic generation"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import httpx
import json

api_key = os.getenv("QWEN_API_KEY", "")
print(f"QWEN_API_KEY: {api_key[:20]}..." if api_key else "QWEN_API_KEY: NOT SET")

if not api_key:
    print("❌ QWEN_API_KEY not found in .env")
    sys.exit(1)

# Test 1: Try portal.qwen.ai/v1
print("\n🧪 Test 1: portal.qwen.ai/v1/chat/completions")
try:
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            "https://portal.qwen.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-max",
                "messages": [{"role": "user", "content": "Say 'Hello' in JSON"}],
                "response_format": {"type": "json_object"},
            },
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:300]}")
        if resp.status_code == 200:
            print("  ✅ SUCCESS!")
        else:
            print("  ❌ FAILED")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: Try dashscope API (alternative)
print("\n🧪 Test 2: dashscope.aliyuncs.com (DashScope API)")
try:
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-plus",
                "messages": [{"role": "user", "content": 'Say {"hello":"world"} in JSON only'}],
                "response_format": {"type": "json_object"},
            },
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:300]}")
        if resp.status_code == 200:
            print("  ✅ SUCCESS!")
        else:
            print("  ❌ FAILED")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: Try OpenAI-compatible Qwen endpoint
print("\n🧪 Test 3: api.qwen.ai/v1/chat/completions")
try:
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            "https://api.qwen.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-plus",
                "messages": [{"role": "user", "content": 'Return JSON: {"test":"ok"}'}],
            },
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:300]}")
        if resp.status_code == 200:
            print("  ✅ SUCCESS!")
        else:
            print("  ❌ FAILED")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 50)
print("Tests complete. Check which endpoint works.")
