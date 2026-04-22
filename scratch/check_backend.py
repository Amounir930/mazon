import requests
import sys

try:
    r = requests.get('http://127.0.0.1:8765/', timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Headers: {r.headers}")
    print(f"Content (first 500 chars):\n{r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
