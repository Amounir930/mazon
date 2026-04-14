# 🔴 تقرير عاجل — مشكلة EAN/UPC في SP-API Submission

> **من:** مهندس الـ Backend
> **إلى:** القائد التقني
> **التاريخ:** 2026-04-14 01:35
> **الأولوية:** 🔴 حرجة

---

## 📋 ملخص المشكلة

الـ SP-API submission بيفشل بـ `INVALID` بسبب 2 حقول ناقصة:

```
❌ 'معرف المنتج الخارجي' مطلوب لكنه مفقود
❌ 'رقم تعريف أمازون القياسي (ASIN) المقترح للتاجر' مطلوب لكنه مفقود
```

يعني:
- `externally_assigned_product_identifier` (EAN/UPC) مش بيتبعت
- `merchant_suggested_asin` مش بيتبعت

---

## 🔍 التحليل الجنائي

### ما تم تأكيده:

| البند | الحالة | الدليل |
|-------|--------|--------|
| SP-API Client شغال | ✅ | `test_integration.py` بيرجع ACCEPTED |
| `.env` بيتحمل | ✅ | `load_dotenv` في `sp_api_router.py` |
| Backend server شغال | ✅ | بيقبل الطلبات بيرد 200/500 |
| المنتج `prod-0923F1ECDX0` موجود | ✅ | الـ API بيرده |

### المشكلة المؤكدة:

**المنتج بيوصل لـ `_build_listing_payload()` بـ `ean = ""` (فاضي)**

### الأدلة:

1. **بعد الـ PUT** لتحديث المنتج:
```bash
curl -X PUT /api/v1/products/prod-0923F1ECDX0 -d '{"ean": "1245768907654", ...}'
# Response بيرد بـ: "ean": "1245768907654" ✅
```

2. **بعد كده في الـ submission**:
```
❌ 'معرف المنتج الخارجي' مطلوب لكنه مفقود
```
يعني `ean` بيوصل لـ `_build_listing_payload` **كـ string فاضي `""`**

3. **في `_build_listing_payload()`**:
```python
ean = product_data.get("ean", "").strip()
# ...
if ean:  # ← لو ean = "" → الشرط ده هيكون False
    attributes["externally_assigned_product_identifier"] = [...]
```

---

## 🎯 السبب المحتمل (3 سيناريوهات):

### السيناريو 1: SQLAlchemy Model مش بيقرأ EAN صح ⭐⭐⭐
| الاحتمال | عالي |
|----------|------|
| **الوصف** | الـ `ean` column في `Product` model موجود في الـ DB لكن SQLAlchemy مش بيرجعه صح |
| **الدليل** | كل محاولات قراءة EAN من Python رجعت output فاضي (حتى مع `python -u -c`) |
| **الحل** | مراجعة `backend/app/models/product.py` والتأكد من تعريف الـ column |

### السيناريو 2: PUT Endpoint مش بيحفظ EAN ⭐⭐
| الاحتمال | متوسط |
|----------|--------|
| **الوصف** | الـ PUT endpoint بيرجع EAN في الـ response لكن مش بيحفظه فعلاً في الـ DB |
| **الدليل** | الـ Response فيه EAN لكن الـ submission مش شايفه |
| **الحل** | مراجعة `backend/app/api/products.py` → الـ PUT handler |

### السيناريو 3: الـ Product ID في الـ task مختلف ⭐
| الاحتمال | منخفض |
|----------|--------|
| **الوصف** | الـ task بيستخدم `product_id` مختلف عن اللي احنا حدّثناه |
| **الدليل** | الـ task بيستخدم `prod-0923F1ECDX0` — نفس اللي حدّثناه |
| **الحل** | مطابقة الـ IDs بين الـ request والـ DB |

---

## 🛠️ الخطوات المطلوبة من القائد التقني:

### أولاً: تحقق من Product Model
```python
# في backend/app/models/product.py
# لازم يكون فيه:
ean = Column(String(13), nullable=True)
upc = Column(String(12), nullable=True)
```

### ثانياً: تحقق من PUT Handler
```python
# في backend/app/api/products.py
# الـ PUT handler لازم يعمل:
product.ean = data.get("ean", product.ean)
db.commit()
db.refresh(product)  # ← مهم جداً!
```

### ثالثاً: تحقق من الـ DB مباشرة
```sql
SELECT id, sku, ean, upc FROM products WHERE id = 'prod-0923F1ECDX0';
-- لازم يرجع:
-- prod-0923F1ECDX0 | 00-3A5S-1EYF | 1245768907654 | 
```

---

## 📊 ما تم إصلاحه بالفعل:

| المشكلة | الإصلاح | الحالة |
|---------|---------|--------|
| Playwright `NotImplementedError` | استبدال بـ SP-API | ✅ تم |
| `product.asin` attribute error | استخدام `product.attributes.get("asin")` | ✅ تم |
| ENV vars مش بتتحمل | إضافة `load_dotenv()` في `sp_api_router.py` | ✅ تم |
| Session credentials check | ENV fallback | ✅ تم |
| `issueLocale` | تغيير من `en_US` لـ `ar_AE` | ✅ تم |
| Fake barcode `000000000000` | Omission if empty | ✅ تم |
| Duplicate `build_product_payload()` | حذف | ✅ تم |

---

## ⏸️ ما تم إيقافه حالياً:

- ❌ Playwright ListingSubmitter (deprecated)
- ❌ ABIS AJAX API (deprecated)
- ⏳ SP-API Submission (مستني حل مشكلة EAN)

---

## 🚀 اللي هيحصل بعد الحل:

1. EAN هيوصل لـ `_build_listing_payload()` صح
2. `externally_assigned_product_identifier` هيتبعت لـ Amazon
3. `merchant_suggested_asin` هيتبعت (من `product.attributes`)
4. الـ listing هيتقبل بـ `ACCEPTED`
5. Polling هيبدأ يتابع لحد ما ASIN يتعيّن

---

**في انتظار توجيهاتك!** 🙏
