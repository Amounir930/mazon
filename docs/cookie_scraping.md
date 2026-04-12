# Cookie-based Scraping Engine

## نظرة عامة

نظام مزامنة كامل باستخدام الـ Cookies من غير SP-API. بيستخدم نفس الـ cookies اللي الـ PyWebView حفظها عشان يسحب البيانات من صفحات Amazon Seller Central.

## المعمارية

```
┌──────────────────────────────────────────────────────────┐
│                   Browser Session (PyWebView)             │
│  ✅ Amazon Egypt Login → 24 cookies في SQLite مشفرة      │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│              CookieScraper Engine                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Products    │  │   Orders     │  │  Inventory   │   │
│  │  Scraper     │  │   Scraper    │  │   Scraper    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         └────────────────┴─────────────────┘            │
│                   niquests + Cookies                    │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│              SQLite Database                              │
│  products | orders | inventory | sessions                │
└──────────────────────────────────────────────────────────┘
```

## الملفات الأساسية

| الملف | الوظيفة |
|------|---------|
| `backend/app/services/cookie_scraper.py` | المحرك الأساسي للـ Scraping |
| `backend/app/api/products_sync.py` | الـ API Endpoints للـ Sync |
| `backend/app/models/order.py` | Order Model |
| `backend/app/models/inventory.py` | Inventory Model |
| `backend/app/migrations.py` | Database Migrations |

## API Endpoints

### 1. Sync Products
```bash
POST /api/v1/sync/products?email=user@email.com

Response:
{
  "success": true,
  "synced": 150,
  "total": 150,
  "products": [...]
}
```

### 2. Sync Orders
```bash
POST /api/v1/sync/orders?email=user@email.com&days=30

Response:
{
  "success": true,
  "synced": 50,
  "total": 50,
  "orders": [...]
}
```

### 3. Sync Inventory
```bash
POST /api/v1/sync/inventory?email=user@email.com

Response:
{
  "success": true,
  "synced": 100,
  "total": 100,
  "inventory": [...]
}
```

## طريقة الاستخدام

### 1. تسجيل الدخول (PyWebView)
```python
from app.services.browser_auth import BrowserAuth

# فتح نافذة تسجيل الدخول
auth = BrowserAuth()
await auth.login(country_code="eg")
```

### 2. مزامنة المنتجات
```python
from app.services.cookie_scraper import CookieScraper

scraper = CookieScraper()
result = await scraper.sync_products("user@email.com")
scraper.close()

print(f"Synced {result['total']} products")
```

### 3. مزامنة الطلبات
```python
result = await scraper.sync_orders("user@email.com", days=30)
print(f"Synced {result['total']} orders from last 30 days")
```

### 4. مزامنة المخزون
```python
result = await scraper.sync_inventory("user@email.com")
print(f"Synced {result['total']} inventory items")
```

## Error Handling

### أنواع الأخطاء المتوقع

| الخطأ | السبب | الحل |
|------|------|------|
| Session expired | الـ cookies انتهت | يرجع رسالة "سجّل دخول تاني" |
| CAPTCHA | Requests كتير | ينتظر 30 ثانية ويحاول تاني |
| Rate limit | Amazon بيمنع scraping | ينتظر 5-10 ثواني بين requests |
| HTML changed | Amazon غيّر التصميم | يسجل error ويرجع آخر بيانات محفوظة |
| Network error | إنترنت قطع | يحاول 3 مرات مع delay |

### مثال على التعامل مع الأخطاء
```python
from app.services.cookie_scraper import CookieScraper

scraper = CookieScraper()
result = await scraper.sync_products("user@email.com")

if not result["success"]:
    error = result["error"]
    if "Session expired" in error:
        print("الجلسة انتهت - سجل دخول تاني")
    elif "Failed to fetch" in error:
        print("مشكلة في الشبكة - حاول تاني")
    else:
        print(f"خطأ غير معروف: {error}")
```

## Rate Limiting

النظام بيستخدم delays تلقائية بين الـ requests:
- **Products**: 2 ثانية بين كل صفحة
- **Orders**: 3 ثانية بين كل صفحة
- **Inventory**: 2 ثانية بين كل صفحة

## Pagination

النظام بيhandle pagination تلقائياً:
```python
# يسحب كل المنتجات (max 10 صفحات)
result = await scraper.sync_products("user@email.com", max_pages=10)

# يسحب أول صفحتين بس
result = await scraper.sync_products("user@email.com", max_pages=2)
```

## Database Schema

### orders table
```sql
CREATE TABLE orders (
    id VARCHAR(36) PRIMARY KEY,
    seller_id VARCHAR(36),
    amazon_order_id VARCHAR(50) NOT NULL UNIQUE,
    order_status VARCHAR(30) DEFAULT 'Pending',
    total NUMERIC(10, 2) DEFAULT 0,
    buyer_name VARCHAR(200),
    purchase_date TIMESTAMP,
    items TEXT,  -- JSON
    source VARCHAR(20) DEFAULT 'cookie',
    ...
);
```

### inventory table
```sql
CREATE TABLE inventory (
    id VARCHAR(36) PRIMARY KEY,
    seller_id VARCHAR(36),
    product_id VARCHAR(36),
    sku VARCHAR(100) NOT NULL,
    asin VARCHAR(20),
    available INTEGER DEFAULT 0,
    reserved INTEGER DEFAULT 0,
    inbound INTEGER DEFAULT 0,
    fba BOOLEAN DEFAULT FALSE,
    fbm BOOLEAN DEFAULT TRUE,
    source VARCHAR(20) DEFAULT 'cookie',
    ...
);
```

## Testing

### 1. تشغيل الـ Backend
```bash
cd backend
python -m app.main
```

### 2. اختبار الـ Endpoints
```bash
# Products
curl -X POST "http://127.0.0.1:8765/api/v1/sync/products?email=amazon_eg"

# Orders
curl -X POST "http://127.0.0.1:8765/api/v1/sync/orders?email=amazon_eg&days=30"

# Inventory
curl -X POST "http://127.0.0.1:8765/api/v1/sync/inventory?email=amazon_eg"
```

### 3. التحقق من Database
```bash
sqlite3 ~/.config/CrazyLister/crazy_lister.db
SELECT count(*) FROM products;
SELECT count(*) FROM orders;
SELECT count(*) FROM inventory;
```

## Dependencies

```
tenacity>=8.2.0        # Retry logic
beautifulsoup4>=4.12.0 # HTML parsing
niquests>=3.18.0       # HTTP client
cryptography>=41.0.0   # Cookie encryption
```

## Security

- **Cookies مشفرة**: باستخدام Fernet symmetric encryption
- **مفتاح التشفير**: محفوظ في `%APPDATA%/CrazyLister/session.key`
- **Session validation**: بيتأكد من صلاحية الـ cookies قبل كل sync
- **No hardcoded secrets**: كل الـ credentials في SQLite encrypted

## Future Improvements

- [ ] إضافة WebSocket للـ real-time progress
- [ ] دعم الـ AJAX API endpoints (Amazon بيستخدمها كتير)
- [ ] إضافة caching للـ HTML parsing
- [ ] دعم الـ FBA inventory details
- [ ] إضافة order details scraping (items, shipping)
- [ ] دعم الـ images extraction من product pages

## Troubleshooting

### Session expired
```
الحل: سجل دخول تاني عبر PyWebView
```

### No products found
```
الأسباب المحتملة:
1. Amazon غير الـ HTML structure
2. الجدول مش موجود في الصفحة
3. الـ cookies مش صحيحة

الحل: شوف الـ logs وحلل الـ HTML
```

### Rate limited
```
النظام بيhandle ده تلقائياً بالـ retry logic
لو المشكلة مستمرة: زود الـ delay بين الـ requests
```

## Logs

كل الـ logs محفوظة في stderr وممكن تتابعها:
```
2026-04-12 03:00:00 | INFO | Scraped 150 products from Amazon
2026-04-12 03:00:01 | INFO | Upserted 150 products to database
2026-04-12 03:00:02 | INFO | Cookie sync: 150 products synced for user@email.com
```
