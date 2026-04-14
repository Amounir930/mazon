#!/usr/bin/env python
"""Test new csk- API key"""
import os, httpx, sys

new_key = "csk-khfrfcrvfk2tv2de9e4355xd29m24cdt4xf489trcmxj4xpy"
print(f"Key: {new_key[:15]}... ({len(new_key)} chars)", flush=True)

endpoints = [
    ("portal.qwen.ai/v1", "qwen-plus"),
    ("dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    ("dashscope.aliyuncs.com/compatible-mode/v1", "qwen-turbo"),
]

for base, model in endpoints:
    try:
        url = f"https://{base}/chat/completions"
        print(f"\nTesting: {base}/{model}", flush=True)
        r = httpx.post(
            url,
            headers={"Authorization": f"Bearer {new_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": 'Say {"ok":true} in JSON'}]},
            timeout=15.0
        )
        status = "✅" if r.status_code == 200 else "❌"
        print(f"  {status} Status: {r.status_code}", flush=True)
        print(f"  Response: {r.text[:200]}", flush=True)
        
        if r.status_code == 200:
            print(f"\n🎉 WORKING ENDPOINT FOUND!", flush=True)
            print(f"  Base URL: {base}", flush=True)
            print(f"  Model: {model}", flush=True)
            
            # Update .env
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            with open(env_path, "r") as f:
                env_content = f.read()
            
            old_key_line = [l for l in env_content.split("\n") if l.startswith("QWEN_API_KEY=")]
            if old_key_line:
                env_content = env_content.replace(old_key_line[0], f"QWEN_API_KEY={new_key}")
            
            with open(env_path, "w") as f:
                f.write(env_content)
            print(f"  .env updated!", flush=True)
            break
    except Exception as e:
        print(f"  ❌ Error: {e}", flush=True)
