#!/usr/bin/env python
"""Test Cerebras API"""
import os, httpx
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

api_key = os.getenv("QWEN_API_KEY", "")
print(f"Key: {len(api_key)} chars")

url = "https://api.cerebras.ai/v1/chat/completions"
print(f"URL: {url}")

r = httpx.post(
    url,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json={
        "model": "llama3.1-8b",
        "messages": [{"role": "user", "content": 'Return ONLY JSON: {"test":"ok"}'}],
    },
    timeout=15.0
)

print(f"Status: {r.status_code}")
print(f"Body: {r.text[:600]}")

if r.status_code == 200:
    data = r.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"Content: {content}")
    print("SUCCESS")
else:
    print("FAILED")
