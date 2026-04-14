# Sync Engine Documentation

## نظرة عامة

نظام المزامنة (Sync Engine) بيستخدم Playwright عشان يسحب البيانات من Amazon Seller Central باستخدام الجلسة المسجلة عبر PyWebView.

## لماذا Playwright وليس niquests + BeautifulSoup؟

| المعيار | niquests + BS4 | Playwright |
|---------|---------------|------------|
| SPA Support | ❌ HTML ثابت فقط | ✅ Fully rendered DOM |
| HttpOnly Cookies | ❌ مش بيقرأها | ✅ بيقبلها كلها |
| JavaScript APIs | ❌ مش بيشغلها | ✅ بيئة متصفح كاملة |
| CAPTCHA Detection | ❌ | ✅ بيقدر يكتشفها |
| Anti-detection | ❌ | ✅ بيخفي automation |

## المعمارية

```
┌────────────────────────────────────────────────────┐
│          User (Frontend React)                      │
│          ↓ POST /api/v1/sync/products              │
└────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────┐
│          FastAPI Backend                            │
│  products_sync.py: sync_products_cookie()           │
│  ↓                                                  │
└────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────┐
│          CookieScraper (Playwright)                 │
│  1. Get session from SQLite (encrypted)            │
│  2. Validate session                               │
│  3. Launch headless browser                        │
│  4. Inject cookies (including HttpOnly)            │
│  5. Navigate to page (with random delays)          │
│  6. Extract data via JavaScript                    │
│  7. Return JSON                                    │
└────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────┐
│          SQLite Database                            │
│  Upsert products/orders/inventory                   │
└────────────────────────────────────────────────────┘
```

## API Endpoints

### 1. Sync Products

```bash
POST /api/v1/sync/products?email=amazon_eg
```

**Response:**
```json
{
  "success": true,
  "products": [
    {
      "sku": "SKU-001",
      "name": "Product Name",
      "asin": "B012345678",
      "price": 150.00,
      "quantity": 25,
      "status": "Active"
    }
  ],
  "total": 1
}
```

**Flow:**
1. Get cookies from SQLite
2. Validate session (navigate to /home, check for login redirect)
3. Navigate to `/inventory` with `wait_until="networkidle"`
4. Wait 3 seconds for content rendering
5. Extract products via JavaScript
6. Return structured data

### 2. Sync Orders

```bash
POST /api/v1/sync/orders?email=amazon_eg&days=30
```

**Response:**
```json
{
  "success": true,
  "orders": [
    {
      "amazon_order_id": "123-4567890-1234567",
      "created_at": "04/12/2026",
      "status": "Unshipped",
      "total": 150.00,
      "buyer_name": "Customer Name",
      "items": []
    }
  ],
  "total": 1
}
```

### 3. Sync Inventory

```bash
POST /api/v1/sync/inventory?email=amazon_eg
```

**Response:**
```json
{
  "success": true,
  "inventory": [
    {
      "sku": "SKU-001",
      "asin": "B012345678",
      "name": "Product Name",
      "available": 25,
      "reserved": 5,
      "inbound": 0,
      "fulfillment": "MFN",
      "fba": false,
      "fbm": true
    }
  ],
  "total": 1
}
```

## Error Handling

### Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),           # 3 attempts
    wait=wait_exponential(multiplier=2, min=4, max=30),  # 4s, 8s, 16s
    retry=retry_if_exception_type(...),   # Retry on timeouts
    reraise=False,                        # Return error dict instead of raising
)
async def sync_products(self, email: str) -> Dict[str, Any]:
    ...
```

### Session Validation

قبل كل sync:
1. Navigate to `/home`
2. Check if redirected to `/ap/signin` or `/gp/signin`
3. Check for login form (`#ap_email`)
4. If any detected → return "Session expired"

### CAPTCHA Detection

```python
async def _check_for_captcha(self) -> bool:
    has_captcha = await self.page.evaluate("""
        () => {
            const captchaElements = [
                '#captcha',
                '#captchacharacters',
                'form[action*="validateCaptcha"]',
                '.captcha-container',
            ];
            return captchaElements.some(sel => !!document.querySelector(sel));
        }
    """)
    return has_captcha
```

If CAPTCHA detected:
1. Wait 10 seconds
2. Retry (up to 3 attempts)

### Random Delays

```python
async def _random_delay(self):
    delay = random.uniform(3, 7)  # 3-7 seconds
    await asyncio.sleep(delay)
```

ده بيخلي الـ requests تبدي طبيعية وتتجنب rate limiting.

### Debug Mode

لو `debug=True`:
```python
scraper = CookieScraper(debug=True)
```

بيحفظ raw HTML في:
```
%TEMP%/crazy_lister/sync_debug/products_20260412_040000.html
%TEMP%/crazy_lister/sync_debug/orders_20260412_040000.html
%TEMP%/crazy_lister/sync_debug/inventory_20260412_040000.html
```

## JavaScript Extraction Strategy

### Multi-selector approach

بدلاً من selector واحد، بنجرب عدة selectors:

```javascript
const selectors = [
    'table tbody tr',           // Traditional tables
    '[role="row"]',             // ARIA grid rows
    '.inventory-row',           // Class-based
    '.data-grid-row',           // Data grid
    '[data-testid*="product"]', // Test IDs
    '.manage-inventory-table tbody tr',  // Specific tables
];

let rows = [];
for (const sel of selectors) {
    rows = document.querySelectorAll(sel);
    if (rows.length > 0) break;  // Stop at first match
}
```

### Pattern-based extraction

بدلاً من column positions، بنستخدم regex patterns:

```javascript
// SKU: ABC-12345
if (/^[A-Z0-9]+-[A-Z0-9\d]+/i.test(text)) {
    p.sku = text;
}
// ASIN: B0XXXXXXXX
else if (/^B[0-9A-Z]{9}$/.test(text)) {
    p.asin = text;
}
// Price
else if (/[\d,]+\.?\d*/.test(text)) {
    p.price = parseFloat(text.replace(/[^\d.]/g, ''));
}
```

## Cookie Injection

### Problem
`document.cookie` in JS only returns non-HttpOnly cookies (~24 cookies). Amazon needs HttpOnly cookies like `session-token`, `at-main` for API calls.

### Solution
Playwright's `context.add_cookies()` allows injecting cookies with `httpOnly: true` flag:

```python
await self.context.add_cookies([{
    "name": "session-token",
    "value": "...",
    "domain": ".amazon.eg",
    "path": "/",
    "httpOnly": True,  # ← Critical!
    "secure": True,
    "sameSite": "Lax",
}])
```

### Cookie Sources
1. **PyWebView Login**: Saves cookies from browser session
2. **Database**: Encrypted in SQLite (`sessions.cookies_json`)
3. **Decryption**: Using Fernet symmetric encryption

## Anti-detection

Playwright by default is detectable. We hide it via:

```python
await self.page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    window.chrome = {runtime: {}};
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['ar-EG', 'ar', 'en-US', 'en']});
""")
```

Plus:
- Random delays (3-7s)
- Realistic User-Agent
- Proper Accept-Language headers
- Viewport: 1920x1080

## Testing

### Unit Test
```bash
cd backend
python test_cookie_scraper.py
```

### API Test
```bash
# Products
curl -X POST "http://127.0.0.1:8765/api/v1/sync/products?email=amazon_eg"

# Orders
curl -X POST "http://127.0.0.1:8765/api/v1/sync/orders?email=amazon_eg&days=30"

# Inventory
curl -X POST "http://127.0.0.1:8765/api/v1/sync/inventory?email=amazon_eg"
```

### Debug Mode
```python
from app.services.cookie_scraper import CookieScraper

scraper = CookieScraper(debug=True)
result = await scraper.sync_products("amazon_eg")
```

Then check:
```
%TEMP%/crazy_lister/sync_debug/products_YYYYMMDD_HHMMSS.html
```

Open in browser to see what Amazon returned.

## Troubleshooting

### "No active session"
- تأكد إن المستخدم سجل دخول عبر PyWebView
- شوف الـ logs: `No active session for amazon_eg`
- الحل: سجل دخول تاني

### "Session expired"
- الـ cookies انتهت صلاحيتها
- الحل: سجل دخول تاني

### "CAPTCHA detected"
- Amazon اكتشف automated access
- النظام هيحاول 3 مرات مع delays
- لو لسه CAPTCHA: انتظر 30 دقيقة وحاول تاني

### "0 products"
- ممكن الحساب فاضي (مش مشكلة)
- أو الـ selectors مش بتطابق
- الحل: شغّل debug mode وشوف الـ HTML

### "TimeoutError"
- الإنترنت بطيء أو Amazon بيستغرق وقت
- Retry logic هيحاول 3 مرات
- لو لسه: زود الـ timeout في الكود

## Future Improvements

- [ ] Intercept internal JSON APIs (faster than DOM extraction)
- [ ] WebSocket support for real-time sync progress
- [ ] Cache last successful sync to avoid re-scraping
- [ ] Support for FBA inventory details
- [ ] Order details extraction (items, shipping address)
- [ ] Automatic selector discovery (scan page for data patterns)
- [ ] Proxy support for distributed scraping
