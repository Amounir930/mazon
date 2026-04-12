"""
Amazon Login via PyWebView - Standalone Script
بيشتغل كـ process منفصل تماماً من الـ Backend
"""
import os
import sys
import json
import time
from pathlib import Path

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
    "uk": "https://sellercentral.amazon.co.uk",
    "us": "https://sellercentral.amazon.com",
}


def parse_cookies(cookie_string):
    """Parse document.cookie into list of dicts"""
    if not cookie_string:
        return []
    cookies = []
    for item in cookie_string.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".amazon.com", "path": "/"})
    return cookies


def main():
    country_code = os.environ.get("AMZN_COUNTRY", "eg")
    output_file = os.environ.get("AMZN_OUTPUT", "")
    
    if not output_file:
        print("ERROR: AMZN_OUTPUT not set")
        sys.exit(1)
    
    base_url = SELLER_CENTRAL_BASE.get(country_code.lower(), SELLER_CENTRAL_BASE["eg"])

    # Just open the base URL - Amazon will redirect to login page automatically
    login_url = base_url
    
    print(f"Opening Amazon login: {login_url}")
    print("User should login in the popup window...")
    
    result = {"success": False, "cookies": [], "error": None}
    
    try:
        import webview
        
        login_state = {"done": False, "cookies": None, "url": None}
        
        def on_loaded(window):
            try:
                url = window.get_current_url()
                login_state["url"] = url
                print(f"Page: {url}")

                if url and "/ap/signin" not in url and "/gp/signin" not in url:
                    if any(x in url for x in ["/home", "/dashboard", "/inventory"]):
                        print(f"Login detected!")
                        try:
                            # Try to get ALL cookies (including HttpOnly) via native API
                            # This is better than document.cookie which misses HttpOnly cookies
                            try:
                                # Method 1: Try native cookie API if available
                                all_cookies = window.get_cookies()
                                if all_cookies:
                                    login_state["cookies"] = all_cookies
                                    print(f"Got {len(login_state['cookies'])} cookies (native API)")
                            except:
                                # Method 2: Fallback to document.cookie
                                cookie_str = window.evaluate_js("document.cookie")
                                if cookie_str:
                                    login_state["cookies"] = parse_cookies(cookie_str)
                                    print(f"Got {len(login_state['cookies'])} cookies (JS fallback)")
                            
                            login_state["done"] = True
                            window.destroy()
                        except Exception as e:
                            print(f"Cookie extract error: {e}")
                            login_state["done"] = True
                            window.destroy()
            except Exception:
                pass
        
        def on_closing():
            login_state["done"] = True
        
        window = webview.create_window(
            title=f"Amazon Login ({country_code.upper()})",
            url=login_url,
            width=1000,
            height=700,
        )
        
        window.events.loaded += lambda: on_loaded(window)
        window.events.closing += on_closing
        
        webview.start(gui="edgechromium")
        
        cookies = login_state.get("cookies") or []
        if cookies:
            result = {"success": True, "cookies": cookies, "url": login_state.get("url")}
        else:
            result = {"success": False, "error": "لم يتم استخراج الكوكيز", "cookies": []}
            
    except Exception as e:
        print(f"Error: {e}")
        result = {"success": False, "error": str(e), "cookies": []}
    
    # Write result
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str)
    
    print(f"Result written to {output_file}")
    print(f"Success: {result['success']}, Cookies: {len(result['cookies'])}")


if __name__ == "__main__":
    main()
