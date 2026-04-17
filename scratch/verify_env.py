import os
import sys
from pathlib import Path

# Mocking the get_env_path logic from the routes
def get_env_path_test(file_path):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(file_path))), '.env')

settings_file = r"c:\Users\Dell\Desktop\learn\amazon\backend\app\api\settings_routes.py"
env_path = get_env_path_test(settings_file)

print(f"Calculated Env Path: {env_path}")
print(f"File Exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("--- Contents of .env (first few lines) ---")
    with open(env_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < 10:
                # Masking sensitive info
                if '=' in line:
                    key, val = line.partition('=')[::2]
                    print(f"{key}={val[:5]}...")
                else:
                    print(line.strip())
    print("------------------------------------------")
else:
    print("ERROR: .env not found at calculated path!")
