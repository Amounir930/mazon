"""
Amazon Login via Playwright - Standalone Script
بيشتغل كـ process منفصل تماماً من الـ Backend
بيقرا كل الـ cookies بما فيها HttpOnly بالـ values
"""
import os
import sys
import json
import time
import asyncio
from pathlib import Path

SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
    "uk": "https://sellercentral.amazon.co.uk",
    "us": "https://sellercentral.amazon.com",
}

# Login URLs - Egypt needs specific sign-in URL without dynamic ssoResponse
LOGIN_URLS = {
    "eg": "https://sellercentral.amazon.eg/ap/signin?openid.return_to=https%3A%2F%2Fsellercentral.amazon.eg%2Fhome&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=amzn_sc_eg_v2&openid.mode=checkid_setup&language=en_AE&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0",
    "sa": "https://sellercentral.amazon.sa/ap/signin?openid.return_to=https%3A%2F%2Fsellercentral.amazon.sa%2Fhome",
    "ae": "https://sellercentral.amazon.ae/ap/signin?openid.return_to=https%3A%2F%2Fsellercentral.amazon.ae%2Fhome",
    "uk": "https://sellercentral.amazon.co.uk/ap/signin?openid.return_to=https%3A%2F%2Fsellercentral.amazon.co.uk%2Fhome",
    "us": "https://sellercentral.amazon.com/ap/signin?openid.return_to=https%3A%2F%2Fsellercentral.amazon.com%2Fhome",
}


def main():
    country_code = os.environ.get("AMZN_COUNTRY", "eg")
    output_file = os.environ.get("AMZN_OUTPUT", "")

    if not output_file:
        print("ERROR: AMZN_OUTPUT not set")
        sys.exit(1)

    base_url = SELLER_CENTRAL_BASE.get(country_code.lower(), SELLER_CENTRAL_BASE["eg"])
    login_url = base_url

    print(f"=" * 60)
    print(f"Amazon Seller Central Login (Playwright)")
    print(f"Country: {country_code.upper()}")
    print(f"URL: {login_url}")
    print(f"=" * 60)
    print()
    print("⚠️  IMPORTANT: A browser window will open.")
    print("   Please login with your Amazon Seller account in THAT window.")
    print("   The script will automatically detect when you're logged in.")
    print()
    print("⏳ Waiting for login... (max 5 minutes)")
    print()

    result = {"success": False, "cookies": [], "error": None}

    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch browser with VISIBLE window - MUST be visible for user to login
            browser = p.chromium.launch(
                headless=False,  # Visible window!
                args=[
                    "--no-sandbox",
                    "--start-maximized",  # Maximize window so it's visible
                    "--disable-blink-features=AutomationControlled",
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            )
            
            page = context.new_page()
            
            # Bring window to front
            page.bring_to_front()
            
            # Hide automation
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)
            
            # Navigate to Amazon - will redirect to sign-in if not logged in
            print(f"🌐 Opening Amazon Seller Central...")
            page.goto(login_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for redirect to sign-in page
            print(f"   Waiting for redirect to sign-in page...")
            try:
                page.wait_for_url("**/ap/signin**", timeout=10000)
                print(f"   ✅ Redirected to sign-in page")
            except:
                print(f"   ⚠️  No redirect detected, current URL: {page.url[:80]}")
            
            print(f"   Current URL: {page.url[:100]}")
            print()
            print("👉 Please login in the browser window that just opened.")
            print("   The script will detect login automatically.")
            print()
            
            # Wait for user to login
            max_wait = 300  # 5 minutes
            waited = 0
            last_url = ""
            
            while waited < max_wait:
                time.sleep(3)
                waited += 3
                
                try:
                    current_url = page.url
                    
                    # Only print if URL changed
                    if current_url != last_url:
                        print(f"   🔄 URL changed: {current_url[:80]}...")
                        last_url = current_url
                    
                    # Check if logged in (not on sign-in page and on dashboard/home/inventory)
                    if "/ap/signin" not in current_url and "/gp/signin" not in current_url and "sign-in" not in current_url.lower():
                        if any(x in current_url for x in ["/home", "/dashboard", "/inventory", "/account-switcher"]):
                            print()
                            print(f"✅ Login detected!")
                            print(f"   URL: {current_url[:100]}")
                            
                            # Get ALL cookies (including HttpOnly with values)
                            all_cookies = context.cookies()
                            print(f"   Extracting {len(all_cookies)} cookies...")
                            
                            # Normalize cookies
                            normalized = []
                            for cookie in all_cookies:
                                normalized.append({
                                    "name": cookie["name"],
                                    "value": cookie["value"],
                                    "domain": cookie.get("domain", ".amazon.eg"),
                                    "path": cookie.get("path", "/"),
                                    "httpOnly": cookie.get("httpOnly", False),
                                    "secure": cookie.get("secure", True),
                                    "sameSite": cookie.get("sameSite", "Lax"),
                                    "expires": cookie.get("expires", ""),
                                })
                            
                            result = {
                                "success": True,
                                "cookies": normalized,
                                "url": current_url,
                            }
                            print(f"✅ Successfully extracted {len(normalized)} cookies!")
                            break
                except Exception as e:
                    print(f"   ⚠️  Check error: {e}")
                    continue
            
            if waited >= max_wait:
                print()
                print("❌ Login timeout! Please try again.")
            
            browser.close()
            
            if not result["success"] and waited < max_wait:
                result = {"success": False, "error": "Login cancelled", "cookies": []}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        result = {"success": False, "error": str(e), "cookies": []}

    # Write result
    print()
    print(f"💾 Saving result to: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str)

    print(f"✅ Result written!")
    print(f"   Success: {result['success']}")
    print(f"   Cookies: {len(result['cookies'])}")
    print(f"=" * 60)


if __name__ == "__main__":
    main()
