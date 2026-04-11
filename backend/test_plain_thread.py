"""Test sync Playwright in plain thread (no asyncio)"""
import threading, queue, time
from playwright.sync_api import sync_playwright

result_q = queue.Queue()

def worker():
    print("Thread started")
    try:
        pw = sync_playwright().start()
        print("Playwright started")
        b = pw.chromium.launch(headless=True)
        p = b.new_page()
        p.goto("https://example.com", timeout=10000)
        print(f"Title: {p.title()}")
        b.close()
        pw.stop()
        result_q.put({"success": True, "title": p.title()})
    except Exception as e:
        result_q.put({"success": False, "error": str(e)})

t = threading.Thread(target=worker, daemon=True)
t.start()

try:
    result = result_q.get(timeout=20)
    print(f"Result: {result}")
except queue.Empty:
    print("TIMEOUT")
    
print("DONE")
