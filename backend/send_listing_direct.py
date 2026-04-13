"""
Direct Amazon Listing Sender — Standalone Script
No server, no DB, no API — just cookies + Playwright + direct POST.

Usage:
  cd backend
  python send_listing_direct.py

Requirements:
  - Active session in DB (cookies)
  - Product data hardcoded below
"""
import json
import asyncio
import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}")

# ============================================================
# 🔧 CONFIGURATION — عدل البيانات دي
# ============================================================

PRODUCT = {
    "title": "خلاط يدوي كهربائي 5 سرعات - وعاء خلط ستانلس ستيل 2 لتر، محرك 250 واط",
    "description": "خلاط يدوي كهربائي احترافي بـ 5 سرعات مع زر التيربو. وعاء خلط من الستانلس ستيل سعة 2 لتر. مثالي لخلط العجين والكريمات. مقبض مريح مانع للانزلاق.",
    "brand": "Generic",
    "manufacturer": "Generic",
    "model_number": "HM-250W",
    "barcode_type": "EAN",
    "barcode": "5012345678901",
    "product_type": "HOME_ORGANIZERS_AND_STORAGE",
    "browse_node": "21863799031",  # المنزل والمطبخ > التخزين والتنظيم
    "price": 350.0,
    "quantity": 25,
    "unit_count": "1",
    "included_components": "خلاط كهربائي + وعاء ستانلس + 2 مضرب",
    "bullet_points": [
        "5 سرعات مع زر تيربو للتحكم الكامل",
        "وعاء ستانلس ستيل 2 لتر",
        "محرك قوي 250 واط",
        "مقبض مريح مانع للانزلاق",
        "سهل التنظيف والتخزين"
    ],
}

COUNTRY_CODE = "eg"

# ============================================================
# 🚫 DO NOT MODIFY BELOW — الكود التحتاني مش محتاج تغيير
# ============================================================

def generate_amazon_payload(product_data: dict, template: dict) -> dict:
    """
    Generate the COMPLETE Amazon listing payload matching all 29 required fields.
    Then inject it into the live template.
    """
    import copy
    payload = copy.deepcopy(template)

    # 🔴 Build the flat attributeProperties dict
    attrs = {
        # الهوية الأساسية
        "item_name#1.value": product_data.get("title"),
        "item_name#1.language_tag": "ar_AE",
        "product_type#1.value": product_data.get("product_type", "HOME_ORGANIZERS_AND_STORAGE"),
        "recommended_browse_nodes#1.value": product_data.get("browse_node", "21863799031"),

        # العلامة التجارية
        "brand#1.value": product_data.get("brand", "Generic"),
        "brand#1.language_tag": "ar_AE",
        "externally_assigned_product_identifier#1.type": product_data.get("barcode_type", "EAN"),
        "externally_assigned_product_identifier#1.value": product_data.get("barcode"),

        # الوصف
        "product_description#1.value": product_data.get("description", ""),
        "product_description#1.language_tag": "ar_AE",
        "bullet_point#1.value": product_data.get("bullet_points", [""])[0] if isinstance(product_data.get("bullet_points"), list) else product_data.get("bullet_points", ""),
        "bullet_point#1.language_tag": "ar_AE",

        # المصنع
        "manufacturer#1.value": product_data.get("manufacturer", "Generic"),
        "manufacturer#1.language_tag": "ar_AE",
        "model_name#1.value": product_data.get("model_number", "MDL-001"),
        "model_name#1.language_tag": "ar_AE",

        # وحدة القياس
        "unit_count#1.value": float(product_data.get("unit_count", "1")),
        "unit_count#1.type.value": "Count",
        "unit_count#1.type.language_tag": "ar_AE",

        # المكونات
        "included_components#1.value": product_data.get("included_components", ""),
        "included_components#1.language_tag": "ar_AE",

        # حالة المنتج
        "condition_type#1.value": "new_new",
        "automated_pricing_rule_type#1.value": "disabled",
        "offerFulfillment": "MFN",
        "country_of_origin#1.value": "EG",
        "supplier_declared_dg_hz_regulation#1.value": "not_applicable",

        # التسعير والكمية
        "fulfillment_availability#1.quantity": int(product_data.get("quantity", 1)),
        "purchasable_offer#1.our_price#1.schedule#1.value_with_tax": float(product_data.get("price")),
        "purchasable_offer#1.maximum_retail_price#1.schedule#1.value_with_tax": float(product_data.get("price")) + 50,
    }

    # 🔴 Merge with template
    listing_details = payload.get("listing", {}).get("listingDetails", {})

    # Update flat attributes
    existing_flat = listing_details.get("attributeProperties", {})
    if not isinstance(existing_flat, dict):
        existing_flat = {}
    existing_flat.update(attrs)
    listing_details["attributeProperties"] = existing_flat

    # Update IMS V3 (nested JSON string)
    ims_v3_str = listing_details.get("attributePropertiesImsV3", "{}")
    if isinstance(ims_v3_str, str) and ims_v3_str.strip():
        try:
            ims_v3 = json.loads(ims_v3_str)
        except:
            ims_v3 = {}
    else:
        ims_v3 = {}
    ims_v3.update(attrs)
    listing_details["attributePropertiesImsV3"] = json.dumps(ims_v3, ensure_ascii=False)

    # Set language
    listing_details["listingLanguageCode"] = "ar_AE"
    listing_details["isDraft"] = True
    listing_details["skuState"] = "Draft"

    logger.info(f"Payload built: {len(json.dumps(payload))} chars, {len(attrs)} attributes")
    return payload


async def main():
    from playwright.async_api import async_playwright

    # Step 1: Load cookies from DB
    logger.info("=" * 60)
    logger.info("🚀 DIRECT LISTING SENDER")
    logger.info("=" * 60)

    logger.info("Step 1: Loading cookies from DB...")
    sys.path.insert(0, ".")
    from app.database import SessionLocal
    from app.models.session import Session as AuthSession
    from app.services.session_store import decrypt_data

    db = SessionLocal()
    auth_session = db.query(AuthSession).filter(
        AuthSession.auth_method == "browser",
        AuthSession.is_active == True,
        AuthSession.is_valid == True,
    ).order_by(AuthSession.created_at.desc()).first()

    if not auth_session:
        logger.error("❌ NO ACTIVE SESSION IN DB — Please login first!")
        db.close()
        sys.exit(1)

    cookies = json.loads(decrypt_data(auth_session.cookies_json))
    country = auth_session.country_code or COUNTRY_CODE
    db.close()

    logger.info(f"✅ Loaded {len(cookies)} cookies, country={country}")

    # Step 2: Launch browser
    logger.info("Step 2: Launching Playwright...")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
    )

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Africa/Cairo",
    )

    # Inject cookies
    pw_cookies = []
    for c in cookies:
        pw_c = {
            "name": c.get("name", ""),
            "value": c.get("value", ""),
            "domain": c.get("domain", ".amazon.eg"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
        }
        if c.get("expires"):
            pw_c["expires"] = c["expires"]
        raw_ss = c.get("sameSite", "")
        if raw_ss:
            ss = str(raw_ss).lower()
            if ss == "strict":
                pw_c["sameSite"] = "Strict"
            elif ss == "none":
                pw_c["sameSite"] = "None"
            else:
                pw_c["sameSite"] = "Lax"
        pw_cookies.append(pw_c)

    await context.add_cookies(pw_cookies)
    logger.info(f"✅ Injected {len(pw_cookies)} cookies")

    page = await context.new_page()

    # Hide automation
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
    """)

    # Step 3: Set up the INTERCEPTION TRAP before navigating
    logger.info("Step 3: Setting up template interception trap...")
    captured_template = {"data": None}

    async def handle_response(response):
        if "/abis/ajax/create-listing" in response.url and response.request.method == "GET":
            if response.status == 200:
                try:
                    captured_template["data"] = await response.json()
                    logger.info("✅ SUCCESS: Live Template Captured from Amazon!")
                except Exception as e:
                    logger.error(f"❌ Failed to parse live template: {e}")

    page.on("response", handle_response)

    # Step 4: Navigate to product_identity page — Amazon will make the GET call
    base = f"https://sellercentral.amazon.{country}"
    url = f"{base}/abis/listing/create/product_identity?productType={PRODUCT['product_type']}"
    logger.info(f"Step 4: Navigating to {url}")

    response = await page.goto(url, wait_until="networkidle", timeout=45000)

    # Check if redirected to login
    current_url = page.url
    if "/ap/signin" in current_url or "/gp/signin" in current_url:
        logger.error(f"❌ SESSION EXPIRED — Redirected to {current_url}")
        await browser.close()
        sys.exit(1)

    logger.info(f"✅ Page loaded: {current_url}")

    # Wait a bit more for all API calls to complete
    await asyncio.sleep(5)

    # Step 5: CRITICAL CHECK — Did we capture the live template?
    logger.info("Step 5: Checking if live template was captured...")
    if not captured_template["data"]:
        logger.error("🚨 FATAL: Failed to capture live template from Amazon. Aborting.")
        logger.error("   This means Amazon did not make the GET /abis/ajax/create-listing call")
        await browser.close()
        sys.exit(1)

    logger.info(f"✅ Live template captured! Keys: {list(captured_template['data'].keys()) if isinstance(captured_template['data'], dict) else 'N/A'}")

    # Step 6: Extract CSRF token — STRICT CHECK
    logger.info("Step 6: Extracting CSRF token...")

    csrf_token = await page.evaluate("""
        () => {
            const w = window['anti-csrftoken-a2z'] || window.a2zToken;
            if (w && w.length > 20) return w;
            const m = document.querySelector('[name="anti-csrftoken-a2z"]')?.content;
            if (m && m.length > 20) return m;
            const i = document.querySelector('input[name="anti-csrftoken-a2z"]')?.value;
            if (i && i.length > 20) return i;
            return "";
        }
    """)

    if not csrf_token or len(csrf_token) < 20:
        logger.error(f"❌ CSRF TOKEN MISSING! Got: '{csrf_token}' (len={len(csrf_token) if csrf_token else 0})")
        logger.error("🚨 ABORTING — cannot send without valid CSRF")
        await browser.close()
        sys.exit(1)

    logger.info(f"✅ CSRF token: {csrf_token[:20]}... ({len(csrf_token)} chars)")

    # Step 7: Build payload from LIVE TEMPLATE (not fake one!)
    logger.info("Step 7: Building payload from LIVE template...")
    payload = generate_amazon_payload(PRODUCT, captured_template["data"])
    payload_json = json.dumps(payload, ensure_ascii=False)
    logger.info(f"✅ Payload size: {len(payload_json)} chars")

    # Step 8: Send POST from INSIDE browser
    logger.info("Step 8: Sending POST from inside browser...")

    result = await page.evaluate("""
        async (params) => {
            const { payload, csrf } = params;

            const formData = new URLSearchParams();
            formData.append('data', payload);
            formData.append('anti-csrftoken-a2z', csrf);

            const res = await fetch('/abis/ajax/create-listing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'anti-csrftoken-a2z': csrf,
                    'x-csrf-token': csrf,
                },
                body: formData.toString(),
            });

            const text = await res.text();

            try {
                const json = JSON.parse(text);
                return {
                    status: res.status,
                    success: json.status === 'SUCCESS',
                    json: json,
                };
            } catch (e) {
                return {
                    status: res.status,
                    success: false,
                    error: 'Response not JSON: ' + text.substring(0, 500),
                };
            }
        }
    """, {"payload": payload_json, "csrf": csrf_token})

    logger.info("=" * 60)
    logger.info("📊 RESULT:")
    logger.info(f"   Status: {result.get('status')}")
    logger.info(f"   Success: {result.get('success')}")
    logger.info(f"   Full response: {json.dumps(result.get('json', result), indent=2, ensure_ascii=False)[:2000]}")
    logger.info("=" * 60)

    await browser.close()

    if result.get("success"):
        logger.info("✅✅✅ LISTING CREATED SUCCESSFULLY!")
    else:
        logger.error(f"❌ FAILED: {result.get('error', result.get('json', {}).get('message', 'Unknown'))}")


if __name__ == "__main__":
    asyncio.run(main())
