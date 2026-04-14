# 🔴 تقرير توجيهي — حالة SP-API الحالية والخطة المطلوبة

> **من:** مهندس الـ Backend  
> **إلى:** القائد التقني  
> **التاريخ:** 2026-04-14 02:05  
> **الأولوية:** 🔴 توجيهي — يحتاج قرار  

---

## 📊 الحالة الحالية — ملخص تنفيذي

### ✅ ما تم إنجازه (3 Features)

| الميزة | الحالة | الملفات |
|--------|--------|---------|
| **PUT** Listing (إنشاء/تحديث كامل) | ✅ كامل | `sp_api_client.py` + `/sp-api/submit/{product_id}` |
| **GET** Listing (منتج واحد) | ✅ كامل | `sp_api_client.py` + `/sp-api/listing/{sku}` |
| **GET** Product Type Schema | ✅ كامل | `sp_api_client.py` + `/sp-api/schema/{product_type}` |
| **DELETE** Listing (Service فقط) | ⚠️ نصف | `sp_api_client.py` موجود — **مفيش API endpoint** |

### ❌ ما ينقصنا (5 Features مطلوبة من Amazon Docs)

| الميزة | SP-API Endpoint | Service Layer | API Endpoint | الأولوية |
|--------|-----------------|---------------|-------------|----------|
| **بحث كل المنتجات** | `GET /listings/2021-08-01/items` | ⚠️ في `amazon_api.py` فقط | ❌ مفيش | ⭐⭐⭐ |
| **تحديث جزئي** | `PATCH /listings/2021-08-01/items/{sellerId}/{sku}` | ❌ مفيش | ❌ مفيش | ⭐⭐ |
| **حذف Listing** | `DELETE /listings/2021-08-01/items/{sellerId}/{sku}` | ✅ موجود | ❌ مفيش | ⭐⭐⭐ |
| **بحث Catalog (SP-API)** | `GET /catalog/2022-04-01/items` | ❌ مفيش (فيه scraping بديل) | ❌ مفيش (فيه scraping بديل) | ⭐⭐⭐ |
| **Catalog Item بـ ASIN** | `GET /catalog/2022-04-01/items/{asin}` | ❌ مفيش (فيه scraping بديل) | ❌ مفيش (فيه scraping بديل) | ⭐⭐ |

---

## 🔍 تحليل تفصيلي لكل ميزة ناقصة

### 1. 🔴 بحث كل المنتجات (Search Listings) — الأولوية القصوى

**الوضع الحالي:**
```
✅ Service: RealSPAPIClient.get_listings() في amazon_api.py (sku=None)
❌ Service: sp_api_client.py (العميل الأساسي) — مفيش search_listings_items
❌ API Endpoint: مفيش خالص
```

**المشكلة:**
- العميل الأساسي (`sp_api_client.py`) مش بيستخدم `python-amazon-sp-api` library
- بيعتمد على AWS SigV4 raw HTTP calls
- الـ `searchListingsItems` method محتاج يضاف يدوياً

**الحل المطلوب:**
```python
# في sp_api_client.py — إضافة method جديد
def search_listings_items(self, seller_id, marketplace_ids=None, skus=None, 
                           status=None, page_size=10):
    """
    GET /listings/2021-08-01/items/{sellerId}
    """
    path = f"/listings/2021-08-01/items/{seller_id}"
    params = {"marketplaceIds": marketplace_ids or [self.marketplace_id]}
    if skus:
        params["skus"] = ",".join(skus)
    if status:
        params["status"] = status
    if page_size:
        params["pageSize"] = page_size
    return self._make_request("GET", path, params=params)
```

```python
# في sp_api_router.py — إضافة endpoint جديد
@router.get("/listings")
async def search_listings(seller_id: str, skus: str = None, status: str = None):
    """Search all Amazon listings for a seller"""
    client = SPAPIClient()
    result = client.search_listings_items(
        seller_id=seller_id,
        skus=skus.split(",") if skus else None,
        status=status
    )
    return result
```

---

### 2. 🔴 حذف Listing (Delete Listing) — جاهز 67%

**الوضع الحالي:**
```
✅ Service: sp_api_client.py.delete_listing_item() — موجود (line 218)
✅ Service: sp_api.py.delete_listing() — موجود (line 218)
❌ API Endpoint: مفيش!
```

**الحل المطلوب (سهل جداً — 5 أسطر):**
```python
# في sp_api_router.py — إضافة endpoint
@router.delete("/listing/{seller_id}/{sku}")
async def delete_listing(seller_id: str, sku: str):
    """Delete a listing from Amazon"""
    client = SPAPIClient()
    result = client.delete_listing_item(seller_id, sku)
    return {"status": result.get("status"), "message": "Listing deleted"}
```

---

### 3. 🟡 تحديث جزئي (PATCH Listing) — محتاج من الصفر

**الوضع الحالي:**
```
❌ Service: مفيش
❌ API Endpoint: مفيش
```

**ليه مهم:**
- دلوقتي لو عايز تعدّل السعر بس → لازم تبعت الـ listing كامل (PUT)
- PATCH بيخلّي تعدّل حقل واحد من غير ما تبعت كل شيء
- أسرع وأأمن (أقل فرصة لـ race conditions)

**الحل المطلوب:**
```python
# في sp_api_client.py
def patch_listing_item(self, seller_id, sku, patches, marketplace_ids=None):
    """
    PATCH /listings/2021-08-01/items/{sellerId}/{sku}
    """
    path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
    params = {"marketplaceIds": marketplace_ids or [self.marketplace_id]}
    body = {"patches": patches}
    return self._make_request("PATCH", path, params=params, json=body)
```

```python
# في sp_api_router.py
@router.patch("/listing/{seller_id}/{sku}")
async def patch_listing(seller_id: str, sku: str, patches: List[dict]):
    """Partial update of a listing (e.g., price only)"""
    client = SPAPIClient()
    result = client.patch_listing_item(seller_id, sku, patches)
    return {"status": result.get("status")}
```

---

### 4. 🔴 بحث Catalog (SP-API) — فيه بديل scraper

**الوضع الحالي:**
```
❌ SP-API Catalog Items API: مفيش خالص
✅ بديل موجود: catalog_search.py (HTML scraping من Seller Central)
✅ Endpoint موجود: /catalog/search?query=...&search_type=...
```

**المشكلة مع الـ Scraping البديل:**
| المشكلة | التأثير |
|---------|---------|
| HTML scraping مش مستقر | ممكن يتكسر لو Amazon غيّرت الـ HTML |
| مش رسمي | Amazon ممكن تمنعه |
| محدود | مش كل البيانات متاحة |

**ميزة SP-API الرسمي:**
```
✅ بيانات أكمل (summaries, images, dimensions, identifiers)
✅ مستقر (API رسمي — مش هييتغير)
✅ أسرع (JSON مباشر مش HTML parsing)
✅ Rate limits واضحة (20 req/sec)
```

**الحل المطلوب:**
```python
# في sp_api_client.py
def search_catalog_items(self, marketplace_ids=None, keywords=None, 
                          identifiers=None, page_size=10):
    """
    GET /catalog/2022-04-01/items
    """
    path = "/catalog/2022-04-01/items"
    params = {"marketplaceIds": marketplace_ids or [self.marketplace_id]}
    if keywords:
        params["keywords"] = keywords
    if identifiers:
        params["identifiers"] = identifiers
    if page_size:
        params["pageSize"] = page_size
    return self._make_request("GET", path, params=params)
```

```python
# في sp_api_router.py — إضافة catalog router جديد
catalog_router = APIRouter()

@catalog_router.get("/search")
async def search_catalog(keywords: str, identifiers: str = None):
    """Search Amazon catalog via SP-API"""
    client = SPAPIClient()
    result = client.search_catalog_items(
        keywords=keywords,
        identifiers=identifiers.split(",") if identifiers else None
    )
    return result
```

---

### 5. 🟡 Catalog Item بـ ASIN (SP-API) — فيه بديل scraper

**الوضع الحالي:**
```
❌ SP-API: مفيش
✅ بديل: /catalog/lookup/{asin} (HTML scraping)
```

**الحل المطلوب:**
```python
# في sp_api_client.py
def get_catalog_item(self, asin, marketplace_ids=None, included_data=None):
    """
    GET /catalog/2022-04-01/items/{asin}
    """
    path = f"/catalog/2022-04-01/items/{asin}"
    params = {"marketplaceIds": marketplace_ids or [self.marketplace_id]}
    if included_data:
        params["includedData"] = ",".join(included_data)
    return self._make_request("GET", path, params=params)
```

---

## 📋 الخطة المقترحة — 3 مراحل

### المرحلة 1: عاجل (اليوم) — Features جاهزة 67%

| الميزة | الوقت | التعقيد |
|--------|-------|---------|
| DELETE Listing Endpoint | 10 دقائق | سهل جداً |
| Search Listings Endpoint | 30 دقيقة | متوسط |

**النتيجة:** المستخدم يقدر يبحث ويحذف listings من Amazon مباشرة

---

### المرحلة 2: قريبة (هذا الأسبوع) — Features جديدة

| الميزة | الوقت | التعقيد |
|--------|-------|---------|
| PATCH Listing Endpoint | 45 دقيقة | متوسط |

**النتيجة:** تعديل جزئي للسعر/الكمية من غير إعادة إرسال كل شيء

---

### المرحلة 3: متوسطة (هذا الشهر) — Catalog API

| الميزة | الوقت | التعقيد |
|--------|-------|---------|
| Catalog Search (SP-API) | 1 ساعة | متوسط |
| Catalog Item by ASIN (SP-API) | 30 دقيقة | سهل |

**النتيجة:** بحث رسمي في Amazon catalog من غير scraping

---

## 🎯 توصيتي

### نفدل دلوقتي (المرحلة 1):
1. ✅ **DELETE endpoint** — 5 أسطر، جاهز 100%
2. ✅ **Search listings endpoint** — 20 سطر، محتاج بس نربط

### بعدين (المرحلة 2-3):
3. ⏳ PATCH endpoint
4. ⏳ Catalog SP-API (نحط scraping كـ fallback)

---

## ❓ أسئلة للقائد التقني

### السؤال 1: الأولوية
```
أيهما أهم دلوقتي؟

أ) DELETE + Search Listings (المرحلة 1 فقط)
ب) كل الـ 5 features مرة واحدة
ج) نركز على حاجة تانية (حددها)
```

### السؤال 2: Catalog Search
```
الـ catalog search الحالي (scraping) شغال؟

أ) أيه شغال — نسيبه ونركز على SP-API
ب) لا مش شغال — نصلحه الأول
ج) نستبدله بـ SP-API بالكامل
```

### السؤال 3: Frontend Integration
```
هل الـ Frontend جاهز يستقبل الـ endpoints الجديدة؟

أ) أيه — فيه UI جاهز
ب) لا — محتاج نبنيه
ج) مش محتاجين UI دلوقتي (backend فقط)
```

---

## 📁 الملفات اللي هتتعدّل

| الملف | التعديل | الأسطر المتوقعة |
|-------|---------|-----------------|
| `sp_api_client.py` | إضافة 4 methods | +80 |
| `sp_api_router.py` | إضافة 4 endpoints | +60 |
| `catalog_router` | جديد أو تعديل | +40 |

---

**في انتظار توجيهاتك!** 🙏
