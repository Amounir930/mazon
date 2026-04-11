"""Test the browser login script directly"""
import os
import json
import tempfile
import subprocess
import time

output_file = os.path.join(tempfile.gettempdir(), "browser_result.json")

env = os.environ.copy()
env.update({
    "BROWSER_EMAIL": "test@example.com",
    "BROWSER_PASSWORD": "test123",
    "BROWSER_COUNTRY": "eg",
    "BROWSER_OTP": "",
    "BROWSER_OUTPUT": output_file,
})

print("Starting browser script...")
proc = subprocess.Popen(
    ["python", "-u", "c:/Users/Dell/Desktop/learn/amazon/backend/app/services/browser_login_script.py"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

# استنى النتيجة
for i in range(20):
    time.sleep(1)
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        break
else:
    proc.terminate()
    print("TIMEOUT")
