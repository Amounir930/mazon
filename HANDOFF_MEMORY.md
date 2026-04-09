# 📋 Crazy Lister v3.0 — Chat Memory & Handoff Document
## لتسليم المشروع لمهندس جديد

> **التاريخ:** أبريل 2026  
> **المشروع:** Crazy Lister v3.0 — Amazon SP-API Desktop App  
> **النوع:** Standalone Windows Desktop Application (.exe)  
> **حالة الخطة:** ✅ مكتملة وجاهزة للتنفيذ

---

## 🎯 ملخص المشروع (30 ثانية)

**الهدف:** تحويل نظام SaaS مبني بـ FastAPI + React من Docker/SaaS متعدد المستخدمين → **تطبيق سطح مكتب Windows واحد** يعمل بضغطة زر (ملف `.exe`).

**العميل:** تاجر واحد (Single Client) — مش محتاج login/logout أو multi-tenant.

**المخرجات النهائية:** ملف `CrazyLister.exe` (~70 MB) — العميل بيدبل كليك عليه → البرنامج يفتح.

---

## 🏗️ Tech Stack

| الطبقة | التقنية |
|--------|---------|
| **Backend** | FastAPI (Python 3.11) |
| **Frontend** | React 19 + Vite + TypeScript + Tailwind CSS |
| **Database** | SQLite (بدلاً من PostgreSQL) |
| **Task Queue** | Asyncio (بدلاً من Celery + Redis) |
| **Desktop Wrapper** | PyWebView (بدلاً من Electron) |
| **Packaging** | PyInstaller → ملف .exe واحد |
| **Amazon Integration** | python-amazon-sp-api (LWA + SP-API) |

---

## 📂 هيكل المشروع الحالي

```
c:\Users\Dell\Desktop\learn\amazon\
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point
│   │   ├── database.py          ← SQLAlchemy (PostgreSQL حالياً)
│   │   ├── config.py            ← Pydantic settings
│   │   ├── seed.py              ← Demo user (يُحذف)
│   │   ├── api/
│   │   │   ├── auth/            ← JWT auth (يُحذف بالكامل)
│   │   │   ├── router.py        ← Main router
│   │   │   ├── products.py      ← Product CRUD
│   │   │   ├── listings.py      ← Listing management
│   │   │   ├── sellers.py       ← Seller management
│   │   │   └── feeds.py         ← Feed management
│   │   ├── models/
│   │   │   ├── seller.py        ← Seller model (يتعدل)
│   │   │   ├── product.py       ← Product model (يتعدل)
│   │   │   └── listing.py       ← Listing model (يتعدل)
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── auth.py          ← LWA OAuth (يبقى)
│   │   │   ├── amazon_api.py    ← SP-API client (يبقى)
│   │   │   └── product_service.py
│   │   ├── tasks/
│   │   │   └── celery_app.py    ← Celery (يُحذف)
│   │   └── middleware/          ← يُحذف
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/auth/          ← Login/Register (يُحذف)
│   │   ├── contexts/AuthContext.tsx  ← JWT auth (يُستبدل)
│   │   ├── router.tsx           ← routes
│   │   ├── api/endpoints.ts     ← API calls
│   │   ├── api/hooks.ts         ← React Query hooks
│   │   └── lib/axios.ts         ← Axios instance
│   └── package.json
├── docker-compose.yml           ← يُحذف
├── implementation_plan_v3.md    ← الخطة الكاملة (مرجعك)
└── 🆕 ملفات سيتم إنشاؤها:
    ├── backend/app/launcher.py        ← Entry point
    ├── backend/app/desktop.py         ← PyWebView wrapper
    ├── backend/app/api/amazon_connect/← Amazon auth API
    ├── backend/app/tasks/task_manager.py ← Asyncio tasks
    ├── crazy_lister.spec              ← PyInstaller config
    └── build.py                       ← Build script
```

---

## 🗺️ الخطة على مراحل (9 مراحل)

| المرحلة | المدة | الوصف | المرجع في الخطة |
|---------|-------|-------|-----------------|
| **0** | - | **الثغرات الحرجة** — 5 مشاكل تم تحديدها وحلها | Section 0 |
| **1** | 30 دقيقة | تنظيف وحذف ملفات JWT Auth + Docker + Celery | Section 5 |
| **2** | 1-2 ساعة | PostgreSQL → SQLite + AppData paths | Section 6 |
| **3** | 2-3 ساعات | Celery/Redis → Asyncio Task Engine | Section 7 |
| **4** | 2-3 ساعات | إعادة بناء Backend APIs (حذف seller_id) | Section 8 |
| **5** | 3-4 ساعات | إعادة بناء Frontend (Dark Mode + Amazon Connect) | Section 9 |
| **6** | 1-2 ساعة | PyWebView Desktop Wrapper | Section 10 |
| **7** | 1-2 ساعة | PyInstaller Spec + Build Script | Section 11 |
| **8** | 1-2 ساعة | Amazon Integration + Testing | Section 12 |
| **9** | 1-2 ساعة | **Desktop Packaging & Delivery** 🆕 | Section 13 |

**المدة الإجمالية:** 5-7 أيام

---

## 🗑️ الملفات التي سيتم حذفها

### Backend (حذف كامل)
```
backend/app/api/auth/              ← JWT auth (4 ملفات)
backend/app/seed.py                ← Demo user
backend/app/tasks/celery_app.py    ← Celery config
backend/app/middleware/            ← Security middleware (2 ملفات)
backend/tests/                     ← اختبارات JWT
backend/static/                    ← Swagger UI assets
backend/Dockerfile                 ← Docker
```

### Frontend (حذف)
```
frontend/src/pages/auth/           ← Login + Register pages
frontend/src/contexts/AuthContext.tsx ← يُستبدل بـ AmazonConnectContext
```

### Root (حذف)
```
docker-compose.yml                 ← مش محتاجين Docker
frontend/nginx.conf                ← PyWebView بديله
frontend/Dockerfile                ←
backend/Dockerfile                 ←
```

---

## 📝 الملفات التي سيتم تعديلها (26 ملف)

| # | الملف | التغيير الرئيسي | % |
|---|-------|-----------------|---|
| 1 | `backend/app/database.py` | PostgreSQL → SQLite + AppData | 80% |
| 2 | `backend/app/config.py` | حذف JWT/Redis/Celery settings | 70% |
| 3 | `backend/app/main.py` | حذف seed + إضافة Task Manager startup | 40% |
| 4 | `backend/app/models/seller.py` | حذف email/hashed_password + إضافة Amazon fields | 70% |
| 5 | `backend/app/models/product.py` | UUID → String(36), JSON → Text, إزالة seller_id | 30% |
| 6 | `backend/app/models/listing.py` | UUID → String(36), إزالة seller_id | 30% |
| 7 | `backend/app/models/task.py` | حذف (مش محتاجين Celery task model) | 100% |
| 8 | `backend/app/api/router.py` | حذف auth router + إضافة amazon_connect | 50% |
| 9 | `backend/app/api/products.py` | إزالة seller_id Query params | 60% |
| 10 | `backend/app/api/listings.py` | إزالة seller_id + إضافة task API | 70% |
| 11 | `backend/app/api/sellers.py` | تبسيط كامل (Amazon settings only) | 80% |
| 12 | `backend/requirements.txt` | حذف Celery/Redis/JWT + إضافة pywebview | 40% |
| 13 | `frontend/src/router.tsx` | حذف /login, /register + إضافة /connect | 50% |
| 14 | `frontend/src/api/endpoints.ts` | حذف authApi + إضافة amazonApi + taskApi | 70% |
| 15 | `frontend/src/api/hooks.ts` | حذف JWT hooks + إضافة Amazon/Task hooks | 70% |
| 16 | `frontend/src/lib/axios.ts` | تبسيط (إزالة JWT interceptor) | 40% |
| 17 | `frontend/src/types/api.ts` | حذف Login/Register types | 50% |
| 18 | `frontend/src/components/layout/Sidebar.tsx` | إزالة Logout | 10% |
| 19 | `frontend/src/pages/dashboard/DashboardPage.tsx` | إعادة بناء (Dark Mode) | 80% |
| 20 | `frontend/src/pages/products/ProductListPage.tsx` | تحديث API calls | 40% |
| 21 | `frontend/src/pages/products/ProductCreatePage.tsx` | إضافة Bulk Upload | 50% |
| 22 | `frontend/src/pages/listings/ListingQueuePage.tsx` | تحديث API calls | 40% |
| 23 | `frontend/src/pages/settings/SettingsPage.tsx` | إعادة بناء | 80% |
| 24 | `frontend/.env` | VITE_API_URL=http://127.0.0.1:8765/api/v1 | 20% |
| 25 | `frontend/package.json` | إزالة deps غير ضرورية | 10% |
| 26 | `backend/.env.example` | تبسيط | 40% |

---

## 🆕 الملفات التي سيتم إنشاؤها (17 ملف)

| # | الملف | الوصف |
|---|-------|-------|
| 1 | `backend/app/launcher.py` | **أهم ملف** — Entry point (دبل كليك → كل شيء يشتغل) |
| 2 | `backend/app/desktop.py` | PyWebView wrapper (اختياري — launcher.py بديل) |
| 3 | `backend/app/api/amazon_connect/__init__.py` | Package init |
| 4 | `backend/app/api/amazon_connect/endpoints.py` | Amazon connect/verify/status API |
| 5 | `backend/app/api/amazon_connect/schemas.py` | Pydantic models |
| 6 | `backend/app/api/amazon_connect/service.py` | Amazon SP-API verification |
| 7 | `backend/app/api/products_sync.py` | Sync products from Amazon |
| 8 | `backend/app/api/bulk_upload.py` | CSV/Excel bulk upload |
| 9 | `backend/app/api/tasks.py` | Task management API |
| 10 | `backend/app/tasks/task_manager.py` | Asyncio-based task manager |
| 11 | `backend/app/tasks/listing_tasks.py` | Listing tasks (asyncio) |
| 12 | `backend/app/tasks/feed_tasks.py` | Feed tasks (asyncio) |
| 13 | `frontend/src/pages/amazon/AmazonConnectPage.tsx` | Amazon connect UI (Dark Mode) |
| 14 | `frontend/src/contexts/AmazonConnectContext.tsx` | Amazon connect context |
| 15 | `crazy_lister.spec` | PyInstaller spec file |
| 16 | `build.py` | Build script (npm build + pyinstaller) |
| 17 | `assets/icon.ico` | Application icon |

---

## 🚨 الثغرات الحرجة (5 ثغرات — تم حلها)

### 🚩 #1: التشغيل اليدوي (The Launcher Gap)
**المشكلة:** العميل مش هيكتب أوامر في Terminal.  
**الحل:** `launcher.py` — نقطة دخول واحدة تشغّل Backend + Frontend.

### 🚩 #2: صلاحيات ويندوز (Permissions Risk)
**المشكلة:** لو البرنامج في `C:\Program Files` بدون Admin → فشل في حفظ البيانات.  
**الحل:** كل البيانات في `%APPDATA%/CrazyLister/`.

### 🚩 #3: نافذة المتصفح (The Browser Shell)
**المشكلة:** البرنامج هيفتح في Chrome كصفحة ويب — مش برنامج حقيقي.  
**الحل:** **PyWebView** — نافذة Windows حقيقية بدون شريط عنوان.

### 🚩 #4: التجميع النهائي (Packaging)
**المشكلة:** مفيش تعليمات لتحويل الكود لـ .exe واحد.  
**الحل:** **PyInstaller + Spec File + build.py**.

### 🚩 #5: معالجة الإغلاق (Graceful Shutdown)
**المشكلة:** قفل النافذة مش بيوقف الـ Backend → يستهلك موارد.  
**الحل:** `on_closing` event في PyWebView.

---

## 🔑 القرارات التقنية المهمة

### 1. لماذا SQLite بدلاً من PostgreSQL؟
- ✅ ملف واحد (`.db`) — لا يحتاج سيرفر
- ✅ يعمل محلياً بدون أي setup
- ✅ سريع كفاية لعميل واحد
- ✅ مدعوم من SQLAlchemy

### 2. لماذا Asyncio بدلاً من Celery + Redis؟
- ✅ لا يحتاج Redis (بدون Broker)
- ✅ لا يحتاج Celery Worker (بدون process منفصل)
- ✅ يعمل داخل نفس الـ Python process
- ✅ أخف وأسرع

### 3. لماذا PyWebView بدلاً من Electron؟
- ✅ أخف (70 MB vs 200+ MB)
- ✅ يستخدم WebView2 المدمج في Windows
- ✅ لا يحتاج Node.js
- ✅ أسهل في الـ Packaging

### 4. لماذا PyInstaller بدلاً من Nuitka؟
- ✅ أسهل في الاستخدام
- ✅ يدعم bundling frontend files
- ✅ مجتمع أكبر ودعم أفضل

### 5. Database: UUID → String(36)
- SQLite لا يدعم UUID بشكل native → نستخدم `String(36)` بدلاً من `UUID(as_uuid=True)`

### 6. JSON → Text
- SQLite + SQLAlchemy القديم لا يدعم JSON بشكل كامل → نستخدم `Text` ونخزن JSON strings

---

## 🔐 Amazon Credentials (المفاتيح الأربعة)

العميل هيحتاج يدخل:

| المفتاح | المصدر |
|---------|--------|
| **Client ID** | Amazon Developer Console |
| **Client Secret** | Amazon Developer Console |
| **Refresh Token** | Amazon Developer Console → LWA |
| **Seller ID** | Amazon Seller Central → Account Info |

**لا يوجد login/register بالـ email/password.** العميل يتصل بـ Amazon مباشرة.

---

## 📊 الـ Auth Flow الجديد

```
العميل يفتح البرنامج (دبل كليك)
    │
    ├──▶ صفحة Amazon Connect تظهر (لو أول مرة)
    │       │
    │       ├──▶ يدخل 4 مفاتيح
    │       ├──▶ اضغط "حفظ"
    │       └──▶ اضغط "تحقق"
    │
    └──▶ لو متصل → Dashboard يظهر
```

---

## 🧪 Testing Strategy

### Local Development Mode
```powershell
# 1. Build frontend
cd frontend && npm run build

# 2. Run desktop app
cd backend && python -m app.launcher

# 3. Open http://127.0.0.1:8765 in browser (for debugging)
```

### Build Mode
```powershell
# Build the .exe
python build.py

# Test the .exe
.\dist\CrazyLister.exe
```

### Mock Amazon API
في `backend/.env`:
```env
USE_AMAZON_MOCK=true
```
ده بيخلي الـ Amazon API يرجع بيانات وهمية للتجربة.

---

## 📦 النتيجة النهائية

```
releases/CrazyLister-v3.0.0/
├── CrazyLister-v3.0.0.exe    ← ~70 MB — ملف واحد
└── README.txt                 ← تعليمات الاستخدام
```

**العميل:**
1. يحمل الملف
2. دبل كليك
3. البرنامج يفتح خلال 3 ثواني
4. يدخل بيانات Amazon
5. يبدأ يشتغل

---

## ⚡ Quick Start للمهندس الجديد

### Step 1: اقرأ الخطة الكاملة
```
implementation_plan_v3.md
```
ابدأ من **Section 0 (الثغرات الحرجة)** → ثم **Section 5 (المرحلة 1)**.

### Step 2: نفّذ المراحل بالترتيب
1. المرحلة 1: التنظيف والحذف (30 دقيقة)
2. المرحلة 2: SQLite + Database (1-2 ساعة)
3. المرحلة 3: Asyncio Engine (2-3 ساعات)
4. المرحلة 4: Backend APIs (2-3 ساعات)
5. المرحلة 5: Frontend (3-4 ساعات)
6. المرحلة 6: PyWebView (1-2 ساعة)
7. المرحلة 7: PyInstaller (1-2 ساعة)
8. المرحلة 8: Amazon Integration (1-2 ساعة)
9. المرحلة 9: Packaging & Delivery (1-2 ساعة)

### Step 3: اختبر في كل مرحلة
- بعد كل مرحلة، شغّل `python -m app.launcher` وتأكد إن كل شيء يشتغل
- استخدم `USE_AMAZON_MOCK=true` للتجربة بدون Amazon حقيقي

### Step 4: ابنِ الـ .exe النهائي
```powershell
python build.py
```

---

## 📞 مراجع مهمة

| المرجع | الوصف |
|--------|-------|
| `implementation_plan_v3.md` | **الخطة الكاملة** — كل الكود والخطوات هنا |
| [PyWebView Docs](https://pywebview.flowrl.com/) | توثيق PyWebView |
| [PyInstaller Docs](https://pyinstaller.org/) | توثيق PyInstaller |
| [python-amazon-sp-api](https://python-amazon-sp-api.readthedocs.io/) | Amazon SP-API Python library |
| [FastAPI Docs](https://fastapi.tiangolo.com/) | FastAPI documentation |

---

## 🚀 جاهز تبدأ؟

1. افتح `implementation_plan_v3.md`
2. ابدأ من **Section 5: المرحلة 1**
3. نفّذ خطوة بخطوة
4. لو وقفت في حاجة — راجع **Section 0 (الثغرات)** أو **Section 12.8 (Troubleshooting)**

**بالتوفيق! 🎯**
