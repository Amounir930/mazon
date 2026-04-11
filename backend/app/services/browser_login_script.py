"""
Browser Login Script - بيشتغل standalone process
بيكتب النتيجة في JSON file
"""
import os
import sys
import json
import time
from pathlib import Path

PROFILE_BASE = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "CrazyListerProfiles"
PROFILE_BASE.mkdir(parents=True, exist_ok=True)
SELLER_CENTRAL_BASE = {"eg": "https://sellercentral.amazon.eg"}

def main():
    email = os.environ.get("BROWSER_EMAIL", "")
    password = os.environ.get("BROWSER_PASSWORD", "")
    country_code = os.environ.get("BROWSER_COUNTRY", "eg")
    otp = os.environ.get("BROWSER_OTP", "")
    output_file = os.environ.get("BROWSER_OUTPUT", "")

    if not output_file:
        print("ERROR: BROWSER_OUTPUT not set")
        sys.exit(1)

    result = {"success": False, "error": "unknown"}

    try:
        from playwright.sync_api import sync_playwright

        profile_dir = PROFILE_BASE / email
        profile_dir.mkdir(parents=True, exist_ok=True)

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-client-side-phishing-detection",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-pings",
            "--password-store=basic",
            "--disable-infobars",
            "--disable-component-update",
            "--disable-background-networking",
            "--disable-dev-shm-usage",
        ])
        ctx = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ar-EG",
        )
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        base = SELLER_CENTRAL_BASE.get(country_code)
        if not base:
            result = {"success": False, "error": f"Unsupported country: {country_code}"}
        else:
            page.goto(f"{base}/home", wait_until="domcontentloaded", timeout=60000)

            for i in range(90):
                time.sleep(2)
                url = page.url

                if "/home" in url or ("/sellercentral" in url and "/ap/" not in url):
                    title = page.title()
                    if "Sign in" not in title:
                        cookies = ctx.cookies()
                        seller = "Unknown"
                        try:
                            el = page.query_selector('[data-testid="account-name"]')
                            if el:
                                seller = el.inner_text().strip()
                        except Exception:
                            pass
                        result = {"success": True, "cookies": cookies, "seller_name": seller, "country_code": country_code}
                        break

                if "/ap/signin" in url or "/signin" in url:
                    try:
                        email_el = page.query_selector('input[name="email"]')
                        if email_el:
                            email_el.fill(email)
                            btn = page.query_selector('input#continue')
                            if btn:
                                btn.click()
                                page.wait_for_load_state("domcontentloaded")
                                time.sleep(1)
                    except Exception:
                        pass
                    try:
                        pw_el = page.query_selector('input[name="password"]')
                        if pw_el:
                            pw_el.fill(password)
                            submit = page.query_selector('#signInSubmit')
                            if submit:
                                submit.click()
                                page.wait_for_load_state("domcontentloaded")
                                time.sleep(2)
                    except Exception:
                        pass

                elif ("/ap/mfa" in url or "two-step" in url.lower()) and otp:
                    try:
                        otp_el = page.query_selector('input[name="otpCode"]')
                        if otp_el:
                            otp_el.fill(otp)
                            btn = page.query_selector('#auth-signin-button')
                            if btn:
                                btn.click()
                                page.wait_for_load_state("domcontentloaded")
                                time.sleep(3)
                    except Exception:
                        pass
            else:
                result = {"success": False, "error": "timeout"}

        browser.close()
        pw.stop()

    except Exception as e:
        result = {"success": False, "error": str(e)}

    # Write result
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=str)

    print(f"Result written to {output_file}")


if __name__ == "__main__":
    main()
