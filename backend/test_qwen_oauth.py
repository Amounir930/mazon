#!/usr/bin/env python
"""Find working Qwen model with OAuth token"""
import os, httpx, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

token = os.getenv("QWEN_API_KEY", "")
base = "https://portal.qwen.ai/v1"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

# Try listing available models
print("📋 Listing available models...", flush=True)
try:
    r = httpx.get(f"{base}/models", headers=headers, timeout=10.0)
    print(f"Status: {r.status_code}", flush=True)
    if r.status_code == 200:
        data = r.json()
        models = data.get("data", [])
        print(f"Found {len(models)} models:", flush=True)
        for m in models:
            mid = m.get("id", "")
            print(f"  - {mid}", flush=True)
        if models:
            # Try first available model
            first_model = models[0]["id"]
            print(f"\n🧪 Testing first model: {first_model}", flush=True)
            r2 = httpx.post(
                f"{base}/chat/completions",
                headers=headers,
                json={"model": first_model, "messages": [{"role": "user", "content": "Say ok"}]},
                timeout=15.0
            )
            print(f"Status: {r2.status_code}", flush=True)
            print(f"Response: {r2.text[:300]}", flush=True)
    else:
        print(f"Error: {r.text[:200]}", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)

# Try different model names that Qwen portal might support
print("\n🧪 Trying alternative model names...", flush=True)
alt_models = [
    "qwen-omni-turbo",
    "qwen-vl-plus", 
    "deepseek-r1",
    "qwq",
    "qwen2.5-72b-instruct",
    "qwen2.5-coder-32b-instruct",
]
for model in alt_models:
    try:
        r = httpx.post(
            f"{base}/chat/completions",
            headers=headers,
            json={"model": model, "messages": [{"role": "user", "content": "Say ok"}]},
            timeout=10.0
        )
        if r.status_code == 200:
            print(f"✅ {model}: WORKING!", flush=True)
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"   Response: {content[:100]}", flush=True)
            break
        else:
            err = r.json().get("error", {}).get("message", "")[:80]
            print(f"❌ {model}: {r.status_code} - {err}", flush=True)
    except Exception as e:
        print(f"❌ {model}: {e}", flush=True)
