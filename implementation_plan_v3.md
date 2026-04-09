# 🚀 Crazy Lister v3.0 — Standalone Windows Desktop App
## خطة التنفيذ الكاملة (Implementation Plan)

> **التاريخ:** أبريل 2026  
> **الهدف:** تحويل النظام من SaaS متعدد المستخدمين → تطبيق سطح مكتب Windows مستقل (.exe)  
> **النوع:** Standalone Desktop App — ملف واحد يعمل بدون Docker أو سطر أوامر  
> **مدة التنفيذ المتوقعة:** 5-7 أيام

---

## 📋 الفهرس

0. [**🚨 الثغرات الحرجة وإصلاحاتها** — 4 مشاكل تمنع التطبيق من العمل كـ Desktop](#0-الثغرات-الحرجة-وإصلاحاتها)
1. [**بنية التطبيق كـ Desktop App** — كيف يعمل الـ .exe من دبل كليك؟](#1-بنية-التطبيق-ك-desktop-app-كيف-يعمل-ال-exe-من-دبل-كليك)
2. [الرؤية والتغييرات الجذرية](#2-الرؤية-والتغييرات-الجذرية)
3. [التغييرات التقنية الأساسية](#3-التغييرات-التقنية-الأساسية)
4. [الملفات المتأثرة](#4-الملفات-المتأثرة)
5. [المرحلة 1: التنظيف والحذف](#5-المرحلة-1-التنظيف-والحذف)
6. [المرحلة 2: SQLite + Database Migration](#6-المرحلة-2-sqlite--database-migration)
7. [المرحلة 3: إزالة Celery/Redis + Asyncio Engine](#7-المرحلة-3-إزالة-celeryredis--asyncio-engine)
8. [المرحلة 4: إعادة بناء Backend APIs](#8-المرحلة-4-إعادة-بناء-backend-apis)
9. [المرحلة 5: إعادة بناء Frontend (Dark Mode)](#9-المرحلة-5-إعادة-بناء-frontend-dark-mode)
10. [المرحلة 6: Desktop Wrapper (PyWebView)](#10-المرحلة-6-desktop-wrapper-pywebview)
11. [المرحلة 7: Build & Packaging (.exe)](#11-المرحلة-7-build--packaging-exe)
12. [المرحلة 8: Amazon Integration + Local Testing](#12-المرحلة-8-amazon-integration--local-testing)
13. [المرحلة 9: Desktop Packaging & Delivery 🆕](#13-المرحلة-9-desktop-packaging--delivery)
14. [خطة التوزيع للعميل](#14-خطة-التوزيع-للعميل)
15. [خطة التحقق (Verification)](#15-خطة-التحقق-verification)

---

## 0. 🚨 الثغرات الحرجة وإصلاحاتها

> ⚠️ **هذا أهم قسم في الخطة.** يحدد 4 ثغرات تمنع التطبيق من العمل كـ Desktop حقيقي — ويقدّم الحل الكامل لكل واحدة.

### 🚩 الثغرة #1: "التشغيل اليدوي" (The Launcher Gap)

**المشكلة:**
> الخطة تفترض إن العميل هيشغّل الـ Backend والـ Frontend بشكل منفصل. العميل **لن** يفتح Terminal ويكتب أوامر. هو يتوقع دبل كليك على أيقونة → البرنامج يفتح.

**الحل: ملف `launcher.py` — نقطة الدخول الوحيدة**

```
┌─────────────────────────────────────────────────────────────┐
│  crazy_lister.exe (الملف التنفيذي الوحيد)                    │
│                                                             │
│  entry point: launcher.py                                   │
│                                                             │
│  def main():                                                │
│      │                                                      │
│      ├──▶ 1. start_backend()     ← Uvicorn في thread خلفي   │
│      ├──▶ 2. wait_for_server()   ← ينتظر 2 ثانية            │
│      └──▶ 3. open_window()       ← PyWebView window         │
│                                                             │
│  ✅ ضغطة زر واحدة — كل شيء يشتغل تلقائياً                   │
└─────────────────────────────────────────────────────────────┘
```

**الكود الكامل:** انظر **المرحلة 6** (القسم 6.1).

---

### 🚩 الثغرة #2: "صلاحيات ويندوز" (Permissions Risk)

**المشكلة:**
> لو العميل حط البرنامج في `C:\Program Files` وفتحه بدون Admin، البرنامج **هيفشل** في حفظ أي بيانات لأن المجلد محمي.

**الحل: كل البيانات في `%APPDATA%`**

```
❌ خطأ (المسار الحالي):
   ./crazy_lister.db          ← يفشل لو في Program Files

✅ صحيح (مسار آمن):
   %APPDATA%/CrazyLister/
   ├── crazy_lister.db        ← قاعدة البيانات
   ├── crazy_lister.log       ← اللوجات
   ├── uploads/               ← ملفات الرفع الجماعي
   └── exports/               ← التقارير المصدرة
```

**لماذا `%APPDATA%`؟**
- ✅ العميل ما يحتاجش Admin permissions
- ✅ البيانات محفوظة حتى لو حذف البرنامج
- ✅ المسار ثابت: `C:\Users\<username>\AppData\Roaming\CrazyLister\`
- ✅ يعمل على كل إصدارات Windows (7, 10, 11)

**الكود:**
```python
# في كل الملفات — مسار قاعدة البيانات
import os
from pathlib import Path

APP_DATA_DIR = Path(os.getenv("APPDATA")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"
```

---

### 🚩 الثغرة #3: "نافذة المتصفح" (The Browser Shell)

**المشكلة:**
> البرنامج هيفتح في Chrome/Edge كصفحة ويب عادية — مع شريط عنوان وأزرار المتصفح. ده **مش** بيعطي إحساس برنامج حقيقي.

**الحل: PyWebView — نافذة Windows حقيقية**

```
❌ خطأ (متصفح عادي):
┌─────────────────────────────────────────────────┐
│ ← → ⟳   https://localhost:8765       [─][□][×]│ ← شريط المتصفح
├─────────────────────────────────────────────────┤
│  محتوى البرنامج...                               │
└─────────────────────────────────────────────────┘

✅ صحيح (PyWebView):
┌─────────────────────────────────────────────────┐
│  Crazy Lister v3.0                       [─][□][×]│ ← عنوان مخصص
├─────────────────────────────────────────────────┤
│  محتوى البرنامج...                               │
│  (بدون شريط عنوان — بدون أزرار متصفح)             │
└─────────────────────────────────────────────────┘
```

**المميزات:**
- ✅ نافذة Windows حقيقية (مش متصفح)
- ✅ عنوان مخصص في شريط النافذة
- ✅ بدون شريط عنوان المتصفح أو أزرار الـ URL
- ✅ أيقونة مخصصة للبرنامج في Taskbar
- ✅ حجم قابل للتعديل مع حد أدنى

**الكود:** انظر **المرحلة 6** (القسم 6.2).

---

### 🚩 الثغرة #4: "التجميع النهائي" (Packaging)

**المشكلة:**
> الخطة تنتهي عند كتابة الكود. مفيش تعليمات لتحويل آلاف الملفات (Python + React + dependencies) إلى **ملف .exe واحد**.

**الحل: PyInstaller + Spec File مخصص**

```
قبل البناء (مئات الملفات):
├── backend/app/              ← 50+ ملف Python
├── frontend/dist/            ← 20+ ملف JS/CSS
├── requirements.txt
└── node_modules/             ← 10000+ ملف!

         ↓ python build.py

بعد البناء (ملف واحد):
├── dist/CrazyLister.exe      ← ~70 MB — ملف واحد
```

**الـ Spec File بيحدد:**
1. **Entry point:** `launcher.py`
2. **Data files:** `frontend/dist/` → يتضمّن جوه الـ .exe
3. **Hidden imports:** كل الـ dependencies اللي PyInstaller مش بيلاقيها
4. **Console:** `False` → ما يظهرش شاشة CMD السوداء
5. **Icon:** أيقونة `.ico` احترافية

**الكود:** انظر **المرحلة 7** و**المرحلة 9**.

---

### 🚩 الثغرة #5: "معالجة الإغلاق" (Graceful Shutdown)

**المشكلة:**
> لو العميل قفل النافذة (زر ×)، الـ Backend لسه شغال في الخلفية → **بيستهلك موارد الجهاز**.

**الحل: `on_closing` event في PyWebView**

```python
def on_closing():
    """يتم استدعاؤها لما العميل يقفل النافذة"""
    stop_backend()      # يوقف Uvicorn
    task_manager.stop()  # يوقف Task Manager
    db.close()           # يقفل قاعدة البيانات
    logger.info("App closed gracefully")
    return True  # يسمح بالإغلاق

window = webview.create_window(..., on_closing=on_closing)
```

---

## 1. بنية التطبيق كـ Desktop App (كيف يعمل الـ .exe من دبل كليك؟)

> ⚠️ **هذا القسم هو الفرق الجوهري بين نسخة Web (SaaS) ونسخة Desktop.**  
> يشرح بالتفصيل كيف يتحول الكود من "موقع ويب" إلى "برنامج سطح مكتب" يعمل بضغطة زر.

### 0.1 الفرق الجوهري: Web App vs Desktop App

```
┌─────────────────────────────────────────────────────────────┐
│                    قبل: Web App (SaaS)                       │
├─────────────────────────────────────────────────────────────┤
│  العميل يفتح المتصفح → يكتب URL → Nginx يخدم الـ Frontend   │
│  Frontend يتصل بالـ Backend (Docker) → Backend يتصل بالـ DB │
│  Celery + Redis يشتغلوا كـ containers منفصلة                │
│                                                             │
│  ⚠️ يحتاج: Docker, docker-compose, سطر أوامر, سيرفر GCP     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   بعد: Desktop App (.exe)                    │
├─────────────────────────────────────────────────────────────┤
│  العميل يدبل كليك على CrazyLister.exe                        │
│      │                                                       │
│      ├──▶ 1. PyWebView يفتح نافذة Windows مستقلة            │
│      ├──▶ 2. FastAPI Backend يشتغل في thread خلفي (port 8765)│
│      ├──▶ 3. SQLite Database يتصل تلقائياً (%APPDATA%)       │
│      ├──▶ 4. Asyncio Task Manager يبدأ في الخلفية           │
│      └──▶ 5. الـ Frontend (React built) يتحمّل في النافذة    │
│                                                             │
│  ✅ يحتاج: دبل كليك فقط — لا Docker، لا سطر أوامر            │
└─────────────────────────────────────────────────────────────┘
```

### 0.2 كيف يعمل الـ Desktop Wrapper (PyWebView)؟

**PyWebView** هو مكتبة Python تفتح نافذة Windows حقيقية (مثل أي برنامج عادي) وتعرض فيها محتوى HTML/JS — تماماً مثل المتصفح لكن بدون شريط العنوان وأزرار التحكم.

```
┌──────────────────────────────────────────────────────────────┐
│  Crazy Lister v3.0                              [─] [□] [×]  │  ← نافذة Windows حقيقية
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🔗 ربط حساب Amazon                                  │  │  ← محتوى React
│  │  أدخل بيانات حسابك في Amazon Seller Central           │  │    (يعرض كأنه موقع)
│  │                                                        │  │
│  │  Client ID:        [________________________]          │  │
│  │  Client Secret:    [________________________]          │  │
│  │  Refresh Token:    [________________________]          │  │
│  │  Seller ID:        [________________________]          │  │
│  │                                                        │  │
│  │        [ حفظ البيانات ]                                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
         ▲                                                      
         │ PyWebView يعرض ملف index.html من الـ dist/ folder   
         │ (نفس ملفات React المبنية بـ Vite)                   
```

**كيف يتم الربط بين الـ Frontend والـ Backend؟**

```
العميل يدبل كليك على .exe
    │
    ├──▶ main thread: PyWebView يفتح النافذة
    │       │
    │       └──▶ يعرض file:///C:/.../frontend/dist/index.html
    │
    └──▶ background thread: FastAPI يشتغل على 127.0.0.1:8765
            │
            └──▶ الـ Frontend (React) يرسل requests لـ http://127.0.0.1:8765/api/v1/
```

**الـ Frontend يعرف يتصل بالـ Backend لأن:**
```ts
// frontend/.env
VITE_API_URL=http://127.0.0.1:8765/api/v1

// frontend/src/lib/axios.ts
const api = axios.create({
  baseURL: 'http://127.0.0.1:8765/api/v1',  // ← يتصل بالـ localhost
})
```

### 0.3 كيف يتم تحويل كل شيء لملف .exe واحد؟

**PyInstaller** يأخذ كل الملفات (Python + Frontend built + dependencies) ويجمعهم في ملف `.exe` واحد:

```
قبل البناء (مجلدات متعددة):
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI app
│   │   ├── desktop.py       ← PyWebView launcher
│   │   ├── models/
│   │   ├── api/
│   │   └── tasks/
│   └── requirements.txt
├── frontend/
│   └── dist/                ← React built files
│       ├── index.html
│       ├── assets/
│       │   ├── index-xxx.js
│       │   └── index-xxx.css
└── crazy_lister.spec        ← PyInstaller config

                    ↓ PyInstaller build

بعد البناء (ملف واحد):
├── dist/
│   └── CrazyLister.exe      ← ملف واحد (~70 MB)
│                              يحتوي على:
│                              • Python runtime
│                              • FastAPI + كل الـ dependencies
│                              • Frontend built files (مضغوطة)
│                              • PyWebView engine
```

**عند تشغيل الـ .exe:**
1. PyInstaller يفك الملفات المضغوطة في مجلد مؤقت (`_MEIPASS`)
2. يشغّل `desktop.py` كـ entry point
3. `desktop.py` يشغّل FastAPI في thread خلفي
4. `desktop.py` يفتح PyWebView window ويعرض الـ Frontend

### 0.4 التدفق الكامل: من دبل كليك إلى شاشة Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    Timeline: Startup Flow                    │
└─────────────────────────────────────────────────────────────┘

0.0s  ─▶ العميل يدبل كليك على CrazyLister.exe
         │
         └──▶ Windows يشغّل الـ .exe
              │
              └──▶ PyInstaller يفك الملفات في %TEMP%/_MEIPASS

0.5s  ─▶ desktop.py يبدأ التنفيذ
         │
         ├──▶ 1. يتحقق إن Frontend files موجودة
         ├──▶ 2. ينشئ مجلد %APPDATA%/CrazyLister/ (لو مش موجود)
         └──▶ 3. يهيئ الـ Logging

1.0s  ─▶ backend thread يبدأ
         │
         ├──▶ FastAPI app يشتغل على 127.0.0.1:8765
         ├──▶ SQLite database يتصل (%APPDATA%/CrazyLister/crazy_lister.db)
         ├──▶ الجداول تتنشأ تلقائياً (لو أول مرة)
         └──▶ Asyncio Task Manager يبدأ في الخلفية

2.0s  ─▶ PyWebView window يفتح
         │
         ├──▶ عنوان النافذة: "Crazy Lister v3.0"
         ├──▶ الحجم: 1280x850
         ├──▶ الخلفية: #0a0a0f (Dark Mode)
         └──▶ المحتوى: file:///.../frontend/dist/index.html

2.5s  ─▶ React App يتحمّل
         │
         ├──▶ axios يتصل بـ http://127.0.0.1:8765/api/v1/amazon/status
         ├──┬──▶ لو isConnected = false
         │  │   └──▶ يعرض صفحة Amazon Connect
         │  │
         │  └──▶ لو isConnected = true
         │      └──▶ يعرض Dashboard

3.0s  ─▶ ✅ التطبيق جاهز للاستخدام!
```

### 0.5 هيكل الـ .exe النهائي

```
CrazyLister.exe (ملف واحد — ~70 MB)
│
├── Python 3.11 Runtime          (~30 MB)
├── FastAPI + Uvicorn            (~10 MB)
├── SQLAlchemy + SQLite drivers  (~5 MB)
├── python-amazon-sp-api         (~8 MB)
├── PyWebView                    (~5 MB)
├── Pandas + OpenPyXL (Excel)    (~8 MB)
├── Frontend built files         (~2 MB)
│   ├── index.html
│   ├── assets/index-xxx.js
│   └── assets/index-xxx.css
└── Loguru + Utilities           (~2 MB)
```

### 0.6 لماذا PyWebView وليس Electron؟

| المعيار | PyWebView | Electron |
|---------|-----------|----------|
| **الحجم** | ~5 MB (يستخدم WebView2 المدمج) | ~150 MB (يحمل Chromium كامل) |
| **الـ .exe النهائي** | ~70 MB | ~200 MB+ |
| **Python integration** | مباشر (نفس الـ process) | يحتاج IPC / localhost server |
| **Node.js مطلوب؟** | ❌ لا | ✅ نعم (للتطوير) |
| **الذاكرة** | ~100 MB | ~200-300 MB |
| **النضج** | جيد جداً | ممتاز |

**الخلاصة:** PyWebView أخف وأبسط وأسهل في الـ Packaging — مثالي لتطبيق Desktop مبني بـ Python + React.

---

## 1. الرؤية والتغييرات الجذرية

### 🔴 ما سيتم حذفه بالكامل

| المكون | السبب |
|--------|-------|
| JWT Authentication | عميل واحد = لا حاجة لـ login/logout |
| Email/Password | لا يوجد مستخدمين متعددين |
| PostgreSQL | نستبدله بـ SQLite (ملف واحد محلي) |
| Redis | نستبدله بـ Asyncio (بدون Broker) |
| Celery Worker | نستبدله بـ Python Background Threads |
| Celery Flower | مش محتاجينه (بدون Celery) |
| Docker Compose | التطبيق هيكون standalone .exe |
| Nginx | PyWebView هيسيرف الـ Frontend |
| Multi-tenant Logic | Single-client system |
| Platform Auth (hashed_password) | غير مطلوب |
| Seller Registration Endpoints | العميل يتصل مباشرة بـ Amazon |

### 🟢 ما سيتم بناؤه

| المكون | الوصف |
|--------|-------|
| Amazon Direct Connect | 4 مفاتيح فقط (Client ID, Secret, Refresh Token, Seller ID) |
| SQLite Database | ملف `.db` واحد محفوظ في AppData |
| Asyncio Task Engine | مهام خلفية بدون Celery/Redis |
| PyWebView Desktop App | نافذة Windows مستقلة |
| PyInstaller .exe | ملف تنفيذي واحد للعميل |
| Single-Client Dashboard | إحصائيات + تحكم كامل |
| Product CRUD | إضافة/تعديل/حذف/عرض |
| Bulk Upload (CSV/Excel) | رفع جماعي للمنتجات |
| Amazon Sync | سحب المنتجات من أمازون |
| Real-time Status | متابعة حالة الرفع |
| Premium Dark UI | تصميم فخم |
| Local File Paths | Logs + DB في AppData |

### 🔄 مقارنة: قبل vs بعد

| المكون | قبل (v2.0 SaaS) | بعد (v3.0 Desktop) |
|--------|-----------------|---------------------|
| **Database** | PostgreSQL (Docker) | SQLite (ملف محلي) |
| **Task Queue** | Celery + Redis | Asyncio + Background Threads |
| **Deployment** | Docker Compose (GCP) | PyInstaller .exe (Windows) |
| **Frontend Server** | Nginx (Docker) | PyWebView (مدمج في الـ .exe) |
| **Backend Server** | FastAPI (Docker) | FastAPI (مدمج في الـ .exe) |
| **File Paths** | `/app/` في Docker | `%APPDATA%/CrazyLister/` |
| **Distribution** | Git + Docker Pull | ملف .exe واحد |
| **Startup** | `docker compose up` | دبل كليك على الـ .exe |

---

## 2. التغييرات التقنية الأساسية

### 2.1 Database: PostgreSQL → SQLite

**لماذا SQLite؟**
- ✅ ملف واحد (`.db`) — لا يحتاج سيرفر
- ✅ يعمل محلياً بدون أي setup
- ✅ سريع كفاية لعميل واحد
- ✅ مدعوم من SQLAlchemy بدون أي تعديل في الـ Models

**التغييرات المطلوبة:**

```python
# backend/app/database.py — قبل (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/crazy_lister")
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# بعد (SQLite)
import os
from pathlib import Path

# مسار قاعدة البيانات في AppData
APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

**ملاحظات مهمة:**
- SQLite لا يدعم `pool_size` أو `max_overflow` → نحذفهم
- SQLite يحتاج `check_same_thread=False` عشان FastAPI يشتغل
- SQLite لا يدعم بعض الـ PostgreSQL-specific types (مثل `ARRAY`) → نستخدم `JSON` بدلاً منها

### 2.2 Task Queue: Celery + Redis → Asyncio

**لماذا Asyncio؟**
- ✅ لا يحتاج Redis (بدون Broker)
- ✅ لا يحتاج Celery Worker (بدون process منفصل)
- ✅ يعمل داخل نفس الـ Python process
- ✅ أخف وأسرع للتطبيقات الصغيرة

**التغييرات المطلوبة:**

```python
# قبل (Celery Task)
# backend/app/tasks/listing_tasks.py
@shared_task(bind=True, max_retries=3)
def submit_listing_task(self, product_id: str, seller_id: str):
    ...
    self.retry(countdown=60)

# بعد (Asyncio Task)
# backend/app/tasks/listing_tasks.py
import asyncio
from datetime import datetime

async def submit_listing_task(product_id: str):
    """Submit product listing to Amazon (async)"""
    from app.database import SessionLocal
    from app.models.seller import Seller
    from app.models.listing import Listing
    from app.models.product import Product
    from app.services.amazon_api import AmazonSPAPIClient
    from loguru import logger

    db = SessionLocal()
    try:
        # Get seller
        seller = db.query(Seller).first()
        if not seller or not seller.is_connected:
            raise ValueError("Amazon not connected")

        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Create listing record
        listing = Listing(
            product_id=product.id,
            status="processing",
            submitted_at=datetime.utcnow(),
        )
        db.add(listing)
        db.commit()

        # Submit to Amazon
        client = AmazonSPAPIClient(
            client_id=seller.lwa_client_id,
            client_secret=seller.lwa_client_secret,
            refresh_token=seller.lwa_refresh_token,
            seller_id=seller.amazon_seller_id,
        )

        result = await client.submit_listing(product.to_dict())

        if result.get("success"):
            listing.status = "success"
            listing.amazon_asin = result.get("asin")
            listing.completed_at = datetime.utcnow()
            logger.info(f"Listing submitted: {product.sku} → ASIN {result.get('asin')}")
        else:
            listing.status = "failed"
            listing.error_message = result.get("error", "Unknown error")
            logger.error(f"Listing failed: {product.sku} — {result.get('error')}")

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Task failed: {str(e)}")
        # Update listing status
        listing = db.query(Listing).filter(Listing.product_id == product_id).order_by(Listing.created_at.desc()).first()
        if listing:
            listing.status = "failed"
            listing.error_message = str(e)
            db.commit()
    finally:
        db.close()
```

**Task Manager (بدلاً من Celery):**

```python
# backend/app/tasks/task_manager.py
"""
Background Task Manager
Replaces Celery with asyncio-based task queue
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

class TaskManager:
    """Manages background tasks using asyncio"""

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, dict] = {}

    async def submit(self, task_id: str, coro) -> str:
        """Submit a task to run in background"""
        async def wrapper():
            try:
                result = await coro
                self._results[task_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.utcnow().isoformat(),
                }
                return result
            except Exception as e:
                self._results[task_id] = {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.utcnow().isoformat(),
                }
                raise

        self._tasks[task_id] = asyncio.create_task(wrapper())
        self._results[task_id] = {
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"Task submitted: {task_id}")
        return task_id

    def get_status(self, task_id: str) -> Optional[dict]:
        """Get task status"""
        return self._results.get(task_id)

    def list_tasks(self) -> Dict[str, dict]:
        """List all tasks"""
        return self._results.copy()

# Global task manager instance
task_manager = TaskManager()
```

### 2.3 Desktop Wrapper: PyWebView

**لماذا PyWebView؟**
- ✅ أخف من Electron (50MB vs 150MB+)
- ✅ يستخدم WebView2 المدمج في Windows 10/11
- ✅ سهل الدمج مع FastAPI
- ✅ لا يحتاج Node.js أو npm

**الكود:**

```python
# backend/app/desktop.py
"""
Desktop App Launcher
Launches FastAPI backend + PyWebView frontend
"""
import os
import sys
import threading
import time
from pathlib import Path
import uvicorn
import webview
from loguru import logger

# Setup paths for PyInstaller
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    BASE_DIR = Path(sys._MEIPASS)
    APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
else:
    BASE_DIR = Path(__file__).parent.parent
    APP_DATA_DIR = BASE_DIR / "app_data"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging to file in AppData
log_file = APP_DATA_DIR / "crazy_lister.log"
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)
logger.add(
    str(log_file),
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
)

def start_backend():
    """Start FastAPI server in background thread"""
    logger.info("Starting FastAPI backend...")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="warning",
    )

def create_app():
    """Create and run the desktop app"""
    logger.info("Starting Crazy Lister v3.0...")

    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for backend to start
    time.sleep(2)

    # Determine frontend path
    if getattr(sys, 'frozen', False):
        # Running as .exe — frontend is in _MEIPASS
        frontend_path = str(BASE_DIR / "frontend" / "dist" / "index.html")
    else:
        # Development mode
        frontend_path = str(BASE_DIR.parent / "frontend" / "dist" / "index.html")

    if not os.path.exists(frontend_path):
        logger.error(f"Frontend not found at: {frontend_path}")
        sys.exit(1)

    logger.info(f"Loading frontend from: {frontend_path}")

    # Create PyWebView window
    window = webview.create_window(
        title="Crazy Lister v3.0",
        url=f"file:///{frontend_path}",
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        background_color="#0a0a0f",
    )

    # Start PyWebView
    webview.start()

if __name__ == "__main__":
    create_app()
```

### 2.4 File Paths: Windows AppData

**كل الملفات هتتحفظ في:**

```
%APPDATA%/CrazyLister/
├── crazy_lister.db          # SQLite Database
├── crazy_lister.log         # Log file
├── uploads/                 # Uploaded CSV/Excel files
│   └── bulk_20260409_143022.xlsx
└── exports/                 # Exported reports
    └── products_20260409.csv
```

**الكود:**

```python
# backend/app/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Windows AppData paths
APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = APP_DATA_DIR / "uploads"
EXPORT_DIR = APP_DATA_DIR / "exports"
LOG_FILE = APP_DATA_DIR / "crazy_lister.log"

for d in [UPLOAD_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "Crazy Lister v3.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # SQLite Database
    DATABASE_URL: str = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"

    # Amazon SP-API (empty by default — user will configure)
    USE_AMAZON_MOCK: bool = False

    # CORS (localhost only for desktop app)
    CORS_ORIGINS: list[str] = ["*"]

    # File paths
    UPLOAD_DIR: str = str(UPLOAD_DIR)
    EXPORT_DIR: str = str(EXPORT_DIR)
    LOG_FILE: str = str(LOG_FILE)

    model_config = {"env_file": ".env", "extra": "ignore"}
```

---

## 3. الملفات المتأثرة

### 🗑️ ملفات سيتم حذفها بالكامل

```
backend/app/api/auth/
├── __init__.py              ❌ حذف
── endpoints.py             ❌ حذف (JWT auth)
├── service.py               ❌ حذف (JWT helpers)
└── schemas.py               ❌ حذف (auth models)

backend/app/seed.py          ❌ حذف (demo user seeding)

backend/app/tasks/
├── celery_app.py            ❌ حذف (Celery config)
└── listing_tasks.py         ⚠️ إعادة كتابة كاملة (Asyncio بدل Celery)

backend/app/middleware/
├── security.py              ❌ حذف (AuditLogMiddleware — مش مطلوب لعميل واحد)
└── TenantIsolationMiddleware ❌ حذف (مش مطلوب لعميل واحد)

backend/tests/               ❌ حذف (اختبارات JWT + Celery)

backend/static/              ❌ حذف (Swagger UI — مش مطلوب في Desktop App)

frontend/src/pages/auth/
├── LoginPage.tsx            ❌ حذف
└── RegisterPage.tsx         ❌ حذف

docker-compose.yml           ❌ حذف (مش محتاجين Docker)

frontend/nginx.conf          ❌ حذف (PyWebView هيسيرف الـ Frontend)

frontend/Dockerfile          ❌ حذف

backend/Dockerfile           ❌ حذف
```

### 📝 ملفات سيتم تعديلها

| # | الملف | نوع التعديل | % التغيير |
|---|-------|-------------|-----------|
| 1 | `backend/app/database.py` | PostgreSQL → SQLite + AppData paths | 80% |
| 2 | `backend/app/config.py` | SQLite + AppData + حذف Redis/Celery | 70% |
| 3 | `backend/app/main.py` | حذف seed.py + إضافة startup tasks | 40% |
| 4 | `backend/app/models/seller.py` | حذف email/hashed_password + إضافة Amazon fields | 70% |
| 5 | `backend/app/models/product.py` | إزالة seller_id FK أو nullable | 30% |
| 6 | `backend/app/models/listing.py` | إزالة seller_id FK أو nullable | 30% |
| 7 | `backend/app/models/task.py` | حذف (مش محتاجين Celery task model) | 100% |
| 8 | `backend/app/api/router.py` | حذف auth router + إضافة amazon_connect | 50% |
| 9 | `backend/app/api/products.py` | إزالة seller_id Query params | 60% |
| 10 | `backend/app/api/listings.py` | إزالة seller_id + إضافة task API | 70% |
| 11 | `backend/app/api/sellers.py` | تبسيط كامل (Amazon settings only) | 80% |
| 12 | `backend/app/api/feeds.py` | تعديل (بدون Celery) | 50% |
| 13 | `backend/requirements.txt` | حذف Celery/Redis/JWT + إضافة pywebview | 40% |
| 14 | `frontend/src/router.tsx` | حذف /login, /register + إضافة /connect | 50% |
| 15 | `frontend/src/api/endpoints.ts` | حذف authApi + إضافة amazonApi + taskApi | 70% |
| 16 | `frontend/src/api/hooks.ts` | حذف JWT hooks + إضافة Amazon/Task hooks | 70% |
| 17 | `frontend/src/lib/axios.ts` | تبسيط (إزالة JWT interceptor) | 40% |
| 18 | `frontend/src/types/api.ts` | حذف Login/Register types + إضافة Task types | 50% |
| 19 | `frontend/src/components/layout/Sidebar.tsx` | إزالة Logout | 10% |
| 20 | `frontend/src/pages/dashboard/DashboardPage.tsx` | إعادة بناء (Dark Mode) | 80% |
| 21 | `frontend/src/pages/products/ProductListPage.tsx` | تحديث API calls | 40% |
| 22 | `frontend/src/pages/products/ProductCreatePage.tsx` | إضافة Bulk Upload | 50% |
| 23 | `frontend/src/pages/listings/ListingQueuePage.tsx` | تحديث API calls | 40% |
| 24 | `frontend/src/pages/settings/SettingsPage.tsx` | إعادة بناء (Amazon settings) | 80% |
| 25 | `frontend/package.json` | إزالة dependencies غير ضرورية | 10% |
| 26 | `frontend/.env` | تغيير VITE_API_URL لـ http://127.0.0.1:8765/api/v1 | 20% |

### 🆕 ملفات سيتم إنشاؤها

| # | الملف | الوصف |
|---|-------|-------|
| 1 | `backend/app/desktop.py` | Desktop app launcher (PyWebView + FastAPI) |
| 2 | `backend/app/api/amazon_connect/__init__.py` | Package init |
| 3 | `backend/app/api/amazon_connect/endpoints.py` | Amazon connect API |
| 4 | `backend/app/api/amazon_connect/schemas.py` | Amazon connect schemas |
| 5 | `backend/app/api/amazon_connect/service.py` | Amazon SP-API verification |
| 6 | `backend/app/api/products_sync.py` | Sync products from Amazon |
| 7 | `backend/app/api/bulk_upload.py` | CSV/Excel bulk upload |
| 8 | `backend/app/api/tasks.py` | Task management API (get status, list tasks) |
| 9 | `backend/app/tasks/task_manager.py` | Asyncio-based task manager |
| 10 | `backend/app/tasks/listing_tasks.py` | Listing tasks (asyncio) |
| 11 | `backend/app/tasks/feed_tasks.py` | Feed tasks (asyncio) |
| 12 | `frontend/src/pages/amazon/AmazonConnectPage.tsx` | Amazon connect UI (Dark Mode) |
| 13 | `frontend/src/contexts/AmazonConnectContext.tsx` | Amazon connect context |
| 14 | `frontend/src/components/common/StatsCard.tsx` | Stats card component |
| 15 | `build.py` | PyInstaller build script |
| 16 | `crazy_lister.spec` | PyInstaller spec file |
| 17 | `README.md` | تحديث (Desktop App instructions) |

---

## 4. المرحلة 1: التنظيف والحذف

### المدة: 30 دقيقة

### 4.1 حذف ملفات الـ Auth

```powershell
# PowerShell (Windows)
Remove-Item -Recurse -Force backend\app\api\auth\
Remove-Item -Force backend\app\seed.py
Remove-Item -Recurse -Force backend\app\middleware\
Remove-Item -Recurse -Force backend\tests\
Remove-Item -Recurse -Force backend\static\
Remove-Item -Recurse -Force frontend\src\pages\auth\
```

### 4.2 حذف ملفات Docker

```powershell
Remove-Item -Force docker-compose.yml
Remove-Item -Force frontend\nginx.conf
Remove-Item -Force frontend\Dockerfile
Remove-Item -Force backend\Dockerfile
```

### 4.3 تنظيف `backend/app/api/router.py`

**قبل:**
```python
from app.api import sellers, products, listings, feeds
from app.api.auth import endpoints as auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
...
```

**بعد:**
```python
from fastapi import APIRouter
from app.api import amazon_connect, sellers, products, listings, feeds, products_sync, bulk_upload, tasks

api_router = APIRouter()

api_router.include_router(amazon_connect.router, prefix="/amazon", tags=["amazon"])
api_router.include_router(sellers.router, prefix="/sellers", tags=["sellers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
api_router.include_router(products_sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(bulk_upload.router, prefix="/bulk", tags=["bulk"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
```

### 4.4 تنظيف `backend/app/main.py`

حذف:
```python
from app.seed import seed_demo_user
...
seed_demo_user(db)
```

إضافة:
```python
from app.database import init_db

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Crazy Lister v3.0...")
    init_db()
    logger.info("Database initialized")
```

### 4.5 تنظيف `backend/requirements.txt`

**حذف:**
```
celery==5.3.6
redis==5.0.1
flower==2.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.6
email-validator==2.1.0
asyncpg==0.29.0
psycopg2-binary==2.9.9
```

**إضافة:**
```
pywebview==4.4.1
pyinstaller==6.5.0
openpyxl==3.1.2
pandas==2.2.0
aiofiles==23.2.1
```

**النسخة النهائية:**
```
# Core
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
pydantic==2.6.1
pydantic-settings==2.1.0
alembic==1.13.1

# Database (SQLite only)
aiosqlite==0.19.0

# Amazon SP-API
python-amazon-sp-api==2.1.8
boto3==1.34.34
botocore==1.34.34

# HTTP Client
requests==2.31.0
httpx==0.27.0
aiofiles==23.2.1

# Excel/CSV
openpyxl==3.1.2
pandas==2.2.0

# Logging
loguru==0.7.2

# Validation
pydantic[email]==2.6.1

# Desktop
pywebview==4.4.1

# Build
pyinstaller==6.5.0

# Utils
python-dotenv==1.0.0
```

---

## 5. المرحلة 2: SQLite + Database Migration

### المدة: 1-2 ساعة

### 5.1 تحديث `backend/app/database.py`

```python
"""
Database Configuration
SQLite for local desktop app
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from loguru import logger

# Windows AppData path
APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"

# SQLite-specific engine config
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables"""
    from app.models import seller, product, listing  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at: {APP_DATA_DIR}/crazy_lister.db")


# Enable WAL mode for better performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=memory")
    cursor.close()
```

**النقاط المهمة:**
- `StaticPool` لأن SQLite مش محتاج connection pool
- `check_same_thread=False` عشان FastAPI بيستخدم threads متعددة
- `WAL mode` لتحسين الأداء
- المسار في `%APPDATA%/CrazyLister/`

### 5.2 Seller Model

**الملف:** `backend/app/models/seller.py`

```python
"""
Seller Account Model - Single Client
Stores Amazon SP-API credentials
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Seller(Base):
    """Single seller account with Amazon credentials"""

    __tablename__ = "sellers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Amazon SP-API Credentials (المفاتيح الأربعة)
    lwa_client_id = Column(String(255), nullable=False)        # Client ID
    lwa_client_secret = Column(String(255), nullable=False)    # Client Secret
    lwa_refresh_token = Column(Text, nullable=False)           # Refresh Token
    amazon_seller_id = Column(String(100), nullable=False)     # Seller ID

    # Optional Info
    display_name = Column(String(200), default="My Amazon Store")
    marketplace_id = Column(String(20), default="ARBP9OOSHTCHU")
    region = Column(String(10), default="EU")

    # Connection Status
    is_connected = Column(Boolean, default=False)
    last_sync_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Seller {self.display_name} ({self.amazon_seller_id})>"
```

**التغيير:** `UUID(as_uuid=True)` → `String(36)` لأن SQLite لا يدعم UUID بشكل native.

### 5.3 Product Model

**الملف:** `backend/app/models/product.py`

```python
"""
Product Model
"""
from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime, Boolean
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Product(Base):
    """Product catalog model"""

    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic Information
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    category = Column(String(100))
    brand = Column(String(200))

    # Identifiers
    upc = Column(String(50))
    ean = Column(String(50))

    # Content
    description = Column(Text)
    bullet_points = Column(Text, default="[]")  # JSON string
    keywords = Column(Text, default="[]")  # JSON string

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    compare_price = Column(Numeric(10, 2))
    cost = Column(Numeric(10, 2))

    # Inventory
    quantity = Column(Integer, default=0)
    weight = Column(Numeric(8, 2))

    # Dimensions (JSON string)
    dimensions = Column(Text, default="{}")

    # Media
    images = Column(Text, default="[]")  # JSON string

    # Additional Attributes
    attributes = Column(Text, default="{}")  # JSON string

    # Status
    status = Column(String(20), default="draft")

    # AI Optimization
    optimized_data = Column(Text)  # JSON string

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"
```

**التغييرات:**
- `UUID` → `String(36)`
- `JSON` → `Text` (SQLite لا يدعم JSON بشكل native في SQLAlchemy القديم)
- `ARRAY` → `Text` (JSON string)
- إزالة `seller_id` ForeignKey

### 5.4 Listing Model

**الملف:** `backend/app/models/listing.py`

```python
"""
Listing Model
"""
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Listing(Base):
    """Listing submission model"""

    __tablename__ = "listings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), nullable=False, index=True)

    # Amazon Integration
    feed_submission_id = Column(String(100))
    status = Column(String(30), default="queued")

    # Results
    amazon_asin = Column(String(20))
    amazon_url = Column(String(500))
    error_message = Column(Text)

    # Queue Management
    queue_position = Column(Integer)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Listing {self.id} - {self.status}>"
```

---

## 6. المرحلة 3: إزالة Celery/Redis + Asyncio Engine

### المدة: 2-3 ساعات

### 6.1 Task Manager (Asyncio-based)

**الملف:** `backend/app/tasks/task_manager.py`

```python
"""
Background Task Manager
Replaces Celery with asyncio-based task queue
"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class TaskManager:
    """Manages background tasks using asyncio"""

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, dict] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """Start the task worker"""
        self._running = True
        logger.info("Task manager started")
        asyncio.create_task(self._worker())

    async def _worker(self):
        """Background worker that processes tasks from queue"""
        while self._running:
            try:
                task_id, coro = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._execute_task(task_id, coro)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")

    async def _execute_task(self, task_id: str, coro):
        """Execute a single task"""
        try:
            self._results[task_id] = {
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }
            result = await coro
            self._results[task_id] = {
                "status": "completed",
                "result": result,
                "completed_at": datetime.utcnow().isoformat(),
            }
            logger.info(f"Task completed: {task_id}")
        except Exception as e:
            self._results[task_id] = {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat(),
            }
            logger.error(f"Task failed: {task_id} — {str(e)}")

    async def submit(self, coro) -> str:
        """Submit a task to the queue"""
        task_id = str(uuid.uuid4())
        await self._queue.put((task_id, coro))
        logger.info(f"Task queued: {task_id}")
        return task_id

    def get_status(self, task_id: str) -> Optional[dict]:
        """Get task status"""
        return self._results.get(task_id)

    def list_all(self) -> Dict[str, dict]:
        """List all tasks"""
        return self._results.copy()

    def stop(self):
        """Stop the task worker"""
        self._running = False
        logger.info("Task manager stopped")


# Global instance
task_manager = TaskManager()
```

### 6.2 Listing Tasks (Asyncio)

**الملف:** `backend/app/tasks/listing_tasks.py`

```python
"""
Listing Tasks (Asyncio-based)
Replaces Celery tasks
"""
import asyncio
from datetime import datetime
from app.database import SessionLocal
from app.models.seller import Seller
from app.models.listing import Listing
from app.models.product import Product
from app.services.amazon_api import AmazonSPAPIClient
from loguru import logger


async def submit_listing_task(product_id: str) -> dict:
    """Submit a product listing to Amazon"""
    db = SessionLocal()
    try:
        # Get seller
        seller = db.query(Seller).first()
        if not seller or not seller.is_connected:
            raise ValueError("Amazon not connected")

        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Create listing record
        listing = Listing(
            product_id=product.id,
            status="processing",
            submitted_at=datetime.utcnow(),
        )
        db.add(listing)
        db.commit()

        # Submit to Amazon
        client = AmazonSPAPIClient(
            client_id=seller.lwa_client_id,
            client_secret=seller.lwa_client_secret,
            refresh_token=seller.lwa_refresh_token,
            seller_id=seller.amazon_seller_id,
        )

        result = await client.submit_listing(product.to_dict())

        if result.get("success"):
            listing.status = "success"
            listing.amazon_asin = result.get("asin")
            listing.amazon_url = result.get("url")
            listing.completed_at = datetime.utcnow()
            logger.info(f"Listing submitted: {product.sku} → ASIN {result.get('asin')}")
        else:
            listing.status = "failed"
            listing.error_message = result.get("error", "Unknown error")
            logger.error(f"Listing failed: {product.sku}")

        db.commit()

        return {"status": listing.status, "asin": listing.amazon_asin}

    except Exception as e:
        db.rollback()
        logger.error(f"Submit listing failed: {str(e)}")

        # Update listing
        listing = db.query(Listing).filter(
            Listing.product_id == product_id
        ).order_by(Listing.created_at.desc()).first()
        if listing:
            listing.status = "failed"
            listing.error_message = str(e)
            db.commit()

        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


async def retry_listing_task(listing_id: str) -> dict:
    """Retry a failed listing"""
    db = SessionLocal()
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # Reset status
        listing.status = "queued"
        listing.error_message = None
        listing.submitted_at = None
        listing.completed_at = None
        db.commit()

        # Re-submit
        result = await submit_listing_task(listing.product_id)
        return result

    except Exception as e:
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
```

### 6.3 Tasks API

**الملف:** `backend/app/api/tasks.py`

```python
"""
Tasks API
Manage background tasks
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.tasks.task_manager import task_manager
from app.tasks.listing_tasks import submit_listing_task, retry_listing_task
from app.models.listing import Listing
from loguru import logger

router = APIRouter()


@router.post("/submit-listing")
async def submit_listing(product_id: str):
    """Submit a product listing (async)"""
    task_id = await task_manager.submit(submit_listing_task(product_id))
    return {"task_id": task_id, "message": "Listing submitted in background"}


@router.post("/retry-listing/{listing_id}")
async def retry_listing(listing_id: str):
    """Retry a failed listing"""
    task_id = await task_manager.submit(retry_listing_task(listing_id))
    return {"task_id": task_id, "message": "Retry submitted in background"}


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Get task status"""
    status = task_manager.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/")
async def list_tasks():
    """List all tasks"""
    return task_manager.list_all()
```

### 6.4 تحديث `backend/app/main.py` لبدء Task Manager

```python
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Starting Crazy Lister v3.0...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Start task manager
    from app.tasks.task_manager import task_manager
    asyncio.create_task(task_manager.start())
    logger.info("Task manager started")
```

---

## 7. المرحلة 4: إعادة بناء Backend APIs

### المدة: 2-3 ساعات

### 7.1 Amazon Connect API

**الملف:** `backend/app/api/amazon_connect/endpoints.py`

```python
"""
Amazon Connect API
Handles Amazon SP-API credentials storage and verification
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.api.amazon_connect.schemas import (
    AmazonConnectRequest,
    AmazonConnectResponse,
    AmazonVerifyResponse,
)
from app.api.amazon_connect.service import amazon_service

router = APIRouter()


@router.post("/connect", response_model=AmazonConnectResponse)
async def connect_amazon(data: AmazonConnectRequest, db: Session = Depends(get_db)):
    """
    Save Amazon credentials for the single seller.
    Overwrites any existing seller record.
    """
    seller = db.query(Seller).first()

    if seller:
        seller.lwa_client_id = data.lwa_client_id
        seller.lwa_client_secret = data.lwa_client_secret
        seller.lwa_refresh_token = data.lwa_refresh_token
        seller.amazon_seller_id = data.amazon_seller_id
        seller.display_name = data.display_name or seller.display_name
        seller.marketplace_id = data.marketplace_id or seller.marketplace_id
        seller.is_connected = False
        logger.info(f"Updated seller: {data.amazon_seller_id}")
    else:
        seller = Seller(
            lwa_client_id=data.lwa_client_id,
            lwa_client_secret=data.lwa_client_secret,
            lwa_refresh_token=data.lwa_refresh_token,
            amazon_seller_id=data.amazon_seller_id,
            display_name=data.display_name or "My Amazon Store",
            marketplace_id=data.marketplace_id or "ARBP9OOSHTCHU",
            region="EU",
            is_connected=False,
        )
        db.add(seller)
        logger.info(f"Created new seller: {data.amazon_seller_id}")

    db.commit()
    db.refresh(seller)

    return AmazonConnectResponse(
        seller_id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        is_connected=seller.is_connected,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        message="Credentials saved. Click 'Verify' to test connection.",
    )


@router.post("/verify", response_model=AmazonVerifyResponse)
async def verify_connection(db: Session = Depends(get_db)):
    """Test Amazon SP-API connection"""
    seller = db.query(Seller).first()
    if not seller:
        raise HTTPException(status_code=404, detail="No seller configured")

    is_valid = await amazon_service.verify_connection(
        client_id=seller.lwa_client_id,
        client_secret=seller.lwa_client_secret,
        refresh_token=seller.lwa_refresh_token,
        seller_id=seller.amazon_seller_id,
    )

    if is_valid:
        seller.is_connected = True
        db.commit()
        return AmazonVerifyResponse(is_connected=True, message="Connected to Amazon successfully!")
    else:
        seller.is_connected = False
        db.commit()
        raise HTTPException(status_code=400, detail="Failed to connect to Amazon. Check your credentials.")


@router.get("/status", response_model=AmazonConnectResponse)
async def get_connection_status(db: Session = Depends(get_db)):
    """Get current Amazon connection status"""
    seller = db.query(Seller).first()

    if not seller:
        return AmazonConnectResponse(
            seller_id=None,
            amazon_seller_id=None,
            is_connected=False,
            message="No seller configured",
        )

    return AmazonConnectResponse(
        seller_id=str(seller.id),
        amazon_seller_id=seller.amazon_seller_id,
        is_connected=seller.is_connected,
        display_name=seller.display_name,
        marketplace_id=seller.marketplace_id,
        last_sync_at=seller.last_sync_at.isoformat() if seller.last_sync_at else None,
        message="Connected" if seller.is_connected else "Not connected",
    )
```

### 7.2 Amazon Connect Schemas

**الملف:** `backend/app/api/amazon_connect/schemas.py`

```python
"""
Amazon Connect Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional


class AmazonConnectRequest(BaseModel):
    lwa_client_id: str = Field(..., description="Amazon LWA Client ID")
    lwa_client_secret: str = Field(..., description="Amazon LWA Client Secret")
    lwa_refresh_token: str = Field(..., description="Amazon LWA Refresh Token")
    amazon_seller_id: str = Field(..., description="Amazon Seller/Merchant ID")
    display_name: Optional[str] = Field("My Amazon Store", max_length=200)
    marketplace_id: Optional[str] = Field("ARBP9OOSHTCHU", description="Marketplace ID")


class AmazonConnectResponse(BaseModel):
    seller_id: Optional[str]
    amazon_seller_id: Optional[str]
    is_connected: bool
    display_name: Optional[str] = None
    marketplace_id: Optional[str] = None
    last_sync_at: Optional[str] = None
    message: str


class AmazonVerifyResponse(BaseModel):
    is_connected: bool
    message: str
```

### 7.3 Amazon Connect Service

**الملف:** `backend/app/api/amazon_connect/service.py`

```python
"""
Amazon SP-API Verification Service
"""
from loguru import logger
from app.services.amazon_api import AmazonSPAPIClient


class AmazonConnectionService:
    async def verify_connection(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        seller_id: str,
    ) -> bool:
        try:
            client = AmazonSPAPIClient(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                seller_id=seller_id,
            )
            result = await client.get_account_info()
            if result:
                logger.info("Amazon connection verified")
                return True
            return False
        except Exception as e:
            logger.error(f"Amazon connection failed: {str(e)}")
            return False


amazon_service = AmazonConnectionService()
```

### 7.4 Products API (بدون seller_id)

**الملف:** `backend/app/api/products.py`

```python
"""
Product API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import json
from decimal import Decimal

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductListResponse, MessageResponse
from loguru import logger

router = APIRouter()


def product_to_dict(product: Product) -> dict:
    """Convert Product model to dict (handle JSON strings)"""
    d = {c.name: getattr(product, c.name) for c in product.__table__.columns}
    # Parse JSON strings
    for field in ['bullet_points', 'keywords', 'images', 'dimensions', 'attributes', 'optimized_data']:
        val = d.get(field)
        if val and isinstance(val, str):
            try:
                d[field] = json.loads(val)
            except:
                d[field] = [] if field != 'dimensions' and field != 'attributes' and field != 'optimized_data' else {}
    # Convert Decimal to float
    for field in ['price', 'compare_price', 'cost', 'weight']:
        if d.get(field) is not None:
            d[field] = float(d[field])
    return d


@router.get("/", response_model=ProductListResponse)
async def list_products(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if status:
        query = query.filter(Product.status == status)
    if category:
        query = query.filter(Product.category == category)

    total = query.count()
    products = query.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListResponse(
        items=[product_to_dict(p) for p in products],
        total=total,
        page=page,
        pages=(total + page_size - 1) // page_size,
        has_next=page * page_size < total,
        has_prev=page > 1,
    )


@router.post("/", status_code=201)
async def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        sku=data.sku,
        name=data.name,
        category=data.category or "",
        brand=data.brand or "",
        price=data.price,
        quantity=data.quantity or 0,
        description=data.description or "",
        bullet_points=json.dumps(data.bullet_points or []),
        images=json.dumps(data.images or []),
        attributes=json.dumps(data.attributes or {}),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_to_dict(product)


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
```

### 7.5 Listings API (بدون seller_id + مع Task API)

**الملف:** `backend/app/api/listings.py`

```python
"""
Listing API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.listing import Listing
from app.tasks.task_manager import task_manager
from app.tasks.listing_tasks import submit_listing_task, retry_listing_task
from loguru import logger

router = APIRouter()


@router.get("/")
async def list_listings(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).order_by(Listing.created_at.desc())
    if status:
        query = query.filter(Listing.status == status)
    listings = query.all()
    return [
        {c.name: getattr(l, c.name) for c in l.__table__.columns}
        for l in listings
    ]


@router.post("/submit")
async def submit_listing(product_id: str):
    """Submit a product listing (async)"""
    task_id = await task_manager.submit(submit_listing_task(product_id))
    return {"task_id": task_id, "message": "Listing submitted in background"}


@router.post("/{listing_id}/retry")
async def retry_listing(listing_id: str):
    """Retry a failed listing"""
    task_id = await task_manager.submit(retry_listing_task(listing_id))
    return {"task_id": task_id, "message": "Retry submitted in background"}
```

### 7.6 Product Sync API

**الملف:** `backend/app/api/products_sync.py`

```python
"""
Product Sync API
Pulls products from Amazon SP-API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json
from loguru import logger

from app.database import get_db
from app.models.seller import Seller
from app.models.product import Product
from app.services.amazon_api import AmazonSPAPIClient

router = APIRouter()


@router.post("/sync")
async def sync_products_from_amazon(db: Session = Depends(get_db)):
    """Pull all products from Amazon"""
    seller = db.query(Seller).first()
    if not seller or not seller.is_connected:
        raise HTTPException(status_code=400, detail="Amazon not connected")

    try:
        client = AmazonSPAPIClient(
            client_id=seller.lwa_client_id,
            client_secret=seller.lwa_client_secret,
            refresh_token=seller.lwa_refresh_token,
            seller_id=seller.amazon_seller_id,
        )

        amazon_products = await client.get_listings()

        synced_count = 0
        for item in amazon_products:
            existing = db.query(Product).filter(Product.sku == item.sku).first()
            if not existing:
                product = Product(
                    sku=item.sku,
                    name=item.title or item.sku,
                    price=item.price,
                    quantity=item.quantity or 0,
                    category=item.category or "",
                    brand=item.brand or "",
                    status="published",
                )
                db.add(product)
                synced_count += 1

        db.commit()
        seller.last_sync_at = datetime.utcnow()
        db.commit()

        logger.info(f"Synced {synced_count} products from Amazon")
        return {"message": f"Synced {synced_count} products", "synced_count": synced_count}

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
```

### 7.7 Bulk Upload API

**الملف:** `backend/app/api/bulk_upload.py`

```python
"""
Bulk Upload API
CSV/Excel file uploads
"""
import os
import io
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from loguru import logger
import pandas as pd

from app.database import get_db
from app.models.product import Product
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/upload")
async def bulk_upload_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload CSV or Excel file"""
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    # Save file to uploads folder
    upload_dir = Path(settings.UPLOAD_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = upload_dir / f"bulk_{timestamp}_{file.filename}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        required = ['sku', 'name', 'price']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

        created_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                product = Product(
                    sku=str(row['sku']),
                    name=str(row['name']),
                    price=float(row['price']),
                    quantity=int(row.get('quantity', 0)),
                    category=str(row.get('category', '')),
                    brand=str(row.get('brand', '')),
                    description=str(row.get('description', '')),
                )
                db.add(product)
                created_count += 1
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")

        db.commit()
        logger.info(f"Bulk uploaded {created_count} products")

        return {
            "message": f"Uploaded {created_count} products",
            "created_count": created_count,
            "errors": errors[:10],
            "file_path": str(file_path),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Bulk upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

---

## 8. المرحلة 5: إعادة بناء Frontend (Dark Mode)

### المدة: 3-4 ساعات

### 8.1 تحديث `frontend/.env`

```env
# Desktop App — FastAPI runs on localhost:8765
VITE_API_URL=http://127.0.0.1:8765/api/v1
```

### 8.2 تبسيط `frontend/src/lib/axios.ts`

```ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8765/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// No auth interceptor — single client desktop app

export default api
```

### 8.3 Amazon Connect Context

**الملف:** `frontend/src/contexts/AmazonConnectContext.tsx`

```tsx
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import api from '@/lib/axios'
import toast from 'react-hot-toast'

interface AmazonConnectStatus {
  seller_id: string | null
  amazon_seller_id: string | null
  is_connected: boolean
  display_name: string | null
  marketplace_id: string | null
  last_sync_at: string | null
  message: string
}

interface AmazonConnectContextType {
  status: AmazonConnectStatus | null
  isConnected: boolean
  isLoading: boolean
  connect: (data: any) => Promise<void>
  verify: () => Promise<void>
  refreshStatus: () => Promise<void>
}

const AmazonConnectContext = createContext<AmazonConnectContextType | null>(null)

export function AmazonConnectProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AmazonConnectStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    refreshStatus()
  }, [])

  const refreshStatus = async () => {
    try {
      const { data } = await api.get<AmazonConnectStatus>('/amazon/status')
      setStatus(data)
    } catch {
      setStatus({
        seller_id: null, amazon_seller_id: null, is_connected: false,
        display_name: null, marketplace_id: null, last_sync_at: null,
        message: 'Not configured',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const connect = async (data: any) => {
    const { data: result } = await api.post('/amazon/connect', data)
    setStatus(result)
    toast.success('تم حفظ بيانات Amazon')
  }

  const verify = async () => {
    const { data } = await api.post('/amazon/verify')
    setStatus(prev => prev ? { ...prev, is_connected: true, message: data.message } : null)
    toast.success('تم الاتصال بـ Amazon بنجاح!')
  }

  return (
    <AmazonConnectContext.Provider value={{ status, isConnected: status?.is_connected ?? false, isLoading, connect, verify, refreshStatus }}>
      {children}
    </AmazonConnectContext.Provider>
  )
}

export function useAmazonConnect() {
  const context = useContext(AmazonConnectContext)
  if (!context) throw new Error('useAmazonConnect must be used within AmazonConnectProvider')
  return context
}
```

### 8.4 Amazon Connect Page (Dark Mode)

**الملف:** `frontend/src/pages/amazon/AmazonConnectPage.tsx`

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAmazonConnect } from '@/contexts/AmazonConnectContext'
import { Shield, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AmazonConnectPage() {
  const navigate = useNavigate()
  const { connect, verify, isConnected, isLoading } = useAmazonConnect()

  const [formData, setFormData] = useState({
    lwa_client_id: '',
    lwa_client_secret: '',
    lwa_refresh_token: '',
    amazon_seller_id: '',
    display_name: 'My Amazon Store',
    marketplace_id: 'ARBP9OOSHTCHU',
  })
  const [isSaving, setIsSaving] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.lwa_client_id || !formData.lwa_client_secret ||
        !formData.lwa_refresh_token || !formData.amazon_seller_id) {
      toast.error('يرجى ملء جميع الحقول المطلوبة')
      return
    }
    setIsSaving(true)
    try {
      await connect(formData)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل حفظ البيانات')
    } finally {
      setIsSaving(false)
    }
  }

  const handleVerify = async () => {
    setIsVerifying(true)
    try {
      await verify()
      setTimeout(() => navigate('/dashboard'), 1500)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'فشل الاتصال')
    } finally {
      setIsVerifying(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    )
  }

  if (isConnected) { navigate('/dashboard'); return null }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-500/10 mb-4">
            <Shield className="w-8 h-8 text-orange-500" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">ربط حساب Amazon</h1>
          <p className="text-gray-400 text-sm">أدخل بيانات حسابك في Amazon Seller Central</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[#12121a] rounded-2xl p-6 space-y-4 border border-gray-800/50">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Client ID <span className="text-red-500">*</span></label>
            <input type="text" value={formData.lwa_client_id} onChange={e => setFormData({...formData, lwa_client_id: e.target.value})}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="amzn1.application-oa2-client.xxx" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Client Secret <span className="text-red-500">*</span></label>
            <input type="password" value={formData.lwa_client_secret} onChange={e => setFormData({...formData, lwa_client_secret: e.target.value})}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="••••••••" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Refresh Token <span className="text-red-500">*</span></label>
            <input type="password" value={formData.lwa_refresh_token} onChange={e => setFormData({...formData, lwa_refresh_token: e.target.value})}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="Atzr|xxx" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Seller ID <span className="text-red-500">*</span></label>
            <input type="text" value={formData.amazon_seller_id} onChange={e => setFormData({...formData, amazon_seller_id: e.target.value})}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition"
              placeholder="A1B2C3D4E5F6G7" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Display Name</label>
            <input type="text" value={formData.display_name} onChange={e => setFormData({...formData, display_name: e.target.value})}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Marketplace</label>
            <select value={formData.marketplace_id} onChange={e => setFormData({...formData, marketplace_id: e.target.value})}
              className="w-full bg-[#1a1a2e] border border-gray-700/50 rounded-lg px-4 py-3 text-white focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none transition">
              <option value="ARBP9OOSHTCHU">مصر (Egypt)</option>
              <option value="ATVPDKIKX0DER">أمريكا (US)</option>
              <option value="A1F83G8C2ARO7P">بريطانيا (UK)</option>
              <option value="A1PA6795UKMFR9">ألمانيا (Germany)</option>
            </select>
          </div>
          <button type="submit" disabled={isSaving}
            className="w-full bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-all flex items-center justify-center gap-2">
            {isSaving ? <><Loader2 className="w-5 h-5 animate-spin" /> جاري الحفظ...</> : 'حفظ البيانات'}
          </button>
        </form>

        {formData.amazon_seller_id && (
          <button onClick={handleVerify} disabled={isVerifying}
            className="mt-4 w-full bg-[#1a1a2e] hover:bg-[#22223a] disabled:opacity-50 text-gray-300 font-medium py-3 rounded-lg border border-gray-700/50 transition-colors flex items-center justify-center gap-2">
            {isVerifying ? <><Loader2 className="w-5 h-5 animate-spin" /> جاري التحقق...</> : <><CheckCircle className="w-5 h-5" /> التحقق من الاتصال</>}
          </button>
        )}

        <div className="mt-6 bg-[#12121a]/50 rounded-xl p-4 border border-gray-800/50">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-400">
              <p className="font-medium text-gray-300 mb-1">من أين أجيب هذه البيانات؟</p>
              <p>1. Client ID & Secret → Amazon Developer Console</p>
              <p>2. Refresh Token → Amazon Developer Console → LWA</p>
              <p>3. Seller ID → Amazon Seller Central → Account Info</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### 8.5 Router

**الملف:** `frontend/src/router.tsx`

```tsx
import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAmazonConnect } from './contexts/AmazonConnectContext'
import Layout from './components/layout/Layout'

import AmazonConnectPage from './pages/amazon/AmazonConnectPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import ProductListPage from './pages/products/ProductListPage'
import ProductCreatePage from './pages/products/ProductCreatePage'
import ListingQueuePage from './pages/listings/ListingQueuePage'
import ReportsPage from './pages/reports/ReportsPage'
import SettingsPage from './pages/settings/SettingsPage'

function ConnectedLayout() {
  const { isConnected, isLoading } = useAmazonConnect()
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0a0f]">
        <div className="w-10 h-10 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }
  if (!isConnected) return <Navigate to="/connect" replace />
  return <Outlet />
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/connect" element={<AmazonConnectPage />} />
      <Route element={<ConnectedLayout />}>
        <Route element={<Layout />}>
          <Route path="" element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="products" element={<ProductListPage />} />
          <Route path="products/create" element={<ProductCreatePage />} />
          <Route path="listings" element={<ListingQueuePage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/connect" replace />} />
    </Routes>
  )
}
```

### 8.6 API Endpoints

**الملف:** `frontend/src/api/endpoints.ts`

```ts
import api from '@/lib/axios'
import type { Product, ProductCreate, ProductListResponse, Listing, MessageResponse, AmazonConnectRequest, AmazonConnectResponse } from '@/types/api'

// ==================== Amazon Connect API ====================
export const amazonApi = {
  connect: (data: AmazonConnectRequest) => api.post<AmazonConnectResponse>('/amazon/connect', data),
  verify: () => api.post('/amazon/verify'),
  status: () => api.get<AmazonConnectResponse>('/amazon/status'),
}

// ==================== Products API ====================
export const productsApi = {
  list: (params?: { status?: string; category?: string; page?: number }) =>
    api.get<ProductListResponse>('/products', { params }),
  get: (id: string) => api.get<Product>(`/products/${id}`),
  create: (data: ProductCreate) => api.post<Product>('/products', data),
  delete: (id: string) => api.delete<MessageResponse>(`/products/${id}`),
  bulkCreate: (products: ProductCreate[]) => api.post<Product[]>('/products/bulk-create', products),
}

// ==================== Listings API ====================
export const listingsApi = {
  list: (params?: { status?: string }) => api.get<Listing[]>('/listings', { params }),
  submit: (product_id: string) => api.post('/listings/submit', null, { params: { product_id } }),
  retry: (id: string) => api.post(`/listings/${id}/retry`),
}

// ==================== Tasks API ====================
export const tasksApi = {
  get: (task_id: string) => api.get(`/tasks/${task_id}`),
  list: () => api.get('/tasks/'),
}

// ==================== Sync API ====================
export const syncApi = {
  syncFromAmazon: () => api.post('/sync/sync'),
}

// ==================== Bulk Upload API ====================
export const bulkApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/bulk/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}
```

### 8.7 Types

**الملف:** `frontend/src/types/api.ts`

```ts
// حذف: LoginRequest, LoginResponse, RegisterRequest, RegisterResponse

export interface AmazonConnectRequest {
  lwa_client_id: string
  lwa_client_secret: string
  lwa_refresh_token: string
  amazon_seller_id: string
  display_name?: string
  marketplace_id?: string
}

export interface AmazonConnectResponse {
  seller_id: string | null
  amazon_seller_id: string | null
  is_connected: boolean
  display_name: string | null
  marketplace_id: string | null
  last_sync_at: string | null
  message: string
}

export interface Product {
  id: string
  sku: string
  name: string
  category: string
  brand: string
  price: number
  quantity: number
  status: string
  created_at: string
}

export interface ProductCreate {
  sku: string
  name: string
  category?: string
  brand?: string
  price: number
  quantity?: number
  description?: string
  bullet_points?: string[]
  images?: string[]
  attributes?: Record<string, any>
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface Listing {
  id: string
  product_id: string
  status: string
  amazon_asin: string | null
  error_message: string | null
  created_at: string
}

export interface TaskStatus {
  status: 'running' | 'completed' | 'failed'
  result?: any
  error?: string
  started_at?: string
  completed_at?: string
}

export interface MessageResponse {
  message: string
}
```

### 8.8 React Query Hooks

**الملف:** `frontend/src/api/hooks.ts`

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi, listingsApi, amazonApi, tasksApi, syncApi, bulkApi } from './endpoints'
import type { ProductCreate, AmazonConnectRequest } from '@/types/api'

// ==================== Product Keys ====================
export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (params: Record<string, unknown>) => [...productKeys.lists(), params] as const,
}

export const listingKeys = {
  all: ['listings'] as const,
  lists: () => [...listingKeys.all, 'list'] as const,
  list: (params: Record<string, unknown>) => [...listingKeys.lists(), params] as const,
}

export const amazonKeys = {
  status: ['amazon', 'status'] as const,
}

export const taskKeys = {
  list: () => ['tasks'] as const,
  detail: (id: string) => [...taskKeys.list(), id] as const,
}

// ==================== Product Hooks ====================
export function useProducts(params?: { status?: string; category?: string }) {
  return useQuery({
    queryKey: productKeys.list(params || {}),
    queryFn: async () => {
      const { data } = await productsApi.list({ ...params, page_size: 50 })
      return data
    },
    staleTime: 1000 * 60 * 2,
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (product: ProductCreate) => productsApi.create(product),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: productKeys.lists() }) },
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => productsApi.delete(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: productKeys.lists() }) },
  })
}

// ==================== Listing Hooks ====================
export function useListings(params?: { status?: string }) {
  return useQuery({
    queryKey: listingKeys.list(params || {}),
    queryFn: async () => {
      const { data } = await listingsApi.list(params)
      return data
    },
    staleTime: 1000 * 30,
    refetchInterval: 5000,
  })
}

export function useSubmitListing() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (product_id: string) => listingsApi.submit(product_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listingKeys.lists() })
      queryClient.invalidateQueries({ queryKey: taskKeys.list() })
    },
  })
}

// ==================== Amazon Connect Hooks ====================
export function useAmazonStatus() {
  return useQuery({
    queryKey: amazonKeys.status,
    queryFn: async () => { const { data } = await amazonApi.status(); return data },
    refetchInterval: 30000,
  })
}

export function useConnectAmazon() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AmazonConnectRequest) => amazonApi.connect(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: amazonKeys.status }) },
  })
}

export function useVerifyConnection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => amazonApi.verify(),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: amazonKeys.status }) },
  })
}

// ==================== Task Hooks ====================
export function useTasks() {
  return useQuery({
    queryKey: taskKeys.list(),
    queryFn: async () => { const { data } = await tasksApi.list(); return data },
    refetchInterval: 3000,
  })
}

export function useSyncFromAmazon() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => syncApi.syncFromAmazon(),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: productKeys.lists() }) },
  })
}

export function useBulkUpload() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => bulkApi.upload(file),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: productKeys.lists() }) },
  })
}
```

### 8.9 Dashboard (Dark Mode)

**الملف:** `frontend/src/pages/dashboard/DashboardPage.tsx`

```tsx
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import api from '@/lib/axios'
import { Package, Upload, CheckCircle, XCircle, Clock, RefreshCw, ShoppingCart } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  const navigate = useNavigate()

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const [productsRes, listingsRes] = await Promise.all([
        api.get('/products?page_size=1'),
        api.get('/listings'),
      ])
      const listings = listingsRes.data || []
      return {
        total_products: productsRes.data.total || 0,
        total_listings: listings.length,
        published: listings.filter((l: any) => l.status === 'success').length,
        queued: listings.filter((l: any) => l.status === 'queued').length,
        failed: listings.filter((l: any) => l.status === 'failed').length,
        processing: listings.filter((l: any) => l.status === 'processing' || l.status === 'submitted').length,
      }
    },
    refetchInterval: 10000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">لوحة التحكم</h1>
          <p className="text-gray-400 text-sm mt-1">نظرة عامة على متجرك</p>
        </div>
        <button onClick={() => navigate('/products/create')}
          className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-all">
          <Package className="w-4 h-4" /> إضافة منتج
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="إجمالي المنتجات" value={stats?.total_products || 0} icon={<ShoppingCart className="w-5 h-5" />} color="blue" />
        <StatCard title="في الانتظار" value={stats?.queued || 0} icon={<Clock className="w-5 h-5" />} color="yellow" />
        <StatCard title="تم الرفع" value={stats?.published || 0} icon={<CheckCircle className="w-5 h-5" />} color="green" />
        <StatCard title="فشل الرفع" value={stats?.failed || 0} icon={<XCircle className="w-5 h-5" />} color="red" />
      </div>

      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">إجراءات سريعة</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickAction icon={<Package className="w-6 h-6" />} title="إضافة منتج جديد" description="إضافة منتج فردي للمكتبة" onClick={() => navigate('/products/create')} />
          <QuickAction icon={<Upload className="w-6 h-6" />} title="رفع جماعي" description="رفع منتجات من ملف Excel/CSV" onClick={() => navigate('/products/create?bulk=true')} />
          <QuickAction icon={<RefreshCw className="w-6 h-6" />} title="مزامنة من Amazon" description="سحب المنتجات الحالية من Amazon" onClick={async () => {
            try { await api.post('/sync/sync'); toast.success('تمت المزامنة') } catch { toast.error('فشل المزامنة') }
          }} />
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: React.ReactNode; color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-500/10 text-blue-500',
    yellow: 'bg-yellow-500/10 text-yellow-500',
    green: 'bg-green-500/10 text-green-500',
    red: 'bg-red-500/10 text-red-500',
  }
  return (
    <div className="bg-[#12121a] rounded-xl border border-gray-800/50 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{title}</span>
        <div className={`p-2 rounded-lg ${colors[color]}`}>{icon}</div>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  )
}

function QuickAction({ icon, title, description, onClick }: { icon: React.ReactNode; title: string; description: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="bg-[#1a1a2e] hover:bg-[#22223a] border border-gray-700/50 rounded-xl p-4 text-right transition-colors group">
      <div className="text-orange-500 mb-3 group-hover:scale-110 transition-transform">{icon}</div>
      <h3 className="text-white font-medium mb-1">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </button>
  )
}
```

### 8.10 Sidebar (حذف Logout)

**الملف:** `frontend/src/components/layout/Sidebar.tsx`

حذف زر Logout فقط. الباقي يبقى زي ما هو.

---

## 9. المرحلة 6: Desktop Wrapper (PyWebView)

### المدة: 1-2 ساعة

### 9.1 Desktop App Launcher

**الملف:** `backend/app/desktop.py`

```python
"""
Desktop App Launcher
Starts FastAPI backend + PyWebView frontend window
"""
import os
import sys
import threading
import time
import asyncio
from pathlib import Path
import uvicorn
import webview
from loguru import logger

# ============================================================
# Path Resolution for PyInstaller
# ============================================================
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    BASE_DIR = Path(sys._MEIPASS)
    APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
else:
    # Development mode
    BASE_DIR = Path(__file__).parent.parent
    APP_DATA_DIR = BASE_DIR / "app_data"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Logging Setup
# ============================================================
log_file = APP_DATA_DIR / "crazy_lister.log"
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <6}</level> | <level>{message}</level>"
)
logger.add(
    str(log_file),
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <6} | {message}"
)

# ============================================================
# Backend Server
# ============================================================
def start_backend():
    """Start FastAPI in background thread"""
    logger.info("Starting FastAPI backend on port 8765...")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="warning",
    )

# ============================================================
# Frontend Path
# ============================================================
def get_frontend_path() -> str:
    """Get the path to the built frontend"""
    if getattr(sys, 'frozen', False):
        return str(BASE_DIR / "frontend" / "dist" / "index.html")
    else:
        return str(BASE_DIR.parent / "frontend" / "dist" / "index.html")

# ============================================================
# App Launcher
# ============================================================
def create_app():
    """Create and run the desktop application"""
    logger.info("=" * 50)
    logger.info("  Crazy Lister v3.0 — Desktop App")
    logger.info("=" * 50)

    # Verify frontend exists
    frontend_path = get_frontend_path()
    if not os.path.exists(frontend_path):
        logger.error(f"Frontend not found: {frontend_path}")
        logger.error("Run 'npm run build' in frontend/ first!")
        input("Press Enter to exit...")
        sys.exit(1)

    logger.info(f"Frontend: {frontend_path}")
    logger.info(f"Data: {APP_DATA_DIR}")

    # Start backend
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for backend
    time.sleep(2)

    # Create PyWebView window
    window = webview.create_window(
        title="Crazy Lister v3.0",
        url=f"file:///{os.path.abspath(frontend_path).replace(chr(92), '/')}",
        width=1280,
        height=850,
        min_size=(900, 600),
        resizable=True,
        background_color="#0a0a0f",
    )

    logger.info("Desktop window created. Starting UI...")
    webview.start()

if __name__ == "__main__":
    create_app()
```

### 9.2 تحديث `backend/app/main.py`

```python
# إضافة Task Manager startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Crazy Lister v3.0...")
    init_db()

    # Start task manager
    import asyncio
    from app.tasks.task_manager import task_manager
    asyncio.create_task(task_manager.start())
    logger.info("Task manager started")
```

---

## 10. المرحلة 7: Build & Packaging (.exe)

### المدة: 1-2 ساعة

### 10.1 PyInstaller Spec File

**الملف:** `crazy_lister.spec`

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/app/desktop.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.logging',
        'loguru',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'pydantic',
        'pydantic_settings',
        'webview',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CrazyLister',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Optional: add app icon
)
```

### 10.2 Build Script

**الملف:** `build.py`

```python
"""
Build Script for Crazy Lister v3.0
Builds the .exe file using PyInstaller
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def run(cmd, cwd=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        sys.exit(1)
    return result

def main():
    project_root = Path(__file__).parent

    # Step 1: Build Frontend
    print_header("Step 1: Building Frontend (React/Vite)")
    frontend_dir = project_root / "frontend"
    run("npm install", cwd=frontend_dir)
    run("npm run build", cwd=frontend_dir)

    # Verify build
    dist_dir = frontend_dir / "dist"
    if not (dist_dir / "index.html").exists():
        print("ERROR: Frontend build failed!")
        sys.exit(1)
    print("✅ Frontend built successfully")

    # Step 2: Install Python Dependencies
    print_header("Step 2: Installing Python Dependencies")
    backend_dir = project_root / "backend"
    run("pip install -r requirements.txt", cwd=backend_dir)

    # Step 3: Build .exe with PyInstaller
    print_header("Step 3: Building .exe with PyInstaller")
    run("pyinstaller crazy_lister.spec --clean")

    # Step 4: Verify output
    print_header("Step 4: Verifying Output")
    exe_path = project_root / "dist" / "CrazyLister.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ Build successful!")
        print(f"   File: {exe_path}")
        print(f"   Size: {size_mb:.1f} MB")
    else:
        print("ERROR: .exe not found!")
        sys.exit(1)

    print_header("Build Complete!")
    print(f"Your app is ready at: {exe_path}")
    print("\nTo distribute: zip the dist/ folder or create an installer")

if __name__ == "__main__":
    main()
```

### 10.3 Build Commands

```powershell
# Development mode (test the app)
cd backend
python -m app.desktop

# Build the .exe
cd c:\Users\Dell\Desktop\learn\amazon
python build.py

# The .exe will be at: dist/CrazyLister.exe
```

### 10.4 حجم الـ .exe المتوقع

| المكون | الحجم التقريبي |
|--------|----------------|
| Python Runtime | ~30 MB |
| FastAPI + Dependencies | ~20 MB |
| PyWebView (WebView2) | ~5 MB (يستخدم المدمج في Windows) |
| Frontend (built) | ~2 MB |
| **الإجمالي** | **~60-80 MB** |

---

## 11. المرحلة 8: Amazon Integration + Local Testing

### المدة: 1-2 ساعة

### 11.1 Amazon API Service (تحديث بسيط)

**الملف:** `backend/app/services/amazon_api.py`

التأكد إن الكود بيشتغل بدون Docker:

```python
# التأكد من أن AmazonSPAPIClient بيشتغل محلياً
# (بدون أي Docker-specific config)

class AmazonSPAPIClient:
    def __init__(self, client_id, client_secret, refresh_token, seller_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.seller_id = seller_id

    async def get_account_info(self) -> dict:
        """Test connection to Amazon"""
        # Use python-amazon-sp-api library
        from sp_api.api import Sellers
        from sp_api.base import Credentials, Marketplaces

        # For local testing with mock:
        if os.getenv("USE_AMAZON_MOCK") == "true":
            return {"seller_id": self.seller_id, "mock": True}

        # Real API call
        # ...
```

### 11.2 Local Testing Checklist

```powershell
# 1. Build frontend
cd frontend && npm run build

# 2. Run desktop app (development mode)
cd backend && python -m app.desktop

# 3. Test Amazon Connect
# Open the app, go to /connect page, enter test credentials

# 4. Test product CRUD
# Add products, verify they appear in the list

# 5. Test bulk upload
# Upload a CSV file with test products

# 6. Test Amazon sync
# Click "Sync from Amazon" button

# 7. Test listing submission
# Submit a product listing, check task status

# 8. Build .exe
cd .. && python build.py

# 9. Test .exe
.\dist\CrazyLister.exe
```

---

## 12. المرحلة 9: Desktop Packaging & Delivery 🆕

> ⚠️ **هذه المرحلة هي اللي بتحوّل الكود من "موقع ويب" إلى "برنامج سطح مكتب احترافي".**  
> تشمل: دمج السيرفر + الواجهة + الأيقونة + معالجة الإغلاق + PyInstaller build.

### المدة: 1-2 ساعة

---

### 12.1 ملف Launcher الرئيسي (نقطة الدخول الوحيدة)

**الملف:** `backend/app/launcher.py`

هذا هو **أهم ملف** في التطبيق كله — هو اللي العميل بيدبل كليك عليه:

```python
"""
Crazy Lister v3.0 — Desktop Launcher
Entry point for the standalone Windows desktop application.

This module:
1. Starts FastAPI backend on a background thread
2. Waits for the server to be ready
3. Opens PyWebView window with the React frontend
4. Handles graceful shutdown when the window is closed
"""
import os
import sys
import time
import signal
import threading
import asyncio
import socket
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

import uvicorn
import webview
from loguru import logger

# ============================================================
# 1. PATH RESOLUTION (PyInstaller compatible)
# ============================================================

if getattr(sys, 'frozen', False):
    # Running as compiled .exe — files are in _MEIPASS
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Development mode
    BASE_DIR = Path(__file__).parent.parent

# ============================================================
# 2. APPDATA PATHS (No Admin permissions needed)
# ============================================================

APP_DATA_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = APP_DATA_DIR / "uploads"
EXPORT_DIR = APP_DATA_DIR / "exports"
LOG_FILE = APP_DATA_DIR / "crazy_lister.log"

for d in [UPLOAD_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Set environment variables for the app to use
os.environ["APP_DATA_DIR"] = str(APP_DATA_DIR)
os.environ["UPLOAD_DIR"] = str(UPLOAD_DIR)
os.environ["EXPORT_DIR"] = str(EXPORT_DIR)

# ============================================================
# 3. LOGGING SETUP
# ============================================================

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <6}</level> | <level>{message}</level>"
)
logger.add(
    str(LOG_FILE),
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <6} | {message}"
)

# ============================================================
# 4. BACKEND SERVER MANAGEMENT
# ============================================================

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8765
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

_server_thread = None
_server_started = False
_shutdown_event = threading.Event()


def _run_server():
    """Run FastAPI server in background thread"""
    global _server_started

    # Set up database before starting server
    import app.database as db_module
    db_module.APP_DATA_DIR = APP_DATA_DIR
    db_module.DATABASE_URL = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"

    logger.info(f"Starting FastAPI backend on {BACKEND_URL}...")

    uvicorn.run(
        "app.main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        log_level="warning",
    )


def start_backend():
    """Start the backend server in a daemon thread"""
    global _server_thread

    _server_thread = threading.Thread(target=_run_server, daemon=True, name="BackendServer")
    _server_thread.start()
    logger.info("Backend server thread started")


def wait_for_server(timeout: int = 15) -> bool:
    """
    Wait for the backend server to be ready.
    Polls the /health endpoint until it responds.
    """
    logger.info(f"Waiting for backend server (timeout: {timeout}s)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = urlopen(f"{BACKEND_URL}/health", timeout=1)
            if response.status == 200:
                logger.info("✅ Backend server is ready!")
                return True
        except (URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(0.3)

    logger.error("❌ Backend server failed to start within timeout")
    return False


def stop_backend():
    """Signal the backend server to stop"""
    logger.info("Stopping backend server...")
    _shutdown_event.set()


# ============================================================
# 5. FRONTEND PATH
# ============================================================

def get_frontend_path() -> str:
    """Get the path to the built frontend index.html"""
    if getattr(sys, 'frozen', False):
        # .exe mode: frontend is bundled in _MEIPASS
        return str(BASE_DIR / "frontend" / "dist" / "index.html")
    else:
        # Dev mode: frontend is in project root
        return str(BASE_DIR.parent / "frontend" / "dist" / "index.html")


# ============================================================
# 6. GRACEFUL SHUTDOWN
# ============================================================

def on_closing():
    """
    Called when the user closes the window.
    Ensures all resources are properly released.
    """
    logger.info("Window closing — initiating graceful shutdown...")

    # Stop task manager
    try:
        from app.tasks.task_manager import task_manager
        task_manager.stop()
        logger.info("Task manager stopped")
    except Exception as e:
        logger.warning(f"Error stopping task manager: {e}")

    # Stop backend
    stop_backend()

    # Close database connections
    try:
        from app.database import SessionLocal, engine
        SessionLocal().close()
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")

    logger.info("✅ Graceful shutdown complete")
    return True  # Allow window to close


# ============================================================
# 7. MAIN APPLICATION
# ============================================================

def create_app():
    """
    Create and run the Crazy Lister desktop application.

    Flow:
    1. Verify frontend files exist
    2. Initialize database
    3. Start backend in background thread
    4. Wait for server readiness
    5. Open PyWebView window
    6. Start event loop
    """
    logger.info("=" * 60)
    logger.info("  🚀 Crazy Lister v3.0 — Desktop Application")
    logger.info("=" * 60)
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Data directory: {APP_DATA_DIR}")

    # ---- Step 1: Verify frontend ----
    frontend_path = get_frontend_path()
    if not os.path.exists(frontend_path):
        logger.error(f"❌ Frontend not found: {frontend_path}")
        logger.error("Run 'npm run build' in frontend/ directory first!")
        input("\nPress Enter to exit...")
        sys.exit(1)
    logger.info(f"✅ Frontend found: {frontend_path}")

    # ---- Step 2: Initialize database ----
    logger.info("Initializing database...")
    import app.database as db_module
    db_module.APP_DATA_DIR = APP_DATA_DIR
    db_module.DATABASE_URL = f"sqlite:///{APP_DATA_DIR}/crazy_lister.db"
    db_module.init_db()
    logger.info(f"✅ Database initialized: {APP_DATA_DIR}/crazy_lister.db")

    # ---- Step 3: Start backend ----
    start_backend()

    # ---- Step 4: Wait for server ----
    if not wait_for_server(timeout=15):
        logger.error("❌ Failed to start backend server. Check logs for details.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # ---- Step 5: Create PyWebView window ----
    logger.info("Creating application window...")

    # Convert path for Windows (forward slashes for file:// protocol)
    file_url = f"file:///{os.path.abspath(frontend_path).replace(chr(92), '/')}"

    window = webview.create_window(
        title="Crazy Lister v3.0",
        url=file_url,
        width=1280,
        height=850,
        min_size=(960, 640),
        resizable=True,
        fullscreen=False,
        easy_drag=True,
        background_color="#0a0a0f",
        on_closing=on_closing,
    )

    # Set window icon (if available)
    icon_path = BASE_DIR / "assets" / "icon.ico"
    if icon_path.exists():
        try:
            window.load_html("")  # Required to set icon in some versions
            # Note: pywebview icon setting varies by version
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")

    # ---- Step 6: Start event loop ----
    logger.info("🎉 Application ready! Starting UI...")
    webview.start()


# ============================================================
# 8. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        create_app()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
```

---

### 12.2 تحديث `backend/app/main.py` (FastAPI App)

**التعديلات المطلوبة:**

```python
# إضافة هذول في startup_event

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Starting Crazy Lister v3.0...")

    # Initialize database
    from app.database import init_db
    init_db()
    logger.info("Database initialized")

    # Start asyncio task manager
    import asyncio
    from app.tasks.task_manager import task_manager
    asyncio.create_task(task_manager.start())
    logger.info("Task manager started")

    # Set APPDATA paths from environment (if set by launcher)
    import os
    app_data = os.getenv("APP_DATA_DIR")
    if app_data:
        logger.info(f"Running from: {app_data}")
```

---

### 12.3 إعداد الأيقونة (Icon Setup)

**الملف:** `assets/icon.ico`

1. **صمّم أيقونة** بمقاسات: 16x16, 32x32, 48x48, 256x256
2. **احفظها كـ `.ico`** في مجلد `assets/`

**أدوات مجانية لتصميم الأيقونة:**
- [ICO Convert](https://icoconvert.com/) — حوّل PNG لـ ICO
- [Favicon.io](https://favicon.io/) — مولّد أيقونات

**الأيقونة هتظهر في:**
- ✅ شريط المهام (Taskbar)
- ✅ قائمة ابدأ (Start Menu)
- ✅ سطح المكتب (Desktop shortcut)
- ✅ Alt+Tab switcher

---

### 12.4 PyInstaller Spec File (النهائي)

**الملف:** `crazy_lister.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Crazy Lister v3.0
Builds a single .exe file with bundled frontend
"""

block_cipher = None

# ============================================================
# Analysis
# ============================================================

a = Analysis(
    ['backend/app/launcher.py'],     # Entry point
    pathex=['backend'],               # Additional search paths
    binaries=[],
    datas=[
        # Bundle the built frontend
        ('frontend/dist', 'frontend/dist'),
        # Bundle icon (optional)
        ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        # Uvicorn (FastAPI server)
        'uvicorn',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.logging',
        # FastAPI
        'fastapi',
        'fastapi.routing',
        'starlette',
        'starlette.routing',
        # Database
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.sqlite.pysqlite',
        # Pydantic
        'pydantic',
        'pydantic_settings',
        'pydantic.fields',
        # PyWebView
        'webview',
        'webview.platforms.winforms',
        # Amazon SP-API
        'sp_api',
        'sp_api.api',
        'sp_api.base',
        'boto3',
        'botocore',
        # Utilities
        'loguru',
        'loguru._defaults',
        'pandas',
        'openpyxl',
        'dateutil',
        'dateutil.parser',
        'dateutil.tz',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Remove unnecessary packages to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy',
        'jinja2',
        'IPython',
        'setuptools',
        'pip',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================
# PYZ (Python bytecode archive)
# ============================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================
# EXE (Final executable)
# ============================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],  # name in the list above means no separate .exe name override
    name='CrazyLister',              # Output filename (without .exe)
    debug=False,                     # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,                     # Don't strip symbols (needed for debugging)
    upx=True,                        # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,             # Use system temp dir
    console=False,                   # NO console window (GUI mode)
    disable_windowed_traceback=False,
    target_arch=None,                # Auto-detect
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',          # Application icon
)
```

---

### 12.5 Build Script (النهائي)

**الملف:** `build.py`

```python
"""
Build Script for Crazy Lister v3.0
====================================
Builds the standalone Windows .exe file.

Usage:
    python build.py

Requirements:
    - Node.js 18+ (for frontend build)
    - Python 3.11+ (for backend)
    - All dependencies installed (pip install -r backend/requirements.txt)
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Colors for console output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"  {text}")
    print(f"{BOLD}{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text):
    print(f"{RED}❌ {text}{RESET}")


def run(cmd, cwd=None, check=True):
    """Run a shell command"""
    print(f"  $ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print_error(f"Command failed: {cmd}")
        if result.stderr:
            print(f"  Error: {result.stderr[:500]}")
        if check:
            sys.exit(1)
    return result


def check_requirements():
    """Check that all requirements are met"""
    print_header("Step 0: Checking Requirements")

    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error(f"Python 3.11+ required (found {version.major}.{version.minor})")
        sys.exit(1)
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")

    # Check Node.js
    try:
        result = run("node --version", check=False)
        print_success(f"Node.js {result.stdout.strip()}")
    except:
        print_error("Node.js not found. Install from https://nodejs.org/")
        sys.exit(1)

    # Check npm
    try:
        result = run("npm --version", check=False)
        print_success(f"npm {result.stdout.strip()}")
    except:
        print_error("npm not found")
        sys.exit(1)

    # Check PyInstaller
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print_error("PyInstaller not installed. Run: pip install pyinstaller")
        sys.exit(1)

    # Check pywebview
    try:
        import webview
        print_success(f"pywebview {webview.__version__}")
    except ImportError:
        print_error("pywebview not installed. Run: pip install pywebview")
        sys.exit(1)


def build_frontend():
    """Build the React frontend"""
    print_header("Step 1: Building Frontend (React/Vite)")

    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        sys.exit(1)

    # Install dependencies
    print("  Installing frontend dependencies...")
    run("npm install", cwd=frontend_dir)

    # Build
    print("  Building frontend...")
    run("npm run build", cwd=frontend_dir)

    # Verify
    dist_dir = frontend_dir / "dist"
    index_html = dist_dir / "index.html"

    if not index_html.exists():
        print_error("Frontend build failed — index.html not found")
        sys.exit(1)

    # Count files
    file_count = sum(1 for _ in dist_dir.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
    size_mb = total_size / (1024 * 1024)

    print_success(f"Frontend built: {file_count} files, {size_mb:.1f} MB")


def build_exe():
    """Build the .exe with PyInstaller"""
    print_header("Step 2: Building .exe (PyInstaller)")

    project_root = Path(__file__).parent
    spec_file = project_root / "crazy_lister.spec"

    if not spec_file.exists():
        print_error(f"Spec file not found: {spec_file}")
        sys.exit(1)

    # Clean previous build
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Run PyInstaller
    print("  Running PyInstaller...")
    run(f"pyinstaller --clean {spec_file}")

    # Verify output
    exe_path = dist_dir / "CrazyLister.exe"
    if not exe_path.exists():
        print_error("Build failed — .exe not found")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print_success(f"Build successful: {exe_path.name} ({size_mb:.1f} MB)")

    # Check for warnings
    warn_file = dist_dir.parent / "build" / "warn-CrazyLister.txt"
    if warn_file.exists():
        print_warning("PyInstaller generated warnings (check build/warn-CrazyLister.txt)")


def create_release():
    """Create a release package"""
    print_header("Step 3: Creating Release Package")

    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    exe_path = dist_dir / "CrazyLister.exe"

    # Create release folder
    version = "3.0.0"
    release_name = f"CrazyLister-v{version}"
    release_dir = project_root / "releases" / release_name
    release_dir.mkdir(parents=True, exist_ok=True)

    # Copy .exe
    shutil.copy(exe_path, release_dir / f"{release_name}.exe")

    # Create README
    readme = release_dir / "README.txt"
    readme.write_text(f"""
===============================================
  Crazy Lister v{version} — تعليمات الاستخدام
===============================================

1. المتطلبات:
   - Windows 10 أو أحدث
   - اتصال بالإنترنت (للربط مع Amazon)
   - حساب Amazon Seller Central

2. التشغيل:
   - دبل كليك على {release_name}.exe
   - انتظر 2-3 ثواني حتى يفتح البرنامج

3. الإعداد الأولي:
   - أدخل بيانات Amazon (Client ID, Secret, Refresh Token, Seller ID)
   - اضغط "تحقق من الاتصال"

4. أين يتم حفظ البيانات؟
   - %APPDATA%\\CrazyLister\\

5. الدعم:
   - اللوجات: %APPDATA%\\CrazyLister\\crazy_lister.log
   - تاريخ البناء: {datetime.now().strftime('%Y-%m-%d')}
""")

    print_success(f"Release created: {release_dir}")

    # Show final info
    release_size = sum(f.stat().st_size for f in release_dir.rglob("*") if f.is_file())
    print(f"\n  📦 Release size: {release_size / (1024*1024):.1f} MB")
    print(f"  📁 Location: {release_dir}")
    print(f"  📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


def main():
    print(f"\n{BOLD}🚀 Crazy Lister v3.0 — Build Script{RESET}\n")

    check_requirements()
    build_frontend()
    build_exe()
    create_release()

    print_header("Build Complete!")
    print(f"{GREEN}  🎉 Your app is ready!{RESET}\n")


if __name__ == "__main__":
    main()
```

---

### 12.6 أمر البناء النهائي

```powershell
# من مجلد المشروع الرئيسي:
python build.py
```

**النتيجة:**
```
releases/
└── CrazyLister-v3.0.0/
    ├── CrazyLister-v3.0.0.exe    ← الملف التنفيذي (~70 MB)
    └── README.txt                 ← تعليمات الاستخدام
```

---

### 12.7 Checklist: قبل الـ Build

| # | التحقق | الحالة |
|---|--------|--------|
| 1 | `frontend/` فيه كل الملفات | ⬜ |
| 2 | `npm run build` يشتغل بدون أخطاء | ⬜ |
| 3 | `backend/app/launcher.py` موجود | ⬜ |
| 4 | `backend/requirements.txt` محدّث | ⬜ |
| 5 | `crazy_lister.spec` موجود | ⬜ |
| 6 | `build.py` موجود | ⬜ |
| 7 | `assets/icon.ico` موجود (اختياري) | ⬜ |
| 8 | `pip install -r backend/requirements.txt` | ⬜ |
| 9 | Python 3.11+ مثبت | ⬜ |
| 10 | Node.js 18+ مثبت | ⬜ |

---

### 12.8 استكشاف الأخطاء (Troubleshooting)

| المشكلة | السبب | الحل |
|---------|-------|------|
| `ModuleNotFoundError: uvicorn` | PyInstaller مش لاقي Uvicorn | أضف `'uvicorn'` في `hiddenimports` |
| Frontend مش بيظهر | مسار `frontend/dist` غلط | تأكد إن `npm run build` اشتغل |
| شاشة CMD سوداء بتظهر | `console=True` في الـ spec | غيّرها لـ `console=False` |
| الـ .exe حجمه كبير | UPX مش شغال | تأكد إن UPX مثبت: `pip install pyinstaller[encryption]` |
| البرنامج بيقفل فوراً | Backend مش بيشتغل | شوف اللوجات في `%APPDATA%/CrazyLister/crazy_lister.log` |
| قاعدة البيانات مش بتتحفظ | مسار غلط | تأكد إن `APPDATA` environment variable موجود |

---

## 13. خطة التوزيع للعميل

### 📦 طريقة التوزيع

هناك **طريقتان** لتوزيع البرنامج:

#### الطريقة 1: ملف .exe واحد (موصى بها)

```
CrazyLister-v3.0.zip
├── CrazyLister.exe          # الملف التنفيذي (~70 MB)
└── README.txt               # تعليمات الاستخدام
```

**المميزات:**
- ✅ عميل واحد فقط — ملف واحد
- ✅ لا يحتاج تثبيت
- ✅ يعمل فوراً بالدبل كليك

**العيوب:**
- ⚠️ الحجم كبير نسبياً (~70 MB)

#### الطريقة 2: مجلد مضغوط (أخف)

```
CrazyLister-v3.0.zip
├── CrazyLister.exe
├── _internal/               # مجلد dependencies
│   ├── python311.dll
│   ├── site-packages/
│   └── ...
└── README.txt
```

**المميزات:**
- ✅ أسرع في البناء
- ✅ أسهل في التحديث

**العيوب:**
- ⚠️ العميل محتاج يشيل كل المجلد (مش ملف واحد)

### 🎯 الطريقة الموصى بها: **ملف واحد**

باستخدام PyInstaller مع `--onefile` (المفعّل في الـ spec file):

```powershell
# النتيجة: ملف واحد
dist/CrazyLister.exe
```

### 📋 تعليمات للعميل (README.txt)

```
===========================================
  Crazy Lister v3.0 — تعليمات الاستخدام
===========================================

1. المتطلبات:
   - Windows 10 أو أحدث
   - اتصال بالإنترنت (للربط مع Amazon)
   - حساب Amazon Seller Central

2. التشغيل:
   - دبل كليك على CrazyLister.exe
   - انتظر ثواني حتى يفتح البرنامج

3. الإعداد الأولي:
   - افتح البرنامج
   - أدخل بيانات Amazon الخاصة بك:
     * Client ID
     * Client Secret
     * Refresh Token
     * Seller ID
   - اضغط "تحقق من الاتصال"

4. أين يتم حفظ البيانات؟
   - قاعدة البيانات: %APPDATA%\CrazyLister\crazy_lister.db
   - اللوجات: %APPDATA%\CrazyLister\crazy_lister.log
   - الملفات المرفوعة: %APPDATA%\CrazyLister\uploads\

5. الدعم:
   - في حالة وجود مشكلة، راجع ملف اللوج:
     %APPDATA%\CrazyLister\crazy_lister.log
```

### 🔄 كيفية التحديث

```
1. العميل يحمل النسخة الجديدة (CrazyLister-v3.1.exe)
2. يستبدل الملف القديم بالجديد
3. البيانات محفوظة في AppData — لن تضيع
```

---

## 13. خطة التحقق (Verification)

### ✅ Checklist نهائي

| # | الاختبار | الحالة |
|---|----------|--------|
| 1 | البرنامج يفتح بالدبل كليك على .exe | ⬜ |
| 2 | نافذة PyWebView تظهر بشكل صحيح | ⬜ |
| 3 | صفحة Amazon Connect تظهر أولاً | ⬜ |
| 4 | إدخال بيانات Amazon وحفظها | ⬜ |
| 5 | زر "تحقق من الاتصال" يرجع success | ⬜ |
| 6 | بعد الاتصال، يتم التوجيه لـ Dashboard | ⬜ |
| 7 | Dashboard يعرض الإحصائيات | ⬜ |
| 8 | إضافة منتج جديد تنجح | ⬜ |
| 9 | قائمة المنتجات تعرض المنتجات | ⬜ |
| 10 | حذف منتج ينجح | ⬜ |
| 11 | رفع ملف CSV/Excel ينجح | ⬜ |
| 12 | المزامنة من Amazon تنجح | ⬜ |
| 13 | إرسال Listing لـ Amazon ينجح (async) | ⬜ |
| 14 | متابعة حالة Listing (queued → processing → success) | ⬜ |
| 15 | إعادة محاولة Listing فاشل تنجح | ⬜ |
| 16 | Settings page تعرض حالة الاتصال | ⬜ |
| 17 | قاعدة البيانات تتحفظ في %APPDATA% | ⬜ |
| 18 | ملف اللوج يتحفظ في %APPDATA% | ⬜ |
| 19 | البرنامج يقفل بشكل نظيف | ⬜ |
| 20 | إعادة فتح البرنامج تحافظ على البيانات | ⬜ |
| 21 | Dark Mode يعمل بشكل صحيح | ⬜ |
| 22 | التصميم متجاوب (Responsive) | ⬜ |
| 23 | حجم الـ .exe معقول (< 100 MB) | ⬜ |
| 24 | لا يوجد أخطاء في Console | ⬜ |
| 25 | Amazon Sync يعمل بكفاءة | ⬜ |
| 26 | Bulk Upload يعمل بكفاءة | ⬜ |

### 🧪 اختبار Amazon Sync

```python
# اختبار محلي (Mock Mode)
# في backend/.env:
USE_AMAZON_MOCK=true

# النتيجة المتوقعة:
# - sync_products_from_amazon() يرجع منتجات وهمية
# - submit_listing() يرجع ASIN وهمي
```

### 📊 مراقبة الأداء (محلياً)

| Metric | Target | Tool |
|--------|--------|------|
| Startup Time | < 3 seconds | Stopwatch |
| API Response Time | < 200ms | Browser DevTools |
| Task Queue | < 5 pending | Task API (/tasks/) |
| DB Query Time | < 50ms | SQLite PRAGMA |
| Memory Usage | < 200 MB | Task Manager |
| .exe Size | < 100 MB | File Properties |

---

## 📦 ملخص الملفات النهائي

### 🗑️ سيتم حذفها (20+ ملف)
```
backend/app/api/auth/ (4 ملفات)
backend/app/seed.py
backend/app/tasks/celery_app.py
backend/app/middleware/ (2 ملفات)
backend/tests/
backend/static/
frontend/src/pages/auth/ (2 ملفات)
docker-compose.yml
frontend/nginx.conf
frontend/Dockerfile
backend/Dockerfile
```

### 📝 سيتم تعديلها (26 ملف)
انظر الجدول في القسم 3.

### 🆕 سيتم إنشاؤها (17 ملف)
```
backend/app/desktop.py
backend/app/api/amazon_connect/__init__.py
backend/app/api/amazon_connect/endpoints.py
backend/app/api/amazon_connect/schemas.py
backend/app/api/amazon_connect/service.py
backend/app/api/products_sync.py
backend/app/api/bulk_upload.py
backend/app/api/tasks.py
backend/app/tasks/task_manager.py
backend/app/tasks/listing_tasks.py (إعادة كتابة)
backend/app/tasks/feed_tasks.py
frontend/src/pages/amazon/AmazonConnectPage.tsx
frontend/src/contexts/AmazonConnectContext.tsx
frontend/src/components/common/StatsCard.tsx
build.py
crazy_lister.spec
```

---

## 🚀 الترتيب المقترح للتنفيذ

| اليوم | المهمة |
|-------|--------|
| **يوم 1** | المرحلة 1 + 2 (التنظيف + SQLite) |
| **يوم 2** | المرحلة 3 (إزالة Celery/Redis + Asyncio) |
| **يوم 3** | المرحلة 4 (Backend APIs) |
| **يوم 4** | المرحلة 5 (Frontend Dark Mode) |
| **يوم 5** | المرحلة 6 + 7 (PyWebView + PyInstaller) |
| **يوم 6** | المرحلة 8 (Amazon Integration + Testing) |
| **يوم 7** | التوزيع النهائي + التوثيق |

---

## 📞 الدعم والمتابعة

لو فيه أي مشكلة:
1. **اللوجات:** `%APPDATA%/CrazyLister/crazy_lister.log`
2. **قاعدة البيانات:** `%APPDATA%/CrazyLister/crazy_lister.db` (افتحها بـ DB Browser for SQLite)
3. **Test mode:** `USE_AMAZON_MOCK=true` في `.env`

---

> **ملاحظة:** كل الكود في الخطة جاهز للنسخ واللصق. التطبيق النهائي هيكون ملف `.exe` واحد يعمل على أي جهاز Windows 10+ بدون أي تثبيت أو إعداد.
