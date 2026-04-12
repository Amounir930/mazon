"""
Test script to check if window.get_cookies() works with PyWebView
"""
import webview
import time

def test_cookies():
    result = {"cookies": None}
    
    def on_loaded(window):
        try:
            url = window.get_current_url()
            print(f"Page loaded: {url}")
            
            # Try get_cookies()
            try:
                print("Trying window.get_cookies()...")
                cookies = window.get_cookies()
                print(f"get_cookies() returned: {type(cookies)}")
                print(f"get_cookies() result: {cookies}")
                if cookies:
                    print(f"Got {len(cookies)} cookies from native API")
                    result["cookies"] = cookies
                else:
                    print("get_cookies() returned empty, trying document.cookie...")
            except Exception as e:
                print(f"get_cookies() failed: {e}")
                print("Falling back to document.cookie...")
            
            # Try document.cookie as fallback
            if not result["cookies"]:
                cookie_str = window.evaluate_js("document.cookie")
                if cookie_str:
                    cookies_list = []
                    for item in cookie_str.split(";"):
                        item = item.strip()
                        if "=" in item:
                            name, value = item.split("=", 1)
                            cookies_list.append({
                                "name": name.strip(),
                                "value": value.strip(),
                                "domain": ".amazon.com",
                                "path": "/",
                                "httpOnly": False,
                                "secure": False,
                            })
                    print(f"document.cookie returned {len(cookies_list)} cookies")
                    result["cookies"] = cookies_list
            
            if result["cookies"]:
                print(f"\n✅ Total cookies: {len(result['cookies'])}")
                for i, c in enumerate(result["cookies"][:10]):
                    print(f"  {i+1}. {c.get('name', 'unknown')}: httpOnly={c.get('httpOnly', 'N/A')}")
            
            window.destroy()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    window = webview.create_window(
        title="Cookie Test",
        url="https://sellercentral.amazon.eg/home",
        width=1000,
        height=700,
    )
    
    window.events.loaded += lambda: on_loaded(window)
    
    webview.start(gui="edgechromium")
    
    print("\n" + "="*60)
    print("Cookie extraction complete")
    print(f"Success: {result['cookies'] is not None}")
    if result["cookies"]:
        print(f"Cookie count: {len(result['cookies'])}")

if __name__ == "__main__":
    test_cookies()
