# 🗺️ WORK MAP v2.0 — CrazyLister SP-API Integration

## 🎉 الإنجاز الحالي (ما تم إثباته بنجاح)

| البند | الحالة | التفاصيل |
|-------|--------|----------|
| **SP-API Authentication** | ✅ نجح 100% | LWA Token + AWS SigV4 + IAM Role |
| **PUT Listing Item** | ✅ ACCEPTED | 0 errors, 0 warnings — Amazon قبلت المنتج |
| **GET Listing Verification** | ✅ مؤكد | المنتج موجود على Amazon.eg |
| **Seller ID** | ✅ `A1DSHARRBRWYZW` | Store: Aigle.Shop |
| **Marketplace** | ✅ `ARBP9OOSHTCHU` | Amazon.eg |
| **Template Schema** | ✅ مستخرج | كل الـ 29 حقل REQUIRED معروفين |
| **Correct Formats** | ✅ مكتشفة | الأبعاد، الوزن، الباركود، البطاريات — كلها صح |

---

## 📊 الوضع الحالي (As-Is)

### ✅ موجود وشغال:
| المكون | الحالة | الملاحظات |
|--------|--------|-----------|
| Frontend Routes | ✅ 7 صفحات | Dashboard, Products, Create, Search, Listings, Reports, Settings |
| ProductCreatePage | ⚠️ موجود لكن ناقص | 3 steps فقط، مش شامل كل الـ 29 حقل |
| Backend APIs | ✅ 14 endpoint | Products, Listings, Auth, Sync, Tasks, etc. |
| SP-API Client | ✅ جاهز | `sp_api_client.py` — نجح في الإرسال |
| Database Models | ✅ 7 models | Product, Listing, Seller, Session, etc. |

### ❌ محتاج تطوير:
| المكون | المشكلة | الحل المطلوب |
|--------|---------|--------------|
| ProductCreatePage | مش شامل كل الحقول المطلوبة | إعادة تنظيم لـ 5 tabs شاملة |
| Backend Validation | صارم جداً | تخفيف + auto-fill defaults |
| Listings Page | بسيط جداً | إضافة تفاصيل + ASIN + روابط |
| Settings | مش فيه إدارة حسابات | إضافة CRUD حسابات متعددة |
| Automation | مفيش | نظام إرسال متعدد + Excel import |
| SP-API Integration | script فقط | ربط بـ Backend API |

---

## 🎯 Work Map — 6 مراحل متكاملة

### المرحلة 1: 🔗 دمج SP-API في Backend (أسبوع 1) ← **الأولوية القصوى**
**الهدف**: تحويل الـ test script إلى API endpoint حقيقي

| # | المهمة | الملفات | الوصف | المدة |
|---|--------|---------|-------|-------|
| 1.1 | إنشاء `sp_api_router.py` | `backend/app/api/sp_api_router.py` | endpoints جديدة: `POST /sp-api/listings`, `GET /sp-api/listings/{sku}` | 2 ساعة |
| 1.2 | تحديث `sp_api_client.py` | `backend/app/services/sp_api_client.py` | إضافة `create_listing_from_product()` — ياخد Product model ويبعت لـ Amazon | 3 ساعة |
| 1.3 | ربط Product → SP-API | `backend/app/api/products.py` | إضافة endpoint `POST /products/{id}/submit-to-amazon` | 2 ساعة |
| 1.4 | تحديث Listing model | `backend/app/models/listing.py` | إضافة حقول: `sp_api_submission_id`, `sp_api_status`, `amazon_asin` | 1 ساعة |
| 1.5 | Error handling | `backend/app/api/sp_api_router.py` | ترجمة أخطاء Amazon لرسائل واضحة بالعربي | 2 ساعة |
| 1.6 | Webhook/Callback | `backend/app/api/sp_api_router.py` | تحديث حالة الـ listing تلقائياً بعد القبول | 2 ساعة |

**المخرجات:**
```
✅ POST /api/v1/products/{id}/submit-to-amazon  ← يرسل منتج لـ Amazon عبر SP-API
✅ GET /api/v1/sp-api/listings/{sku}            ← يجيب حالة listing من Amazon
✅ GET /api/v1/sp-api/schema/{product_type}     ← يجيب schema المطلوب من Amazon
```

---

### المرحلة 2: 📋 إعادة بناء Product Create Page (أسبوع 1-2)
**الهدف**: صفحة إنشاء منتجات شاملة بكل الـ 29 حقل المطلوبة من Amazon

| # | المهمة | الملفات | الوصف | المدة |
|---|--------|---------|-------|-------|
| 2.1 | إعادة تنظيم الصفحة لـ 5 tabs | `frontend/src/pages/products/ProductCreatePage.tsx` | الهوية ← الوصف ← التسعير ← الشحن ← الوسائط | 6 ساعات |
| 2.2 | Tab 1: الهوية الأساسية | نفس الملف | اسم (عربي+إنجليزي)، نوع، باركود (EAN/UPC/ASIN/معفي)، براند، موديل، مصنع، بلد منشأ | 3 ساعات |
| 2.3 | Tab 2: الوصف والتفاصيل | نفس الملف | وصف (عربي+إنجليزي)، 5 نقاط بيعية، فئة (Browse Node dropdown من temp.txt)، كلمات مفتاحية، مواد، مكونات، عدد وحدات | 3 ساعات |
| 2.4 | Tab 3: التسعير والكمية | نفس الملف | سعر، سعر مقارنة، تكلفة، كمية، سعر تخفيض + تواريخ | 2 ساعة |
| 2.5 | Tab 4: الشحن والأبعاد | نفس الملف | قناة شحن (MFN/AFN)، وقت تجهيز، حالة منتج، أبعاد (طول×عرض×ارتفاع)، وزن + وحدة، عدد قطع بالباكج | 3 ساعات |
| 2.6 | Tab 5: الصور والإرسال | نفس الملف | صورة رئيسية (إجبارية)، 8 صور فرعية (اختيارية)، عدد نسخ (1-50)، أزرار: حفظ ← حفظ وإرسال لأمزون ← معاينة | 3 ساعات |
| 2.7 | Auto-fill defaults | نفس الملف | قيم افتراضية ذكية (brand="Generic", condition="New", country="CN", etc.) | 2 ساعة |
| 2.8 | Validation مخفف | نفس الملف | السماح بحقول فاضية، صور اختيارية مؤقتاً، رسائل واضحة بالعربي | 2 ساعة |

**5 Tabs المقترحة:**
```
┌─────────────────────────────────────────────────────────────┐
│  Tab 1: الهوية الأساسية                                      │
│  ├── اسم المنتج (عربي + إنجليزي) *                          │
│  ├── نوع المنتج (dropdown من temp.txt) *                    │
│  ├── الباركود: EAN / UPC / ASIN / معفي *                    │
│  ├── البراند                                                │
│  ├── الموديل                                                │
│  ├── المصنع                                                 │
│  └── بلد المنشأ (dropdown)                                  │
├─────────────────────────────────────────────────────────────┤
│  Tab 2: الوصف والتفاصيل                                      │
│  ├── الوصف عربي *                                           │
│  ├── الوصف English *                                        │
│  ├── النقاط البيعية (5 حقول) *                              │
│  ├── الفئة (Browse Node — dropdown من temp.txt) *           │
│  ├── الكلمات المفتاحية (15 كلمة)                            │
│  ├── المواد                                                 │
│  ├── المكونات المرفقة *                                     │
│  └── عدد الوحدات + نوعها *                                  │
├─────────────────────────────────────────────────────────────┤
│  Tab 3: التسعير والكمية                                     │
│  ├── السعر *                                                │
│  ├── سعر المقارنة (قبل الخصم)                               │
│  ├── التكلفة                                                │
│  ├── الكمية *                                               │
│  └── سعر التخفيض + التواريخ                                │
├─────────────────────────────────────────────────────────────┤
│  Tab 4: الشحن والأبعاد                                       │
│  ├── قناة الشحن (MFN / AFN) *                               │
│  ├── وقت التجهيز                                            │
│  ├── حالة المنتج (dropdown) *                               │
│  ├── الأبعاد: طول × عرض × ارتفاع (سم) *                     │
│  ├── الوزن + الوحدة (كجم) *                                 │
│  ├── وزن الباكج + الوحدة *                                  │
│  └── عدد القطع في الباكج                                    │
├─────────────────────────────────────────────────────────────┤
│  Tab 5: الصور والإرسال                                       │
│  ├── الصورة الرئيسية (إجبارية) *                            │
│  ├── 8 صور فرعية (اختيارية)                                 │
│  ├── عدد النسخ (1-50)                                       │
│  ├── [💾 حفظ في المخزون]                                    │
│  ├── [🚀 حفظ وإرسال لـ Amazon]                              │
│  └── [👁️ معاينة Amazon Feed]                                │
└─────────────────────────────────────────────────────────────┘
* = حقل مطلوب من Amazon SP-API
```

---

### المرحلة 3: 📊 تحديث Listings Page (أسبوع 2)
**الهدف**: صفحة listings شاملة تعرض كل التفاصيل

| # | المهمة | الملفات | الوصف | المدة |
|---|--------|---------|-------|-------|
| 3.1 | إعادة تصميم الجدول | `frontend/src/pages/listings/ListingQueuePage.tsx` | إضافة: اسم المنتج، SKU، ASIN، رابط Amazon، سعر، كمية | 3 ساعات |
| 3.2 | إضافة Filters | نفس الملف | فلترة بـ: الحالة (success/failed/processing)، التاريخ، Product Type | 2 ساعة |
| 3.3 | إضافة Retry Button | نفس الملف | إعادة محاولة المنتجات الفاشلة | 1 ساعة |
| 3.4 | Error Details Modal | نفس الملف | عرض رسالة الخطأ كاملة + الحلول المقترحة | 2 ساعة |
| 3.5 | Export to Excel | نفس الملف | تصدير النتائج لملف Excel | 2 ساعة |
| 3.6 | Real-time Updates | نفس الملف | WebSocket/SSE لتحديث الحالة تلقائياً | 3 ساعات |

---

### المرحلة 4: ⚙️ Settings — حسابات متعددة (أسبوع 2-3)
**الهدف**: إضافة وإدارة حسابات Amazon متعددة

| # | المهمة | الملفات | الوصف | المدة |
|---|--------|---------|-------|-------|
| 4.1 | إعادة تصميم Settings | `frontend/src/pages/settings/UnifiedAuthPage.tsx` | جدول حسابات + إضافة حساب جديد + التحقق | 4 ساعات |
| 4.2 | Backend CRUD للحسابات | `backend/app/api/sellers.py` | إضافة، حذف، تعطيل، تفعيل حسابات | 3 ساعات |
| 4.3 | تخزين SP-API Credentials | `backend/app/models/seller.py` | حفظ: Seller ID, LWA Client, AWS Keys, Role ARN | 2 ساعة |
| 4.4 | Verify Connection | `backend/app/api/auth_routes.py` | اختبار الاتصال بـ SP-API + عرض النتائج | 3 ساعات |

---

### المرحلة 5: 🚀 نظام الأتمتة (أسبوع 3)
**الهدف**: إرسال سريع ومتعدد المنتجات

| # | المهمة | الملفات | الوصف | المدة |
|---|--------|---------|-------|-------|
| 5.1 | صفحة Automation | `frontend/src/pages/automation/AutomationPage.tsx` (جديد) | اختيار منتجات متعددة + إرسال دفعة | 6 ساعات |
| 5.2 | Backend Batch API | `backend/app/api/sp_api_router.py` | `POST /sp-api/listings/batch` — إرسال 10-50 منتج | 4 ساعات |
| 5.3 | Excel Import | `frontend/src/pages/automation/ExcelImportPage.tsx` (جديد) | رفع Excel → تحويل لمنتجات → إرسال | 6 ساعات |
| 5.4 | Progress Tracker | `frontend/src/components/automation/ProgressTracker.tsx` (جديد) | شريط تقدم + logs حية + نتائج | 4 ساعات |
| 5.5 | Queue Management | `backend/app/tasks/listing_tasks.py` | تحسين نظام الطابور + retry ذكي | 3 ساعات |

---

### المرحلة 6: 🔗 ربط الكل (End-to-End Flow) (أسبوع 3)
**الهدف**: Workflow متكامل

| # | المهمة | الملفات | الوصف | المدة |
|---|--------|---------|-------|-------|
| 6.1 | زر "إرسال لأمزون" في Products List | `frontend/src/pages/products/ProductListPage.tsx` | زر مباشر لكل منتج + bulk selection | 2 ساعة |
| 6.2 | Toast Notifications | Frontend | إشعارات عند نجاح/فشل الإرسال | 1 ساعة |
| 6.3 | Dashboard Stats | `frontend/src/pages/dashboard/DashboardPage.tsx` | إحصائيات: إجمالي المنتجات، المرفوعة، الناجحة | 2 ساعة |
| 6.4 | Documentation | `docs/` | دليل استخدام + troubleshooting | 3 ساعات |

---

## 🔄 الـ Workflow النهائي

```
┌─────────────────────────────────────────────────────────────┐
│                    الكامل Flow المتكامل                      │
│                                                              │
│  1. /settings                                                │
│     └── إضافة حساب Amazon (Seller ID + Credentials)         │
│         └── Verify → ✅ متصل                                │
│                                                              │
│  2. /products/create                                        │
│     └── إنشاء منتج (5 tabs, 29 حقل مطلوب)                   │
│         └── [💾 حفظ في المخزون] أو [🚀 حفظ وإرسال لأمزون]   │
│                                                              │
│  3. /products                                               │
│     └── مراجعة المنتجات في المخزون                          │
│         └── اختيار منتج → [🚀 إرسال لأمزون]                 │
│                                                              │
│  4. (Background) SP-API PUT /listings/2021-08-01/items/...  │
│     └── Amazon ترد بـ: ACCEPTED / INVALID                   │
│                                                              │
│  5. /listings                                               │
│     └── متابعة حالة الإرسال                                 │
│         ├── ✅ نجح → يظهر ASIN + رابط Amazon               │
│         └── ❌ فشل → يظهر الخطأ + زر Retry                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 الجدول الزمني

| الأسبوع | المراحل | المخرجات |
|---------|---------|----------|
| **أسبوع 1** | 1 + 2 | SP-API في Backend + Product Create Page شاملة |
| **أسبوع 2** | 3 + 4 | Listings Page محدّثة + Settings حسابات متعددة |
| **أسبوع 3** | 5 + 6 | نظام أتمتة + Workflow متكامل |

---

## 📋 الملفات المتأثرة

| الملف | الإجراء | المرحلة |
|-------|---------|---------|
| `backend/app/services/sp_api_client.py` | ✅ جاهز — تحديث بسيط | 1 |
| `backend/app/api/sp_api_router.py` | 🔴 إنشاء جديد | 1 |
| `backend/app/api/products.py` | ⚠️ تحديث — إضافة submit endpoint | 1 |
| `backend/app/models/listing.py` | ⚠️ تحديث — إضافة حقول SP-API | 1 |
| `frontend/src/pages/products/ProductCreatePage.tsx` | 🔴 إعادة بناء شاملة | 2 |
| `frontend/src/pages/listings/ListingQueuePage.tsx` | ⚠️ تحديث شامل | 3 |
| `frontend/src/pages/settings/UnifiedAuthPage.tsx` | ⚠️ تحديث — حسابات متعددة | 4 |
| `frontend/src/pages/automation/AutomationPage.tsx` | 🔴 إنشاء جديد | 5 |
| `frontend/src/pages/products/ProductListPage.tsx` | ⚠️ تحديث — إضافة زر إرسال | 6 |

---

## ⚠️ المخاطر والتخفيف

| الخطر | الاحتمال | التأثير | التخفيف |
|-------|----------|---------|---------|
| Amazon ترفض Product Type | 🟢 منخفض | المنتج ما يترفعش | نجرب Product Types مختلفة |
| Session تنتهي | 🟡 متوسط | الإرسال يتوقف | Auto-refresh token |
| SP-API Rate Limits | 🟡 متوسط | بطء في الإرسال | Queue + throttling |
| Schema يتغير | 🟡 متوسط | الحقول تبطل تشتغل | نجيب schema جديد ديناميكياً |

---

## ✅ معايير القبول (Acceptance Criteria)

### المرحلة 1:
- [ ] `POST /api/v1/products/{id}/submit-to-amazon` يعمل
- [ ] المنتج يظهر في Amazon.eg
- [ ] أخطاء Amazon مترجمة للعربي

### المرحلة 2:
- [ ] 5 tabs شاملة لكل الـ 29 حقل
- [ ] Validation مخفف مع auto-fill
- [ ] منتج ينحفظ ويترفع بنجاح

### المرحلة 3:
- [ ] Listings table فيه: اسم، SKU، ASIN، رابط Amazon
- [ ] Filters بالشكل المطلوب
- [ ] Retry button شغال

### المرحلة 4:
- [ ] إضافة حساب جديد من Settings
- [ ] Verify connection شغال
- [ ] حسابات متعددة مدعومة

### المرحلة 5:
- [ ] إرسال 10 منتجات دفعة واحدة
- [ ] Excel import شغال
- [ ] Progress tracker يعرض النتائج

### المرحلة 6:
- [ ] زر "إرسال لأمزون" في Products List
- [ ] Toast notifications شغالة
- [ ] Dashboard stats محدّثة

---

**الحالة: بانتظار موافقة القائد التقني للبدء في التنفيذ** 🚀
