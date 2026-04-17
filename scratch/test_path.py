import os
import sys

file_path = r"c:\Users\Dell\Desktop\learn\amazon\backend\app\api\settings_routes.py"
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(file_path))), '.env')
print(f"File: {file_path}")
print(f"Env Path: {env_path}")
print(f"Exists: {os.path.exists(env_path)}")
