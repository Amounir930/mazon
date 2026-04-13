"""
Playwright Login Script — Runs as a DETACHED subprocess
Phase 1: Cookie Extraction with Browser Fingerprint Protection

This script is launched by playwright_login.py and runs independently.
Results are written to a temp JSON file.
"""
import os
import sys
import json
import time
import re
import tempfile
from pathlib import Path
from typing import Optional

# =============================================
# Centralized User-Agent (MUST match niquests/requests)
# =============================================
AMAZON_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

WINDOWS_USER_AGENT = AMAZON_USER_AGENT  # Alias for backward compatibility

print("=" * 60)
print("🚀 Playwright Login Script Started")
print(f"   Python: {sys.version}")
print(f"   Working Dir: {os.getcwd()}")
print(f"   Script: {__file__}")
print("=" * 60)

# =============================================
# Amazon Seller Central URLs
# =============================================
SELLER_CENTRAL_BASE = {
    "eg": "https://sellercentral.amazon.eg",
    "sa": "https://sellercentral.amazon.sa",
    "ae": "https://sellercentral.amazon.ae",
}


def install_stealth(page):
    """Install stealth patches to remove bot fingerprints."""
    stealth_script = """
    () => {
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // Mock chrome.runtime
        window.chrome = { runtime: {}, loadTimes: () => ({}), csi: () => ({}), app: {} };

        // Override plugins
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });

        // Override languages
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

        // Override hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

        // Override deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    }
    """
    try:
        page.evaluate(stealth_script)
    except Exception:
        pass


def extract_seller_name(page) -> str:
    """Phase 3: Extract seller name via internal API or page content."""
    # Method 1: Try merchant picker API
    try:
        response = page.evaluate("""
        async () => {
            try {
                const resp = await fetch('/merchant_picker/ajax/getData', {
                    credentials: 'include',
                    headers: { 'Accept': 'application/json' }
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
            return null;
        }
        """)
        if response and isinstance(response, dict):
            seller_name = response.get("sellerName") or response.get("merchantName")
            if seller_name:
                print(f"Seller name extracted via API: {seller_name}")
                return seller_name
    except Exception:
        pass

    # Method 2: Try to find seller name from page content (Good morning, [Seller Name])
    try:
        page_content = page.content()
        # Look for "Good morning/afternoon/evening, [Seller Name]"
        import re
        greeting_pattern = r'Good\s+(?:morning|afternoon|evening)[,，]\s+([^<,.]+)'
        match = re.search(greeting_pattern, page_content, re.IGNORECASE)
        if match:
            seller_name = match.group(1).strip()
            if seller_name and 2 < len(seller_name) < 100 and seller_name.lower() not in ['amazon', 'unknown']:
                print(f"Seller name extracted from greeting: {seller_name}")
                return seller_name
    except Exception:
        pass

    # Method 3: Try to extract from /account-health or dashboard API
    try:
        response = page.evaluate("""
        async () => {
            try {
                const resp = await fetch('/home/dashboard/ajax/getData', {
                    credentials: 'include',
                    headers: { 'Accept': 'application/json' }
                });
                if (resp.ok) return await resp.json();
            } catch(e) {}
            return null;
        }
        """)
        if response and isinstance(response, dict):
            seller_name = response.get("sellerName") or response.get("merchantName") or response.get("displayName")
            if seller_name:
                print(f"Seller name extracted from dashboard API: {seller_name}")
                return seller_name
    except Exception:
        pass

    # Fallback: page title (but filter out "Amazon")
    try:
        title = page.title()
        if title:
            for suffix in [" - Seller Central", " | Seller Central", "Seller Central"]:
                title = title.replace(suffix, "")
            title = title.strip()
            if title and 2 < len(title) < 100 and title.lower() not in ['amazon', 'unknown', 'amazon seller central']:
                print(f"Seller name from title: {title}")
                return title
    except Exception:
        pass

    print("WARNING: Could not extract seller name, using email as fallback")
    return "Unknown Seller"


def extract_csrf_token(html_content: str) -> Optional[str]:
    """Phase 2: Extract CSRF Token via Regex from JavaScript-embedded code."""
    patterns = [
        # Amazon's actual pattern: "anti-csrftoken-a2z":"TOKEN_VALUE"
        r'"anti-csrftoken-a2z"\s*:\s*"([^"]+)"',
        # Variant with single quotes
        r"'anti-csrftoken-a2z'\s*:\s*'([^']+)'",
        # Alternative token name
        r'"antiCsrfToken"\s*:\s*"([^"]+)"',
        # Meta tag (rare but possible)
        r'<meta[^>]*anti-csrf-token[^>]*content=["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            token = match.group(1).strip()
            # Validate token length (real CSRF tokens are 40-300 chars)
            if 40 < len(token) < 500:
                # REJECT A/B test tokens and experiment names
                invalid_patterns = [
                    r'_treatment',
                    r'_experiment',
                    r'_weblab',
                    r'_test_',
                    r'^mons_',
                    r'^ab',
                ]
                if any(re.search(inv, token, re.IGNORECASE) for inv in invalid_patterns):
                    print(f"CSRF candidate rejected (A/B test): {token[:30]}...")
                    continue
                print(f"CSRF Token extracted via regex ({len(token)} chars)")
                return token

    print("WARNING: No CSRF token found with any regex pattern")
    return None


def main():
    country_code = os.environ.get("AMZN_COUNTRY", "eg")
    output_file = os.environ.get("AMZN_OUTPUT", "")

    if not output_file:
        print("ERROR: AMZN_OUTPUT not set")
        sys.exit(1)

    base_url = SELLER_CENTRAL_BASE.get(country_code.lower(), SELLER_CENTRAL_BASE["eg"])
    login_url = base_url

    result = {
        "success": False,
        "cookies": [],
        "seller_name": "Unknown Seller",
        "csrf_token": None,
        "user_agent": WINDOWS_USER_AGENT,  # FIX 3: Pass to backend for niquests consistency
        "error": None,
        "url": login_url,
    }

    print(f"Opening Playwright (headless=False, stealth, persistent) → {login_url}")
    print("=" * 60)
    print("🔥 STARTING BROWSER LAUNCH (PERSISTENT CONTEXT)...")
    print("=" * 60)

    try:
        from playwright.sync_api import sync_playwright

        playwright = sync_playwright().start()
        print("✅ Playwright started")

        # =============================================
        # FIX 1: Persistent Context (save Local Storage, IndexedDB, Cache)
        # =============================================
        user_data_dir = os.path.join(tempfile.gettempdir(), "amazon_browser_profile_eg" if country_code == "eg" else f"amazon_browser_profile_{country_code}")
        print(f"📁 User Data Dir: {user_data_dir}")

        print("🚀 Launching Chromium with persistent context...")
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            user_agent=WINDOWS_USER_AGENT,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            timezone_id="Africa/Cairo",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-infobars",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        print("✅ Browser launched with persistent context!")

        page = context.pages[0] if context.pages else context.new_page()
        print("✅ Browser context and page created")

        # =============================================
        # THE NINJA CSRF SNIFFER (التنصت على الشبكة)
        # =============================================
        captured_data = {"csrf_token": None}

        def intercept_request(request):
            """Sniff outgoing requests for CSRF token in headers."""
            try:
                headers = request.headers
                if 'anti-csrftoken-a2z' in headers:
                    token = headers['anti-csrftoken-a2z']
                    # Reject A/B test tokens
                    if token and len(token) > 30 and not token.startswith('mons_'):
                        captured_data["csrf_token"] = token
                        print(f"🕵️ CSRF TOKEN CAPTURED FROM NETWORK: {token[:30]}... ({len(token)} chars)")
            except Exception:
                pass

        # Enable request interception
        page.on("request", intercept_request)
        print("🕵️ Network sniffer activated — hunting CSRF token from outgoing requests...")

        # Install stealth
        install_stealth(page)

        # Force window to foreground on Windows
        try:
            import ctypes
            hwnd = page.evaluate("() => window.outerHeight ? 1 : 0")
            ctypes.windll.user32.SetForegroundWindow(ctypes.windll.kernel32.GetCurrentProcessId())
            print("📌 Attempting to bring browser window to foreground...")
        except Exception as e:
            print(f"   (Could not force window to foreground: {e})")

        print(f"Navigating to {login_url}...")
        page.goto(login_url, wait_until="domcontentloaded", timeout=60000)

        print("✅✅✅ Browser window should now be visible!")
        print("👉 Look for the Chromium window on your screen")
        print("Waiting for user to login (close browser when done)...")
        print("Login in the browser window and wait for dashboard to load.")

        start_time = time.time()
        timeout_seconds = 300

        while time.time() - start_time < timeout_seconds:
            time.sleep(2)

            try:
                current_url = page.url

                # =============================================
                # LAYER 1: Parse URL and check the PATH only
                # =============================================
                from urllib.parse import urlparse
                parsed = urlparse(current_url)
                url_path = parsed.path  # e.g. "/ap/signin" or "/home" (NOT query params!)
                print(f"[Check] URL Path: {url_path}")

                # =============================================
                # LAYER 2: REJECT if on ANY login/auth page
                # =============================================
                # Amazon auth pages start with /ap/ or /gp/
                auth_prefixes = ["/ap/", "/gp/", "/auth/", "/signin", "/login"]
                is_auth_page = any(url_path.startswith(prefix) for prefix in auth_prefixes)

                if is_auth_page:
                    print(f"  ❌ Still on auth page: {url_path} — waiting...")
                    continue

                # =============================================
                # LAYER 3: If NOT on auth page → user IS logged in!
                # =============================================
                # KEY INSIGHT: ANY page that's not /ap/ or /gp/ means logged in
                # Amazon may force users to /mario/... (seller onboarding)
                # but they ARE logged in — we just can't navigate to /home!
                
                if not is_auth_page:
                    print(f"  ✅ NOT on auth page → User is logged in!")
                    print(f"     Current page: {url_path}")
                    
                    # Try to navigate to /home to confirm, but don't block if it fails
                    try:
                        page.goto(f"{base_url}/home", wait_until="domcontentloaded", timeout=10000)
                        time.sleep(1)
                        current_url = page.url
                        url_path = urlparse(current_url).path
                        print(f"  ✅ Navigated to /home: {url_path}")
                    except Exception as nav_error:
                        # Navigation failed (Amazon redirected us) — but user IS logged in!
                        print(f"  ⚠️ Could not navigate to /home: {nav_error}")
                        print(f"     But user IS logged in (not on /ap/ or /gp/) — proceeding!")
                        # Extract current page URL for result
                        current_url = page.url
                        url_path = urlparse(current_url).path
                        # Don't block — proceed with cookie extraction

                    print(f"  ✅ Dashboard detected via URL: {url_path}")
                    # Proceed to Layer 4 and then extract cookies
                else:
                    # Still on auth page
                    print(f"  ❌ Still on auth page: {url_path} — waiting...")
                    continue

                # =============================================
                # LAYER 4: Page title verification (extra safety)
                # =============================================
                try:
                    page_title = page.title()
                    print(f"[Check] Page Title: {page_title}")

                    # REJECT if page title indicates login
                    login_titles = ["sign in", "تسجيل الدخول", "sign-in", "login to amazon"]
                    is_login_title = any(lt in page_title.lower() for lt in login_titles)

                    if is_login_title:
                        print(f"  ❌ Page title indicates login — false positive!")
                        continue

                    # CONFIRM if page title indicates dashboard
                    dashboard_titles = ["seller central", "dashboard", "inventory", "orders"]
                    is_dashboard_title = any(dt in page_title.lower() for dt in dashboard_titles)

                    if not is_dashboard_title:
                        print(f"  ⚠️ Page title not confirmed as dashboard — checking content...")
                        # Check page content as fallback
                        page_content = page.content()
                        dashboard_content = ["account health", "global snapshot", "add a product"]
                        if not any(dc in page_content.lower() for dc in dashboard_content):
                            print(f"  ❌ Page content doesn't match dashboard — waiting...")
                            continue

                except Exception as e:
                    print(f"  ⚠️ Title/content check error: {e}")
                    # Don't block on content errors, URL path is reliable enough
                    pass

                # =============================================
                # SUCCESS: We're definitely logged in!
                # =============================================
                print(f"✅✅✅ LOGIN CONFIRMED! URL: {current_url}")
                print(f"  Path: {url_path}")
                print(f"  Title: {page.title()}")
                time.sleep(5)  # Let cookies settle and allow background AJAX requests to fire

                # Extract ALL cookies (from ALL domains — .amazon.com, .amazon.eg, etc.)
                all_cookies = context.cookies()
                print(f"Extracted {len(all_cookies)} cookies via Playwright (all domains)")

                if not all_cookies:
                    result["error"] = "No cookies extracted"
                    break

                cookie_names = [c["name"] for c in all_cookies]
                print(f"Cookie names: {cookie_names}")

                result["cookies"] = all_cookies
                result["url"] = current_url

                # Extract seller name
                result["seller_name"] = extract_seller_name(page)

                # =============================================
                # CSRF EXTRACTION: Network Sniffer (Primary) + JS Injection (Fallback)
                # =============================================

                # Step 1: Check if we captured the token from network sniffing
                if captured_data["csrf_token"]:
                    result["csrf_token"] = captured_data["csrf_token"]
                    print(f"✅ NETWORK SNIFFER SUCCESS: CSRF token captured ({len(result['csrf_token'])} chars)")
                else:
                    print("⚠️ Network sniffer didn't capture CSRF token — trying JS injection fallback...")

                    # Step 2: JS injection fallback
                    js_extractor = """
                    () => {
                        // 1. Check direct window variables
                        if (window.a2zToken) return window.a2zToken;
                        if (window['anti-csrftoken-a2z']) return window['anti-csrftoken-a2z'];
                        if (window.amznCsrfToken) return window.amznCsrfToken;

                        // 2. Deep scan in window objects
                        for (let key in window) {
                            if (typeof window[key] === 'string' && key.toLowerCase().includes('csrf')) {
                                if (window[key].length > 30) return window[key];
                            }
                        }

                        // 3. Scan all script tags memory
                        let scripts = document.querySelectorAll('script');
                        for (let s of scripts) {
                            let text = s.innerText;
                            let match = text.match(/"anti-csrftoken-a2z"\\s*:\\s*"([^"]+)"/i) ||
                                        text.match(/a2zToken\\s*=\\s*"([^"]+)"/i);
                            if (match && match[1].length > 30 && !match[1].startsWith('mons_')) {
                                return match[1];
                            }
                        }

                        return null;
                    }
                    """

                    try:
                        csrf_token = page.evaluate(js_extractor)
                        if csrf_token and len(csrf_token) > 30:
                            result["csrf_token"] = csrf_token
                            print(f"✅ JS INJECTION SUCCESS: CSRF token extracted ({len(csrf_token)} chars)")
                        else:
                            print("⚠️ JS injection didn't find CSRF token — trying HTML regex fallback...")
                            # Step 3: HTML regex as last resort
                            html = page.content()
                            fallback_token = extract_csrf_token(html)
                            if fallback_token:
                                result["csrf_token"] = fallback_token
                                print(f"✅ REGEX FALLBACK SUCCESS: CSRF token extracted ({len(fallback_token)} chars)")
                            else:
                                result["csrf_token"] = None
                                print("❌ All CSRF extraction methods failed")
                    except Exception as e:
                        print(f"❌ Error during JS token extraction: {e}")
                        result["csrf_token"] = None

                result["success"] = True
                break

            except Exception as e:
                print(f"Login poll error: {e}")
                continue

        # Close persistent context
        context.close()
        playwright.stop()

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Playwright error: {e}")
        print(f"Traceback:\n{tb}")
        result["error"] = f"{str(e)}\n\n{tb}"
        try:
            context.close()
            playwright.stop()
        except Exception:
            pass

    # Write result
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str)

    print(f"Result written to {output_file}")
    print(f"Success: {result['success']}, Cookies: {len(result['cookies'])}, Seller: {result['seller_name']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = f"{str(e)}\n\n{tb}"
        print(f"FATAL ERROR: {error_msg}")
        # Try to write error to output file if possible
        try:
            output_file = os.environ.get("AMZN_OUTPUT", "")
            if output_file:
                error_result = {
                    "success": False,
                    "cookies": [],
                    "seller_name": None,
                    "csrf_token": None,
                    "user_agent": None,
                    "error": error_msg,
                    "url": None,
                }
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(error_result, f, ensure_ascii=False, default=str)
                print(f"Error written to {output_file}")
        except Exception:
            pass
        # Keep console open on error so we can see the message
        time.sleep(10)
        sys.exit(1)
