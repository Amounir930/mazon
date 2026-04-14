#!/usr/bin/env python
"""Find working Qwen model"""
import os, httpx, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

api_key = os.getenv("QWEN_API_KEY", "")
print(f"Key loaded: {len(api_key)} chars")

# Models to try
models = ["qwen-plus", "qwen-turbo", "qwen2.5-plus", "qwen2.5-turbo", "qwen-max-latest", "qwen-long"]

for model in models:
    try:
        r = httpx.post(
            "https://portal.qwen.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "Say ok"}]},
            timeout=10.0
        )
        if r.status_code == 200:
            print(f"✅ {model}: WORKING!")
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"   Response: {content[:100]}")
            # Test JSON mode
            r2 = httpx.post(
                "https://portal.qwen.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": 'Return JSON only: {"test":1}'}],
                    "response_format": {"type": "json_object"},
                },
                timeout=10.0
            )
            if r2.status_code == 200:
                print(f"   JSON mode: ✅")
                json_data = r2.json()
                json_content = json_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"   JSON response: {json_content[:100]}")
            else:
                print(f"   JSON mode: ❌ ({r2.status_code})")
            break
        else:
            print(f"❌ {model}: {r.status_code} — {r.text[:100]}")
    except Exception as e:
        print(f"❌ {model}: {e}")
