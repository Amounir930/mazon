"""Test Playwright directly in standalone script"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

print(f"PID: {os.getpid()}", flush=True)
print("Starting Playwright...", flush=True)

pw = sync_playwright().start()
print("Playwright started", flush=True)

b = pw.chromium.launch(headless=True)
print("Browser launched!", flush=True)

p = b.new_page()
p.goto("https://example.com", wait_until="domcontentloaded", timeout=10000)
print(f"Title: {p.title()}", flush=True)

b.close()
pw.stop()
print("DONE!", flush=True)
