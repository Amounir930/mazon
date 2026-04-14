# 🎯 خطة تنفيذية — SP-API Features الكاملة

> **من:** القائد التقني  
> **التاريخ:** 2026-04-14  
> **الحالة:** ⏳ بانتظار الموافقة  
> **الأولوية:** 🔴 عاجل

---

## 📊 تحليل الوضع الحالي

### ✅ الموجود (Working)

| الميزة | Service Layer | API Endpoint | الحالة |
|--------|--------------|--------------|--------|
| PUT Listing | `sp_api_client.py.create_listing_from_product()` | `/sp-api/submit/{product_id}` | ✅ كامل |
| GET Listing (SKU) | `sp_api_client.py.get_listing_item()` | `/sp-api/listing/{sku}` | ✅ كامل |
| GET Schema | `sp_api_client.py.get_product_type_definitions()` | `/sp-api/schema/{product_type}` | ✅ كامل |
| DELETE Listing | `sp_api_client.py.delete_listing_item()` | ❌ **مفيش** | ⚠️ Service فقط |
| Search Listings | `amazon_api.py.get_listings(sku=None)` | ❌ **مفيش** | ⚠️ Service فقط |
| Catalog Search | `catalog_search.py` (Scraping) | `/catalog/search` | ✅ Scraping بديل |
| Catalog Lookup | `catalog_search.py` (Scraping) | `/catalog/lookup/{asin}` | ✅ Scraping بديل |

### ❌ الناقص (Missing)

| الميزة | SP-API | Service | API | الأولوية |
|--------|--------|---------|-----|----------|
| DELETE Endpoint | ✅ موجود | ✅ موجود | ❌ **مفيش** | 🔴 P0 |
| Search Listings | ✅ في `amazon_api.py` | ⚠️ `RealSPAPIClient` فقط | ❌ **مفيش** | 🔴 P0 |
| PATCH Listing | ✅ موجود | ❌ مفيش | ❌ مفيش | 🟡 P1 |
| Catalog SP-API | ✅ موجود | ❌ مفيش | ❌ مفيش | 🟢 P2 |

---

## 🔍 تحليل معماري مهم

### مشكلة مزدوجة الـ Clients

عندنا **3 ملفات** بتعمل نفس الوظيفة:

| الملف | الطريقة | الحالة |
|-------|---------|--------|
| `sp_api_client.py` | Raw HTTP + AWS SigV4 | ✅ المُستخدم حالياً |
| `sp_api.py` | `python-amazon-sp-api` library | ⚠️ موجود بس مش مُستخدم |
| `amazon_api.py` | Hybrid (Real + Mock) | ⚠️ فيه `get_listings` بس |

**القرار:** هنستخدم `sp_api_client.py` كمصدروحيد (Single Source of Truth) لأنه:
1. ✅ شغال بالفعل مع الـ endpoints الحالية
2. ✅ مش معتمد على مكتبة خارجية (`python-amazon-sp-api` مش مثبتة)
3. ✅ بيستخدم AWS SigV4 مباشرة (أكثر شفافية)

---

## 🏗️ الخطة التنفيذية — 3 مراحل

### المرحلة 1: عاجل (اليوم) — P0

#### 1.1 DELETE Listing Endpoint
```
الملف: sp_api_router.py
التعديل: إضافة 1 endpoint
الأسطر: +15
التعقيد: سهل جداً
```

**الكود المطلوب:**
```python
@router.delete("/listing/{seller_id}/{sku}")
async def delete_listing(seller_id: str, sku: str):
    """
    Delete a listing from Amazon SP-API.
    
    API: DELETE /listings/2021-08-01/items/{sellerId}/{sku}
    Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#deletelistingsitem
    """
    db = SessionLocal()
    try:
        # Get session credentials
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
        ).order_by(AuthSession.created_at.desc()).first()

        if not auth_session:
            raise HTTPException(status_code=400, detail="No active session")

        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"

        # Call SP-API
        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        result = client.delete_listing_item(seller_id, sku)

        return {
            "success": True,
            "status": result.get("status", "ACCEPTED"),
            "message": f"Listing deleted: SKU={sku}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

---

#### 1.2 Search Listings Endpoint
```
الملف: sp_api_router.py
التعديل: إضافة 1 method في sp_api_client.py + 1 endpoint
الأسطر: +40
التعقيد: متوسط
```

**أولاً: إضافة method في `sp_api_client.py`:**
```python
def search_listings_items(self, seller_id: str, skus: list = None,
                           status: str = None, page_size: int = 10) -> Dict[str, Any]:
    """
    Search/list all listings for a seller.

    API: GET /listings/2021-08-01/items/{sellerId}
    Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#searchlistingsitems
    """
    path = f"/listings/2021-08-01/items/{seller_id}"
    params = {"marketplaceIds": self.marketplace_id}
    
    if skus:
        params["skus"] = ",".join(skus)
    if status:
        params["status"] = status  # ACTIVE, INCOMPLETE, INACTIVE
    if page_size:
        params["pageSize"] = min(page_size, 200)  # Amazon limit

    return self._make_request("GET", path, params=params)
```

**ثانياً: إضافة endpoint في `sp_api_router.py`:**
```python
@router.get("/listings")
async def search_listings(
    seller_id: str = None,
    skus: str = None,
    status: str = None,
    page_size: int = 10
):
    """
    Search all Amazon listings for a seller.
    
    Query params:
    - seller_id: Amazon Seller ID (required)
    - skus: Comma-separated SKUs to filter (optional)
    - status: ACTIVE, INCOMPLETE, or INACTIVE (optional)
    - page_size: Number of results (default: 10, max: 200)
    """
    db = SessionLocal()
    try:
        if not seller_id:
            # Fallback to session credentials
            auth_session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.is_active == True,
            ).order_by(AuthSession.created_at.desc()).first()

            if not auth_session:
                raise HTTPException(status_code=400, detail="No active session")

            credentials = json.loads(decrypt_data(auth_session.credentials_json))
            seller_id = credentials.get("seller_id")
            marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
            country_code = auth_session.country_code or "eg"
        else:
            marketplace_id = os.getenv("SP_API_MARKETPLACE_ID", "ARBP9OOSHTCHU")
            country_code = os.getenv("SP_API_COUNTRY", "eg")

        if not seller_id:
            raise HTTPException(status_code=400, detail="seller_id required")

        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        result = client.search_listings_items(
            seller_id=seller_id,
            skus=skus.split(",") if skus else None,
            status=status,
            page_size=page_size
        )

        return {
            "success": True,
            "seller_id": seller_id,
            "total_results": len(result.get("items", [])),
            "items": result.get("items", []),
            "pagination": result.get("pagination", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search listings error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

---

### المرحلة 2: قريب (هذا الأسبوع) — P1

#### 2.1 PATCH Listing Endpoint
```
الملفات: sp_api_client.py (+25 أسطر) + sp_api_router.py (+30 أسطر)
التعقيد: متوسط
```

**أولاً: إضافة method في `sp_api_client.py`:**
```python
def patch_listing_item(self, seller_id: str, sku: str, patches: list,
                        marketplace_ids: list = None) -> Dict[str, Any]:
    """
    Partial update of a listing item.

    API: PATCH /listings/2021-08-01/items/{sellerId}/{sku}
    Docs: https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-reference#patchlistingsitem

    Args:
        seller_id: Amazon Seller ID
        sku: Product SKU
        patches: List of patch operations
            Example: [
                {"op": "replace", "path": "/attributes/purchasable_offer/0/our_price/0/schedule/0/value_with_tax", "value": 150},
                {"op": "replace", "path": "/attributes/quantity/0/value", "value": 50}
            ]

    Returns:
        {
            "status": "ACCEPTED" | "INVALID",
            "issues": [...],
            "sku": "...",
        }
    """
    path = f"/listings/2021-08-01/items/{seller_id}/{sku}"
    params = {
        "marketplaceIds": marketplace_ids or self.marketplace_id,
        "issueLocale": "ar_AE",
    }

    # SP-API expects body with 'patches' key
    body = {"patches": patches}

    logger.info(f"Patching listing: SKU={sku}, patches={len(patches)}")
    return self._make_request("PATCH", path, data=body, params=params)
```

**ملاحظة:** لازم نضيف دعم `PATCH` في `_make_request`:
```python
# في _make_request method — إضافة:
elif method == "PATCH":
    response = requests.patch(url, headers=headers, json=data, params=params, auth=aws_auth, timeout=30)
```

**ثانياً: إضافة endpoint في `sp_api_router.py`:**
```python
class PatchListingRequest(BaseModel):
    patches: list[dict]


@router.patch("/listing/{seller_id}/{sku}")
async def patch_listing(seller_id: str, sku: str, request: PatchListingRequest):
    """
    Partial update of a listing (e.g., price or quantity only).
    
    Patches format:
    [
        {"op": "replace", "path": "/attributes/purchasable_offer/0/our_price/0/schedule/0/value_with_tax", "value": 150},
        {"op": "replace", "path": "/attributes/quantity/0/value", "value": 50}
    ]
    """
    db = SessionLocal()
    try:
        auth_session = db.query(AuthSession).filter(
            AuthSession.auth_method == "browser",
            AuthSession.is_active == True,
        ).order_by(AuthSession.created_at.desc()).first()

        if not auth_session:
            raise HTTPException(status_code=400, detail="No active session")

        credentials = json.loads(decrypt_data(auth_session.credentials_json))
        marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
        country_code = auth_session.country_code or "eg"

        if not request.patches:
            raise HTTPException(status_code=400, detail="patches required")

        client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
        result = client.patch_listing_item(seller_id, sku, request.patches)

        issues = result.get("issues", [])
        errors = [i for i in issues if i.get("severity") == "ERROR"]

        return {
            "success": len(errors) == 0,
            "status": result.get("status", "UNKNOWN"),
            "errors": errors,
            "message": "Listing updated" if len(errors) == 0 else "Patch failed",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Patch listing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

---

### المرحلة 3: متوسط (هذا الشهر) — P2

#### 3.1 Catalog Search SP-API
```
الملفات: sp_api_client.py (+30 أسطر) + catalog_router جديد (+25 أسطر)
التعقيد: متوسط
```

**أولاً: إضافة method في `sp_api_client.py`:**
```python
def search_catalog_items(self, keywords: str = None, identifiers: list = None,
                          page_size: int = 10, included_data: list = None) -> Dict[str, Any]:
    """
    Search Amazon catalog via SP-API.

    API: GET /catalog/2022-04-01/items
    Docs: https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-reference#searchcatalogitems

    Args:
        keywords: Search keywords (e.g., "wireless headphones")
        identifiers: List of identifiers (EAN, UPC, ISBN, etc.)
        page_size: Number of results (default: 10, max: 20)
        included_data: Additional data to include
            Options: ["summaries", "images", "dimensions", "identifiers", "links"]

    Returns:
        {
            "numberOfResults": int,
            "pagination": {...},
            "items": [...]
        }
    """
    path = "/catalog/2022-04-01/items"
    params = {"marketplaceIds": self.marketplace_id}

    if keywords:
        params["keywords"] = keywords
    if identifiers:
        params["identifiers"] = ",".join(identifiers)
    if page_size:
        params["pageSize"] = min(page_size, 20)  # Amazon limit
    if included_data:
        params["includedData"] = ",".join(included_data)

    return self._make_request("GET", path, params=params)
```

**ثانياً: إضافة endpoints جديدة في `sp_api_router.py`:**
```python
@router.get("/catalog/search")
async def search_catalog(
    keywords: str = None,
    identifiers: str = None,
    page_size: int = 10,
    use_sp_api: bool = True
):
    """
    Search Amazon catalog.
    
    If use_sp_api=True: Use official SP-API Catalog Items API
    If use_sp_api=False: Fallback to Seller Central scraping
    """
    db = SessionLocal()
    try:
        if use_sp_api:
            # SP-API approach
            auth_session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.is_active == True,
            ).order_by(AuthSession.created_at.desc()).first()

            if not auth_session:
                raise HTTPException(status_code=400, detail="No active session")

            marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
            country_code = auth_session.country_code or "eg"

            client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
            result = client.search_catalog_items(
                keywords=keywords,
                identifiers=identifiers.split(",") if identifiers else None,
                page_size=page_size,
                included_data=["summaries", "images", "identifiers"]
            )

            return {
                "success": True,
                "method": "SP-API",
                "total_results": result.get("numberOfResults", 0),
                "items": result.get("items", []),
            }
        else:
            # Fallback to scraping (existing implementation)
            from app.api.catalog_search import search_catalog as search_catalog_legacy
            return await search_catalog_legacy(
                query=keywords or identifiers,
                search_type="KEYWORD"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/catalog/{asin}")
async def get_catalog_item_by_asin(asin: str, use_sp_api: bool = True):
    """
    Get catalog item details by ASIN.
    
    If use_sp_api=True: Use official SP-API
    If use_sp_api=False: Fallback to Seller Central scraping
    """
    db = SessionLocal()
    try:
        if use_sp_api:
            auth_session = db.query(AuthSession).filter(
                AuthSession.auth_method == "browser",
                AuthSession.is_active == True,
            ).order_by(AuthSession.created_at.desc()).first()

            if not auth_session:
                raise HTTPException(status_code=400, detail="No active session")

            marketplace_id = auth_session.marketplace_id or "ARBP9OOSHTCHU"
            country_code = auth_session.country_code or "eg"

            client = SPAPIClient(marketplace_id=marketplace_id, country_code=country_code)
            result = client.get_catalog_item(
                asin=asin,
                included_data=["summaries", "images", "dimensions", "identifiers"]
            )

            return {
                "success": True,
                "method": "SP-API",
                "asin": asin,
                "item": result,
            }
        else:
            # Fallback to scraping
            from app.api.catalog_search import lookup_asin as lookup_asin_legacy
            return await lookup_asin_legacy(asin=asin)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog lookup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
```

**ثالثاً: إضافة method `get_catalog_item` في `sp_api_client.py`:**
```python
def get_catalog_item(self, asin: str, marketplace_ids: list = None,
                      included_data: list = None) -> Dict[str, Any]:
    """
    Get catalog item by ASIN.

    API: GET /catalog/2022-04-01/items/{asin}
    Docs: https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2022-04-01-reference#getcatalogitem
    """
    path = f"/catalog/2022-04-01/items/{asin}"
    params = {"marketplaceIds": marketplace_ids or self.marketplace_id}

    if included_data:
        params["includedData"] = ",".join(included_data)

    return self._make_request("GET", path, params=params)
```

---

## 📋 ملخص التعديلات

| الملف | المرحلة | التعديل | أسطر متوقعة |
|-------|---------|---------|-------------|
| `sp_api_client.py` | 1 | `search_listings_items()` | +20 |
| `sp_api_client.py` | 1.5 | `PATCH` support in `_make_request` | +2 |
| `sp_api_client.py` | 2 | `patch_listing_item()` | +25 |
| `sp_api_client.py` | 3 | `search_catalog_items()` + `get_catalog_item()` | +50 |
| `sp_api_router.py` | 1 | `DELETE /listing/{seller_id}/{sku}` | +20 |
| `sp_api_router.py` | 1 | `GET /listings` | +40 |
| `sp_api_router.py` | 2 | `PATCH /listing/{seller_id}/{sku}` + model | +35 |
| `sp_api_router.py` | 3 | `GET /catalog/search` + `GET /catalog/{asin}` | +70 |
| **المجموع** | | **8 تعديلات** | **~262 سطر** |

---

## 🎯 ترتيب التنفيذ

```
✅ المرحلة 1 (عاجل — اليوم):
  1.1 DELETE endpoint  ← 10 دقائق
  1.2 Search listings endpoint  ← 30 دقيقة

⏳ المرحلة 2 (هذا الأسبوع):
  2.1 PATCH endpoint  ← 45 دقيقة

⏳ المرحلة 3 (هذا الشهر):
  3.1 Catalog Search SP-API  ← 1 ساعة
  3.2 Catalog Item by ASIN  ← 30 دقيقة
```

---

## 🧪 خطة الاختبار

### لكل مرحلة:

```
1. Unit Tests:
   - Test method calls with mock responses
   - Test error handling (4xx, 5xx)
   - Test edge cases (empty results, pagination)

2. Integration Tests:
   - Call real SP-API endpoints (staging if available)
   - Verify response structure
   - Test with real product data

3. API Tests (via curl/Postman):
   - Test each new endpoint
   - Verify authentication
   - Test error scenarios
```

---

## ⚠️ المخاطر والحلول

| الخطر | الاحتمال | الحل |
|-------|---------|------|
| SP-API rate limits | عالي | إضافة retry logic + exponential backoff |
| Session expiry | متوسط | التحقق من الجلسة قبل كل request |
| Pagination handling | متوسط | دعم `nextToken` في الـ responses |
| Mock vs Real API | منخفض | `sp_api_client.py` بيشتغل مع الاثنين |

---

## ❓ أسئلة للموافقة

### السؤال 1: نطاق التنفيذ
```
هل نبدأ بـ المرحلة 1 فقط (عاجل) ولا كل المراحل؟

أ) المرحلة 1 فقط (اليوم) ← الأسرع والأأمن
ب) المرحلة 1 + 2 (اليوم + الأسبوع)
ج) كل المراحل مرة واحدة
```

### السؤال 2: Catalog SP-API
```
الـ Catalog scraping الحالي شغال؟ نستخدمه كـ fallback؟

أ) أيه شغال — نضيف SP-API كـ option إضافي (use_sp_api param)
ب) نستبدله بالكامل بـ SP-API
ج) نسيبه كما هو (مش أولوية دلوقتي)
```

### السؤال 3: الاختبارات
```
هل تريد اختبارات وحدة (unit tests) مع كل مرحلة؟

أ) أيه — tests إلزامية لكل feature
ب) لا — نختبر يدوياً الأول
ج) نضيف tests بعدين (technical debt)
```

---

**في انتظار موافقتك للبدء! 🙏**
