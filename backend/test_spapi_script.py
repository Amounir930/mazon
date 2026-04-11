"""Test SP-API standalone script"""
import os
import json
import tempfile
import subprocess
import time

output_file = os.path.join(tempfile.gettempdir(), "spapi_result.json")

env = os.environ.copy()
env.update({
    "SPAPI_OUTPUT": output_file,
    "SPAPI_CLIENT_ID": "amzn1.application-oa2-client.bc622c264b9c4158a55a8967ce93e1cc",
    "SPAPI_CLIENT_SECRET": "amzn1.oa2-cs.v1.83c5d141906aa1fc630f88b5870367d541bbb4162ce64cf8f1ad1721e6bcef04",
    "SPAPI_REFRESH_TOKEN": "Atzr|IwEBIA4A4xmWNxFTeais7mF3dC6OpShVZoIP0U4wIAATo-em7oLwEZ7emG1wAtAA-Y7zwsvUJ-q3Ndld9aQ8OeackmDJiyHZjH7bY9coobaFfCPODgGQTophDzL-igWSz3mN11gOWKAKI5yLeqqSD9x7a9qUK71ZqdT1qxQ0YZAEwASOJFnbDN0QU1CS_bJr9cSMowwtpOshCfBNoULZhVjNpi84JdIL06TXTubDyghy2UlfSz-N4lYU1TWMeKKD-NPHJYtGoR7SS7XVbcDVr5DaO_EC1xRLKRYzkzoyKnv41DQ2BF3_cBvAwOj3zLZuanl6UUIzvl8wRrrpEmNaYXeO4TA2",
    "AWS_ACCESS_KEY_ID": "AKIA5AJTOJBXTBC7UQ72",
    "AWS_SECRET_ACCESS_KEY": "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",
    "SPAPI_MARKETPLACE_ID": "ARBP9OOSHTCHU",
})

print("Starting SP-API script...")
proc = subprocess.Popen(
    ["python", "-u", "c:/Users/Dell/Desktop/learn/amazon/backend/app/services/sp_api_login_script.py"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

# Wait for result
for i in range(20):
    time.sleep(1)
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        break
    # Check if process is still running
    if proc.poll() is not None:
        print(f"Process exited with code: {proc.returncode}")
        break
else:
    proc.terminate()
    print("TIMEOUT")
