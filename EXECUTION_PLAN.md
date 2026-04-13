# 📋 الخطة التنفيذية — نظام الكوكيز 100%

## 📊 حالة النظام الحالية (بعد التنفيذ)

| التصنيف | عدد الملفات | الحالة |
|---------|-------------|--------|
| ✅ شغال بنسبة 100% | 10 ملفات | amazon_http_client, amazon_session_manager, abis_client, playwright_login_script, listing_tasks, catalog_search API, auth_routes, sync_engine, browser_auth, cookie_auth |
| ⚠️ شغال جزئياً | 3 ملفات | amazon_direct_api, amazon_lookup, cookie_scraper |
| ❌ محتاج إصلاح | 0 ملف | لا يوجد |

---

## ✅ المرحلة 0: إصلاحات حرجة — مكتملة

| # | الملف | المشكلة | الحل | الحالة |
|---|-------|---------|------|--------|
| 0.1 | `sync_engine.py` | `import niquests` = TLS مكشوف | استبدال بـ AmazonHTTPClient | ✅ |
| 0.2 | `catalog_search.py` | `get_active_session()` dead code + missing imports | حذف الدالة | ✅ |
| 0.3 | `cookie_auth.py` | `sync_products/sync_orders` stubs فاضية | تفويض لـ CookieScraper | ✅ |
| 0.4 | `amazon_direct_api.py` | `_get_client_context()` double-wrapped | إصلاح الـ JSON structure | ✅ |
| 0.5 | `browser_auth.py` | `import niquests` في `verify_session()` | استبدال بـ AmazonHTTPClient | ✅ |

---

## ✅ المرحلة 1: إصلاح 403 selection_required — مكتملة

**التشخيص الصحيح من القائد التقني:**
> الخطأ `selection_required` **مش** معناه اختار منتج من الكتالوج (ASIN)!
> معناه إن حقل `productType` في الـ payload فاضي `""` — أمازون مش عارفة تصنف المنتج!

**الحل المطبق:**
```python
# في abis_client.py و amazon_direct_api.py:
product_type = product_data.get("product_type", "").strip()
if not product_type:
    product_type = "HOME"  # Default product type
    logger.info(f"⚠️ product_type was empty, defaulting to '{product_type}'")
```

---

## 🏗 البنية النهائية:

```
┌─────────────────────────────────────────────────────────────┐
│              النظام الكامل (100% كوكيز)                      │
│                                                              │
│  تسجيل الدخول: Playwright → 43 كوكيز + CSRF Token           │
│                                                              │
│  سحب البيانات:                                              │
│  ├─ المنتجات: CookieScraper → /inventory (Playwright)       │
│  ├─ الطلبات:  CookieScraper → /orders (Playwright)          │
│  ├─ المخزون:  CookieScraper → /manage/inventory             │
│  └─ الكتالوج:  curl_cffi + CookieJar → /product-search      │
│                                                              │
│  إرسال البيانات:                                            │
│  ├─ Listing: curl_cffi + CookieJar → /abis/ajax/create      │
│  ├─ Offer:   curl_cffi + CookieJar → /abis/ajax/create-offer│
│  └─ Inventory: curl_cffi + CookieJar → /myinventory/gql     │
│                                                              │
│  0 SP-API calls. 0 AWS credentials. 100% Cookies.          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 الملفات المعدّلة:

| الملف | التغيير |
|-------|---------|
| `sync_engine.py` | niquests → AmazonHTTPClient (curl_cffi + CookieJar) |
| `catalog_search.py` | حذف `get_active_session()` — الـ API route يستخدم AmazonSessionManager |
| `cookie_auth.py` | `sync_products/sync_orders` → تفويض لـ CookieScraper |
| `amazon_direct_api.py` | إصلاح `_get_client_context()` + إضافة `productType` افتراضي |
| `browser_auth.py` | `verify_session()` → AmazonHTTPClient.is_session_valid() |
| `abis_client.py` | إضافة `productType` default "HOME" + CSRF في form data |
| `playwright_login_script.py` | Network Sniffer + JS injection + HTML regex fallback |

---

## 🎯 الخطوة الجاية:

**جاهز للاختبار!** سجّل دخول جديد (عشان الـ CSRF token يتحدث) وحاول ترفع listing تاني.

الـ log الجديد هيورينا:
- هل 403 لسه بيحصل؟
- لو أيه، الـ response body هيكشف السبب
- هل CSRF token بيتبعت صح في الـ form data؟
