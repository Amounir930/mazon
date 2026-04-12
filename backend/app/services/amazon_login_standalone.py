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
    """Parse document.cookie into list of dicts (fallback for old method)"""
    if not cookie_string:
        return []
    cookies = []
    for item in cookie_string.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({"name": name.strip(), "value": value.strip(), "domain": ".amazon.com", "path": "/"})
    return cookies


def normalize_pywebview_cookies(cookies_data, cookie_values: dict = None) -> list:
    """
    Convert PyWebView get_cookies() format to our expected format.
    
    PyWebView format:
    [{"cookie_name": {"expires": "...", "domain": "...", "httponly": True, ...}}]
    Note: get_cookies() does NOT return values! We need document.cookie for that.
    
    Our format:
    [{"name": "cookie_name", "value": "...", "domain": "...", "httpOnly": True, ...}]
    """
    if not cookies_data:
        return []
    
    normalized = []
    cookie_values = cookie_values or {}
    
    if isinstance(cookies_data, list):
        # PyWebView returns list of {name: {attrs}}
        for item in cookies_data:
            if not isinstance(item, dict):
                continue
            
            # Each item is {cookie_name: {attrs}}
            for name, attrs in item.items():
                if not isinstance(attrs, dict):
                    continue
                
                # Get value from document.cookie if available
                value = cookie_values.get(name, "")
                
                cookie = {
                    "name": name,
                    "value": value,
                    "domain": attrs.get("domain", ".amazon.eg"),
                    "path": attrs.get("path", "/"),
                    "httpOnly": attrs.get("httponly", attrs.get("httpOnly", False)),
                    "secure": attrs.get("secure", attrs.get("Secure", False)),
                    "sameSite": attrs.get("samesite", attrs.get("sameSite", "Lax")),
                    "expires": attrs.get("expires", ""),
                }
                
                # Only add if we have a value or it's an httpOnly cookie
                if value or cookie["httpOnly"]:
                    normalized.append(cookie)
    
    elif isinstance(cookies_data, dict):
        # Alternative format: {name: {attrs}}
        for name, attrs in cookies_data.items():
            if not isinstance(attrs, dict):
                continue
            
            value = cookie_values.get(name, "")
            
            cookie = {
                "name": name,
                "value": value,
                "domain": attrs.get("domain", ".amazon.eg"),
                "path": attrs.get("path", "/"),
                "httpOnly": attrs.get("httponly", attrs.get("httpOnly", False)),
                "secure": attrs.get("secure", attrs.get("Secure", False)),
                "sameSite": attrs.get("samesite", attrs.get("sameSite", "Lax")),
                "expires": attrs.get("expires", ""),
            }
            
            if value or cookie["httpOnly"]:
                normalized.append(cookie)
    
    # Filter out cookies with no value at all
    normalized = [c for c in normalized if c["value"]]
    
    print(f"Normalized {len(normalized)} cookies with values")
    return normalized


def parse_document_cookies(cookie_string) -> dict:
    """Parse document.cookie string into {name: value} dict for value lookup"""
    if not cookie_string:
        return {}
    
    values = {}
    for item in cookie_string.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            values[name.strip()] = value.strip()
    
    return values


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
                            # Strategy: Get ALL cookies from native API + values from document.cookie
                            # This gives us both httpOnly cookies AND their values
                            
                            # Step 1: Get cookie metadata (names, domains, httpOnly flags)
                            all_cookies = window.get_cookies()
                            print(f"get_cookies() returned type: {type(all_cookies)}")
                            
                            if not all_cookies or len(all_cookies) == 0:
                                raise Exception("Empty cookies from native API")
                            
                            # Step 2: Get cookie values from document.cookie
                            cookie_str = window.evaluate_js("document.cookie")
                            cookie_values = parse_document_cookies(cookie_str)
                            print(f"document.cookie has {len(cookie_values)} cookie values")
                            
                            # Step 3: Merge metadata with values
                            login_state["cookies"] = normalize_pywebview_cookies(all_cookies, cookie_values)
                            print(f"Got {len(login_state['cookies'])} normalized cookies")
                            
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
