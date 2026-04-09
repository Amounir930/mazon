# 🚀 خطة تطوير فرونت-إند Crazy Lister v2.0

> **خطة شاملة ومفصلة لتحويل تطبيق سطح المكتب إلى منصة ويب احترافية**

**تاريخ الإنشاء:** 9 أبريل 2026  
**الإصدار:** 2.0.0  
**الحالة:** ✅ المرحلة 1 مكتملة - جاري التنفيذ

---

## 📋 فهرس الخطة

1. [الرؤية والأهداف](#1-الرؤية-والأهداف)
2. [تحليل الوضع الحالي](#2-تحليل-الوضع-الحالي)
3. [المكدس التقني الكامل](#3-المكدس-التقني-الكامل)
4. [هندسة المشروع التفصيلية](#4-هندسة-المشروع-التفصيلية)
5. [تصميم قاعدة بيانات الواجهة](#5-تصميم-قاعدة-بيانات-الواجهة)
6. [هندسة المكونات التفصيلية](#6-هندسة-المكونات-التفصيلية)
7. [تصميم الشاشات والصفحات](#7-تصميم-الشاشات-والصفحات)
8. [تكامل الـ API التفصيلي](#8-تكامل-ال-api-التفصيلي)
9. [إدارة الحالة State Management](#9-إدارة-الحالة-state-management)
10. [نظام التوثيق والأمان](#10-نظام-التوثيق-والأمان)
11. [المراحل التنفيذية الخمس](#11-المراحل-التنفيذية-الخمس)
12. [نظام الاختبارات](#12-نظام-الاختبارات)
13. [الأداء والتحسين](#13-الأداء-والتحسين)
14. [التوزيع والنشر](#14-التوزيع-والنشر)
15. [خطة الطوارئ](#15-خطة-الطوارئ)

---

## 1. الرؤية والأهداف

### الرؤية
> **"منصة ويب احترافية لإدارة ورفع المنتجات على أمازون بشكل آلي، تعمل على جميع الأجهزة، مع تجربة مستخدم سلسة وسريعة"**

### الأهداف الاستراتيجية

| الهدف | الوصف | الأولوية | المؤشر |
|-------|-------|----------|---------|
| **تجربة مستخدم حديثة** | واجهة جميلة، سريعة، سهلة | 🔴 P0 | CSAT > 4.5/5 |
| **دعم كل الأجهزة** | Desktop + Tablet + Mobile | 🔴 P0 | 100% Responsive |
| **عربي أولاً (RTL)** | دعم كامل للعربية | 🔴 P0 | RTL Native |
| **أداء عالي** | تحميل < 2 ثانية | 🔴 P0 | Lighthouse > 90 |
| **حالة实时** | WebSocket للمهام | 🟡 P1 | Real-time < 100ms |
| **نظام إشعارات** | Toast + WebSocket | 🟡 P1 | Delivery > 99% |
| **إمكانية الوصول** | WCAG 2.1 AA | 🟢 P2 | Score > 90 |
| **PWA** | Offline + Install | 🟢 P2 | Lighthouse PWA > 80 |

### الجمهور المستهدف

| الشريحة | الوصف | الاحتياجات |
|---------|-------|------------|
| **بائعون أفراد** | 1-3 حسابات أمازون | واجهة بسيطة، رفع سريع |
| **شركات صغيرة** | 3-10 حسابات | إدارة متعددة، تقارير |
| **وكلاء تسويق** | 10+ حسابات | لوحة تحكم، أذونات |

---

## 2. تحليل الوضع الحالي

### 2.1 الفرونت-إند القديم (Tkinter)

#### الهيكل الحالي

```
Crazy Lister.py (2184 سطر)
├── AmazonAutoListingBot (class رئيسي)
│   ├── __init__()                    # تهيئة الواجهة
│   ├── setup_ui()                    # بناء الواجهة
│   ├── setup_auto_login_tab()        # تبويب تسجيل الدخول
│   ├── setup_advanced_add_tab()      # تبويب إضافة المنتج
│   ├── setup_manage_tab()            # تبويب الإدارة
│   ├── setup_auto_listing_tab()      # تبويب الرفع الآلي
│   ├── setup_results_tab()           # تبويب النتائج
│   │
│   ├── auto_login_complete()         # تسجيل الدخول الآلي
│   ├── save_to_inventory()           # حفظ في المخزون
│   ├── add_to_queue()                # إضافة للطابور
│   ├── auto_list_now()               # رفع آلي مباشر
│   ├── upload_to_amazon()            # رفع لأمازون
│   ├── create_amazon_xml()           # إنشاء XML
│   │
│   └── run()                         # تشغيل التطبيق
│
├── تخزين البيانات
│   ├── amazon_bot_settings.json      # إعدادات المستخدم
│   └── amazon_inventory.json         # المخزون المحلي
│
└── التكامل مع أمازون
    ├── MWS API (منتهي الصلاحية)
    ├── OAuth2 Flow (غير مكتمل)
    └── OTP Handling (محاكاة)
```

#### الميزات الموجودة في الفرونت القديم

| الميزة | الوصف | التقييم | النقل للفرونت الجديد |
|--------|-------|---------|----------------------|
| **تسجيل دخول آلي** | إدخال البريد + كلمة + OTP | ⚠️ يحتاج تحديث | تحويل لـ OAuth2 |
| **إضافة منتج (5 تبويبات)** | بيانات أساسية، تسعير، صور، خصائص، إعلانات | ✅ ممتاز | نفس التبويبات بتصميم حديث |
| **إدارة المنتجات** | جدول + CRUD | ✅ جيد | DataTable + بحث + تصفية |
| **طابور الرفع** | قائمة الانتظار | ✅ جيد | Queue UI + حالة实时 |
| **نتائج حية** | إحصائيات + روابط | ✅ جيد | Charts + Real-time |
| **تصدير تقارير** | TXT فقط | ⚠️ محدود | CSV, PDF, Excel |
| **إعلانات متعددة** | نسخ متعددة من منتج | ✅ فريد | Multi-listing wizard |
| **واجهة عربية RTL** | كامل بالعربية | ✅ ممتاز | عربي + إنجليزي |

#### مشاكل الفرونت القديم

| المشكلة | التأثير | الحل في الفرونت الجديد |
|---------|---------|----------------------|
| **Desktop فقط** | لا يعمل على الموبايل | React Responsive |
| **لا توثيق** | بيانات في JSON | JWT + OAuth2 |
| **لا إشعارات** | لا يعرف حالة المهام | WebSocket + Toast |
| **لا مشاركة** | مستخدم واحد | Multi-tenant |
| **بطيء** | Tkinter ثقيل | React + Vite |
| **لا تصحيح** | صعب تتبع الأخطاء | Sentry + Console |
| **MWS منتهي** | API غير معتمد | SP-API v2 |

### 2.2 الباك-إند الحالي

| المكون | الحالة | التفاصيل |
|--------|--------|----------|
| **FastAPI** | ✅ يعمل | 28 ملف Python |
| **PostgreSQL** | ✅ يعمل | قاعدة بيانات إنتاجية |
| **Redis** | ✅ يعمل | Cache + Broker |
| **Celery** | ✅ يعمل | معالجة غير متزامنة |
| **SP-API** | ✅ جاهز | تكامل Amazon الرسمي |
| **Docker** | ✅ جاهز | 5 حاويات |

---

## 3. المكدس التقني الكامل

### 3.1 المكدس الأساسي

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Stack                            │
│                                                             │
│  Framework:    React 18 + TypeScript                       │
│  Build Tool:   Vite 6                                       │
│  Styling:      Tailwind CSS v4 + shadcn/ui                  │
│  Routing:      React Router v6                              │
│  State Mgmt:   Zustand (UI) + React Query (Server)          │
│  Forms:        React Hook Form 7 + Zod                      │
│  Notifications: React Hot Toast                             │
│  Charts:       Recharts                                     │
│  i18n:         i18next + react-i18next                      │
│  HTTP:         Axios                                        │
│  Icons:        Lucide React                                 │
│  Utils:        clsx + tailwind-merge                        │
│                                                             │
│  Testing:      Vitest + React Testing Library + Playwright   │
│  Linting:      ESLint + Prettier                            │
│  CI/CD:        GitHub Actions                               │
│  Hosting:      Nginx + Docker                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 لماذا هذه التقنيات؟

| التقنية | السبب | البديل | لماذا لم نختره |
|---------|-------|--------|---------------|
| **React 18** | مجتمع ضخم، مكونات جاهزة، TypeScript ممتاز | Vue 3 | React أكبر في العالم العربي |
| **TypeScript** | أمان النوع، تقليل الأخطاء 40%+ | JavaScript | خطر أخطاء Runtime |
| **Vite** | بناء في 200ms، HMR فوري | Webpack | Webpack بطيء |
| **Tailwind v4** | تصميم سريع، ملف صغير | CSS Modules | Tailwind أسرع 10x |
| **Zustand** | بسيط (1KB)، لا boilerplate | Redux | Redux معقد جداً |
| **React Query** | إدارة ذكية للبيانات | SWR | React Query أكثر اكتمالاً |
| **React Hook Form** | بدون re-render زائد | Formik | أبطأ 5x |
| **Zod** | متوافق مع RHF، Types آمنة | Yup | Zod أحدث وأسرع |
| **Recharts** | مرسوم بـ SVG، خفيف | Chart.js | Recharts أكثر مرونة |
| **Lucide** | أيقونات حديثة، شجرة قابلة | Font Awesome | Lucide أخف 80% |

### 3.3 إصدارات المكتبات

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "@tanstack/react-query": "^5.60.0",
    "zustand": "^5.0.0",
    "axios": "^1.7.0",
    "@hookform/resolvers": "^3.9.0",
    "react-hook-form": "^7.53.0",
    "zod": "^3.23.0",
    "i18next": "^24.0.0",
    "react-i18next": "^15.0.0",
    "i18next-browser-languagedetector": "^8.0.0",
    "recharts": "^2.13.0",
    "lucide-react": "^0.460.0",
    "react-hot-toast": "^2.4.1",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0",
    "@playwright/test": "^1.48.0",
    "eslint": "^9.14.0",
    "prettier": "^3.3.0"
  }
}
```

---

## 4. هندسة المشروع التفصيلية

### 4.1 هيكل المجلدات الكامل

```
frontend/
├── public/
│   ├── favicon.ico              # أيقونة المتصفح
│   ├── logo.svg                 # شعار التطبيق
│   ├── robots.txt               # SEO
│   └── manifest.json            # PWA Manifest
│
├── src/
│   ├── main.tsx                 # نقطة الدخول - تهيئة React + Providers
│   ├── App.tsx                  # المكون الرئيسي - QueryClient + Router
│   ├── router.tsx               # إعداد التوجيه + حماية المسارات
│   ├── index.css                # Tailwind + Custom Styles
│   │
│   ├── api/                     # طبقة الاتصال بالـ API
│   │   ├── client.ts            # عميل Axios المُهيأ
│   │   │   ├── Interceptors (Auth, Error, Retry)
│   │   │   ├── Base URL config
│   │   │   └── Timeout settings
│   │   │
│   │   ├── endpoints.ts         # جميع نقاط الـ API
│   │   │   ├── AUTH endpoints
│   │   │   ├── PRODUCTS endpoints
│   │   │   ├── LISTINGS endpoints
│   │   │   └── FEEDS endpoints
│   │   │
│   │   ├── types/               # أنواع TypeScript للـ API
│   │   │   ├── product.ts       # Product + ProductList + ProductCreate
│   │   │   ├── listing.ts       # Listing + ListingStatus
│   │   │   ├── seller.ts        # Seller + AuthResponse
│   │   │   ├── feed.ts          # FeedStatus + FeedResult
│   │   │   └── common.ts        # Pagination + ApiResponse
│   │   │
│   │   └── hooks/               # React Query Hooks
│   │       ├── useProducts.ts   # useProducts, useCreateProduct, useUpdateProduct
│   │       ├── useListings.ts   # useListings, useSubmitListing, useRetryListing
│   │       ├── useSellers.ts    # useSellers, useRegisterSeller
│   │       └── useFeeds.ts      # useFeedStatus, useFeedResults
│   │
│   ├── components/              # مكونات قابلة لإعادة الاستخدام
│   │   ├── ui/                  # مكونات shadcn/ui الأساسية
│   │   │   ├── button.tsx       # زر أساسي + variants
│   │   │   ├── input.tsx        # حقل إدخال + validation
│   │   │   ├── textarea.tsx     # حقل نص متعدد الأسطر
│   │   │   ├── select.tsx       # قائمة منسدلة
│   │   │   ├── dialog.tsx       # نافذة منبثقة
│   │   │   ├── table.tsx        # جدول بيانات
│   │   │   ├── tabs.tsx         # تبويبات
│   │   │   ├── badge.tsx        # شارة حالة
│   │   │   ├── card.tsx         # بطاقة محتوى
│   │   │   ├── alert.tsx        # تنبيه
│   │   │   ├── skeleton.tsx     # تحميل وهمي
│   │   │   ├── toast.tsx        # إشعار
│   │   │   ├── pagination.tsx   # ترقيم الصفحات
│   │   │   └── dropdown.tsx     # قائمة منسدلة متقدمة
│   │   │
│   │   ├── layout/              # مكونات التخطيط
│   │   │   ├── Layout.tsx       # التخطيط الرئيسي (Sidebar + Header + Content)
│   │   │   ├── Sidebar.tsx      # القائمة الجانبية
│   │   │   │   ├── Logo
│   │   │   │   ├── Navigation Links
│   │   │   │   ├── Active State
│   │   │   │   └── Logout Button
│   │   │   ├── Header.tsx       # الهيدر
│   │   │   │   ├── Page Title
│   │   │   │   ├── Search Bar
│   │   │   │   ├── Notifications Bell
│   │   │   │   └── User Menu
│   │   │   └── Footer.tsx       # الفوتر
│   │   │
│   │   ├── forms/               # مكونات النماذج
│   │   │   ├── ProductForm/     # نموذج المنتج الكامل
│   │   │   │   ├── BasicInfoTab.tsx       # المعلومات الأساسية
│   │   │   │   ├── PricingTab.tsx         # التسعير والمخزون
│   │   │   │   ├── MediaTab.tsx           # الصور والوسائط
│   │   │   │   ├── AdvancedTab.tsx        # الخصائص المتقدمة
│   │   │   │   ├── MultiListingTab.tsx    # الإعلانات المتعددة
│   │   │   │   ├── index.tsx              # المكون الرئيسي
│   │   │   │   └── validation.ts          # Zod Schema
│   │   │   ├── SellerForm.tsx             # نموذج تسجيل البائع
│   │   │   ├── LoginForm.tsx              # نموذج الدخول
│   │   │   └── ListingForm.tsx            # نموذج الرفع
│   │   │
│   │   ├── common/              # مكونات مشتركة
│   │   │   ├── Loading.tsx      # مؤشر تحميل
│   │   │   ├── ErrorBoundary.tsx # حد الخطأ
│   │   │   ├── EmptyState.tsx   # حالة فارغة
│   │   │   ├── Pagination.tsx   # ترقيم الصفحات
│   │   │   ├── StatusBadge.tsx  # شارة الحالة (منشور، فشل، قيد المعالجة)
│   │   │   ├── ConfirmDialog.tsx # نافذة تأكيد
│   │   │   ├── FileUpload.tsx   # رفع ملفات (Drag & Drop)
│   │   │   ├── ImageGallery.tsx # معرض الصور
│   │   │   └── SearchInput.tsx  # حقل بحث
│   │   │
│   │   ├── charts/              # رسوم بيانية
│   │   │   ├── ListingStats.tsx     # رسم الإرسالات
│   │   │   ├── InventoryChart.tsx   # رسم المخزون
│   │   │   ├── SuccessRateChart.tsx # رسم نسبة النجاح
│   │   │   └── TimeSeriesChart.tsx  # رسم زمني
│   │   │
│   │   └── feedback/            # مكونات التغذية الراجعة
│   │       ├── Toast.tsx        # إشعارات Toast
│   │       ├── Progress.tsx     # شريط التقدم
│   │       └── Spinner.tsx      # مؤشر دوران
│   │
│   ├── pages/                   # صفحات التطبيق
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx          # تسجيل الدخول
│   │   │   │   ├── Email + Password
│   │   │   │   ├── Amazon OAuth Button
│   │   │   │   └── Forgot Password Link
│   │   │   ├── RegisterPage.tsx       # التسجيل
│   │   │   │   ├── OAuth Flow
│   │   │   │   └── Manual Registration
│   │   │   └── OAuthCallback.tsx      # استقبال OAuth
│   │   │
│   │   ├── dashboard/
│   │   │   ├── DashboardPage.tsx      # لوحة التحكم
│   │   │   ├── StatsCards.tsx         # بطاقات الإحصائيات
│   │   │   ├── RecentListings.tsx     # آخر الإرسالات
│   │   │   ├── QuickActions.tsx       # إجراءات سريعة
│   │   │   └── ActivityFeed.tsx       # شريط النشاط
│   │   │
│   │   ├── products/
│   │   │   ├── ProductListPage.tsx    # قائمة المنتجات
│   │   │   │   ├── DataTable
│   │   │   │   ├── Search + Filter
│   │   │   │   └── Bulk Actions
│   │   │   ├── ProductCreatePage.tsx  # إضافة منتج
│   │   │   │   └── ProductForm (5 tabs)
│   │   │   ├── ProductEditPage.tsx    # تعديل منتج
│   │   │   │   └── ProductForm (pre-filled)
│   │   │   ├── ProductDetailPage.tsx  # تفاصيل منتج
│   │   │   │   ├── Product Info
│   │   │   │   ├── Listing History
│   │   │   │   └── Actions
│   │   │   └── BulkUploadPage.tsx     # رفع جماعي
│   │   │       ├── CSV Import
│   │   │       └── Progress Tracker
│   │   │
│   │   ├── listings/
│   │   │   ├── ListingQueuePage.tsx   # طابور الرفع
│   │   │   │   ├── Queue Table
│   │   │   │   ├── Status Badges
│   │   │   │   └── Actions (Retry, Cancel)
│   │   │   ├── ListingResultsPage.tsx # النتائج
│   │   │   │   ├── Results Table
│   │   │   │   ├── Amazon Links
│   │   │   │   └── Export Buttons
│   │   │   └── BulkSubmitPage.tsx     # رفع جماعي
│   │   │       ├── Product Selection
│   │   │       └── Progress Monitor
│   │   │
│   │   ├── sellers/
│   │   │   ├── SellerListPage.tsx     # قائمة البائعين
│   │   │   ├── SellerRegisterPage.tsx # تسجيل بائع
│   │   │   └── SellerDetailPage.tsx   # تفاصيل بائع
│   │   │
│   │   ├── reports/
│   │   │   ├── ReportsPage.tsx        # التقارير
│   │   │   ├── ExportPage.tsx         # التصدير
│   │   │   └── AnalyticsPage.tsx      # التحليلات
│   │   │
│   │   └── settings/
│   │       ├── SettingsPage.tsx       # الإعدادات
│   │       ├── ProfilePage.tsx        # الملف الشخصي
│   │       └── SecurityPage.tsx       # الأمان
│   │
│   ├── contexts/                # React Contexts
│   │   ├── AuthContext.tsx      # نظام التوثيق
│   │   │   ├── State: user, token, isAuthenticated
│   │   │   ├── Actions: login, logout, refreshToken
│   │   │   └── Persistence: localStorage
│   │   ├── ThemeContext.tsx     # الوضع الداكن/الفاتح
│   │   └── LocaleContext.tsx    # اللغة (عربي/إنجليزي)
│   │
│   ├── store/                   # Zustand Stores
│   │   ├── auth.ts              # حالة التوثيق
│   │   ├── ui.ts                # حالة الواجهة
│   │   │   ├── sidebarOpen
│   │   │   ├── theme
│   │   │   └── locale
│   │   ├── products.ts          # حالة المنتجات
│   │   ├── listings.ts          # حالة الإرسالات
│   │   └── index.ts             # تصدير موحد
│   │
│   ├── hooks/                   # Custom Hooks
│   │   ├── useAuth.ts           # استخدام التوثيق
│   │   ├── useWebSocket.ts      # WebSocket Real-time
│   │   ├── useToast.ts          # الإشعارات
│   │   ├── usePagination.ts     # ترقيم الصفحات
│   │   ├── useLocalStorage.ts   # التخزين المحلي
│   │   ├── useDebounce.ts       # Debounce للبحث
│   │   ├── useMediaQuery.ts     # استعلام الوسائط
│   │   └── useFileUpload.ts     # رفع الملفات
│   │
│   ├── utils/                   # أدوات مساعدة
│   │   ├── format.ts            # تنسيق الأرقام والتواريخ
│   │   ├── validation.ts        # Schemas مشتركة
│   │   ├── constants.ts         # ثوابت التطبيق
│   │   ├── helpers.ts           # دوال مساعدة
│   │   ├── fileUtils.ts         # معالجة الملفات
│   │   └── apiUtils.ts          # أدوات API
│   │
│   ├── lib/                     # مكتبات خارجية مهيأة
│   │   ├── axios.ts             # إعداد Axios
│   │   ├── queryClient.ts       # إعداد React Query
│   │   ├── i18n.ts              # إعداد i18next
│   │   └── utils.ts             # clsx + merge
│   │
│   ├── i18n/                    # الترجمة
│   │   ├── locales/
│   │   │   ├── ar.json          # الترجمة العربية
│   │   │   └── en.json          # الترجمة الإنجليزية
│   │   ├── config.ts            # إعداد i18next
│   │   └── index.ts             # تهيئة
│   │
│   ├── assets/                  # الصور والأيقونات
│   │   ├── images/
│   │   │   ├── logo.svg
│   │   │   ├── logo-dark.svg
│   │   │   └── placeholders/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── config/                  # ملفات الإعداد
│   │   ├── app.ts               # إعدادات التطبيق
│   │   ├── routes.ts            # تعريف المسارات
│   │   └── constants.ts         # الثوابت
│   │
│   └── types/                   # أنواع TypeScript
│       ├── api.ts               # أنواع API
│       ├── product.ts           # أنواع المنتج
│       ├── listing.ts           # أنواع الإرسال
│       ├── seller.ts            # أنواع البائع
│       ├── ui.ts                # أنواع الواجهة
│       └── index.ts             # تصدير موحد
│
├── tests/                       # الاختبارات
│   ├── unit/                    # اختبارات الوحدة
│   │   ├── components/
│   │   ├── hooks/
│   │   └── utils/
│   ├── integration/             # اختبارات التكامل
│   │   ├── api/
│   │   └── forms/
│   ├── e2e/                     # اختبارات النهاية للنهاية
│   │   ├── auth.spec.ts
│   │   ├── products.spec.ts
│   │   └── listings.spec.ts
│   └── setup.ts                 # إعداد الاختبارات
│
├── .env.example                 # متغيرات البيئة
├── .env.local                   # محلي (غير مُcommitted)
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── eslint.config.js
├── prettier.config.js
├── index.html
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## 5. تصميم قاعدة بيانات الواجهة

### 5.1 Local Storage Schema

```typescript
// ما يُخزَّن محلياً في المتصفح

interface LocalStorage {
  // التوثيق
  'auth-token': string          // JWT Token
  'auth-user': User             // بيانات المستخدم
  
  // الواجهة
  'ui-theme': 'light' | 'dark'  // الوضع
  'ui-locale': 'ar' | 'en'      // اللغة
  'ui-sidebar-open': boolean    // حالة القائمة
  
  // التخزين المؤقت
  'cache-products': Product[]   // آخر قائمة منتجات
  'cache-listings': Listing[]   // آخر إرسالات
  
  // الإعدادات
  'settings-seller-id': string  // معرف البائع الحالي
}
```

### 5.2 IndexedDB Schema (للملفات الكبيرة)

```typescript
// IndexedDB - للصور والملفات الكبيرة

interface IndexedDB {
  // الصور المؤقتة
  'product-images': {
    id: string                  // UUID
    productId: string           // معرف المنتج
    fileName: string            // اسم الملف
    data: Blob                  // بيانات الصورة
    createdAt: Date             // تاريخ الإنشاء
  }
  
  // طلبات غير متزامنة
  'pending-requests': {
    id: string                  // UUID
    endpoint: string            // نقطة الـ API
    method: string              // HTTP Method
    payload: any                // البيانات
    createdAt: Date             // تاريخ الإنشاء
    retries: number             // محاولات إعادة
  }
}
```

---

## 6. هندسة المكونات التفصيلية

### 6.1 شجرة المكونات

```
App
├── QueryClientProvider
│   └── BrowserRouter
│       └── AuthProvider
│           ├── Router (Protected Routes)
│           │   └── Layout
│           │       ├── Sidebar
│           │       │   ├── Logo
│           │       │   ├── NavLinks[]
│           │       │   └── LogoutButton
│           │       ├── Header
│           │       │   ├── PageTitle
│           │       │   ├── SearchBar
│           │       │   ├── NotificationsBell
│           │       │   └── UserMenu
│           │       └── MainContent (Outlet)
│           │           ├── DashboardPage
│           │           │   ├── StatsCards[]
│           │           │   ├── QuickActions[]
│           │           │   ├── RecentListings
│           │           │   └── ActivityFeed
│           │           ├── ProductListPage
│           │           │   ├── PageHeader
│           │           │   ├── SearchFilter
│           │           │   ├── ProductTable
│           │           │   │   ├── TableRow[]
│           │           │   │   │   ├── StatusBadge
│           │           │   │   │   └── ActionButtons
│           │           │   │   └── Pagination
│           │           │   └── BulkActions
│           │           ├── ProductCreatePage
│           │           │   ├── PageHeader
│           │           │   ├── ProductForm
│           │           │   │   ├── TabNavigation
│           │           │   │   ├── BasicInfoTab
│           │           │   │   ├── PricingTab
│           │           │   │   ├── MediaTab
│           │           │   │   ├── AdvancedTab
│           │           │   │   └── MultiListingTab
│           │           │   └── SaveButton
│           │           └── ...
│           └── Public Routes
│               ├── LoginPage
│               └── RegisterPage
│
└── ToastProvider (Notifications)
```

### 6.2 تفاصيل المكونات الرئيسية

#### ProductForm Component

```typescript
interface ProductFormProps {
  initialData?: Product          // للتعديل
  onSubmit: (data: ProductCreate) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

interface ProductFormData {
  // التبويب 1: المعلومات الأساسية
  sku: string                    // مطلوب، فريد
  parent_sku?: string            // للمنتجات الفرعية
  is_parent: boolean             // هل هو منتج أب؟
  name: string                   // مطلوب
  category: string               // مطلوب
  brand: string                  // مطلوب
  upc?: string                   // UPC/EAN/ISBN
  ean?: string
  description: string            // وصف المنتج
  bullet_points: string[]        // حتى 5 نقاط
  
  // التبويب 2: التسعير والمخزون
  price: number                  // مطلوب
  compare_price?: number         // السعر قبل الخصم
  cost?: number                  // التكلفة
  quantity: number               // مطلوب
  tax_id?: string                // رقم ضريبي
  weight?: number                // الوزن
  
  // التبويب 3: الصور
  main_image: string             // الصورة الرئيسية
  additional_images: string[]    // حتى 8 صور
  
  // التبويب 4: الخصائص المتقدمة
  dimensions?: {
    length: number
    width: number
    height: number
    unit: 'cm' | 'in'
  }
  color?: string
  size?: string
  material?: string
  style?: string
  keywords: string[]
  
  // التبويب 5: الإعلانات المتعددة
  num_listings: number           // عدد الإعلانات
  vary_sku: boolean              // تغيير SKU
  vary_price: boolean            // تغيير السعر
  vary_title: boolean            // تغيير العنوان
}
```

#### DataTable Component

```typescript
interface DataTableProps<T> {
  columns: ColumnDef<T>[]        // تعريف الأعمدة
  data: T[]                      // البيانات
  loading?: boolean              // حالة التحميل
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
  }
  sorting?: {
    field: string
    direction: 'asc' | 'desc'
    onSort: (field: string) => void
  }
  selection?: {
    selected: string[]
    onSelect: (ids: string[]) => void
  }
  actions?: {
    label: string
    icon: React.ReactNode
    onClick: (items: T[]) => void
    disabled?: boolean
  }[]
  emptyState?: {
    title: string
    description: string
    action?: {
      label: string
      onClick: () => void
    }
  }
}
```

---

## 7. تصميم الشاشات والصفحات

### 7.1 لوحة التحكم (Dashboard)

```
┌──────────────────────────────────────────────────────────────────┐
│  🟠 Crazy Lister v2.0          [🔍 بحث...] [🔔3] [👤 المستخدم] │
├──────────────┬───────────────────────────────────────────────────┤
│              │  📊 لوحة التحكم                                   │
│  📊 لوحة     │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  التحكم      │  │📦 1,234 │ │⏳ 56    │ │✅ 1,178 │ │❌ 12    ││
│              │  │المنتجات │ │في الطابور│ │منشورة  │ │فاشلة   ││
│  📦 المنتجات│  └─────────┘ └─────────┘ └─────────┘ └─────────┘│
│  🚀 طابور    │                                                   │
│  الرفع       │  📈 الإرسالات خلال 30 يوم                        │
│  📊 التقارير│  ┌─────────────────────────────────────────────┐ │
│  ⚙️ الإعدادات│  │████████████████████████████████████████████│ │
│              │  │█████ Success ██████ Fail ████ Pending     │ │
│              │  └─────────────────────────────────────────────┘ │
│              │                                                   │
│  [تسجيل     │  ⏳ آخر الإرسالات                                  │
│   الخروج]   │  ┌─────────────────────────────────────────────┐ │
│              │  │ المنتج    │ SKU  │ الحالة │ الوقت │ عرض  │ │
│              │  ├─────────────────────────────────────────────┤ │
│              │  │ تيشرت    │ T001 │ ✅ منشور│ 10:30 │ 🔗   │ │
│              │  │ بنطال    │ P002 │ 🟡 جاري │ 10:31 │ ⏳   │ │
│              │  │ حذاء     │ S003 │ ❌ فشل │ 10:32 │ 🔄   │ │
│              │  └─────────────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────────┘
```

### 7.2 صفحة إضافة منتج (5 تبويبات)

```
┌──────────────────────────────────────────────────────────────────┐
│  إضافة منتج جديد                          [💾 حفظ] [📤 رفع]     │
├──────────────────────────────────────────────────────────────────┤
│  📦 أساسيات │ 💰 تسعير │ 🖼️ صور │ ⚙️ خصائص │ 📢 إعلانات متعددة│
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SKU: [_________________]  اسم المنتج: [____________________]   │
│  الفئة: [إلكترونيات ▼]     الماركة: [____________________]       │
│  UPC/EAN: [______________]  الوصف:                               │
│                            [_________________________________]   │
│                            [_________________________________]   │
│                            [_________________________________]   │
│                                                                   │
│  النقاط الرئيسية:                                                 │
│  1. [________________________________________________________]  │
│  2. [________________________________________________________]  │
│  3. [________________________________________________________]  │
│  4. [________________________________________________________]  │
│  5. [________________________________________________________]  │
│                                                                   │
├──────────────────────────────────────────────────────────────────┤
│  [التبويب التالي →]                                              │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 صفحة طابور الرفع

```
┌──────────────────────────────────────────────────────────────────┐
│  🚀 طابور الرفع الآلي          [▶️ رفع الكل] [⏸️ إيقاف] [🔄]   │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ # │ المنتج    │ SKU  │ الحالة   │ الوقت  │ Feed ID │ إجراء│ │
│  ├───┼───────────┼──────┼──────────┼────────┼─────────┼──────┤ │
│  │ 1 │ تيشرت    │ T001 │ ✅ منشور │ 10:30  │ Feed_123│ 🔗   │ │
│  │ 2 │ بنطال    │ P002 │ 🟡 جاري  │ 10:31  │ -       │ ⏳   │ │
│  │ 3 │ حذاء     │ S003 │ ❌ فشل   │ 10:32  │ -       │ 🔄   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  📊 الإحصائيات: ✅ 45 منشور | ❌ 3 فشل | ⏳ 8 قيد المعالجة       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. تكامل الـ API التفصيلي

### 8.1 مخطط الاتصال

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend → Backend API                   │
│                                                             │
│  1. تسجيل الدخول                                            │
│     POST /api/v1/sellers/auth-url                           │
│     → Redirect → Amazon LWA → Callback → Token              │
│                                                             │
│  2. إدارة المنتجات                                          │
│     GET    /api/v1/products/?seller_id=...&page=1           │
│     POST   /api/v1/products/?seller_id=...                  │
│     PUT    /api/v1/products/{id}                            │
│     DELETE /api/v1/products/{id}                            │
│                                                             │
│  3. الإرسالات                                               │
│     POST   /api/v1/listings/submit/                         │
│     GET    /api/v1/listings/?seller_id=...                  │
│     POST   /api/v1/listings/{id}/retry                      │
│                                                             │
│  4. حالة Feeds                                              │
│     GET    /api/v1/feeds/{feed_id}/status                   │
│                                                             │
│  5. WebSocket Real-time                                     │
│     ws://localhost:8000/ws/tasks/{task_id}                  │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Axios Configuration

```typescript
// api/client.ts
import axios from 'axios'
import { API_BASE_URL } from './constants'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept-Language': 'ar',
  },
})

// Request Interceptor - إضافة التوكين
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth-token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor - معالجة الأخطاء
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 401 - إعادة التوجيه للدخول
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // 429 - Rate Limit
    if (error.response?.status === 429) {
      // Retry after header
      const retryAfter = error.response.headers['retry-after'] || 5
      await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000))
      return api(originalRequest)
    }

    // 5xx - Server Error
    if (error.response?.status >= 500) {
      toast.error('خطأ في الخادم، يرجى المحاولة لاحقاً')
    }

    return Promise.reject(error)
  }
)

export default api
```

### 8.3 React Query Hooks

```typescript
// api/hooks/useProducts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../client'
import type { Product, ProductCreate, ProductListResponse } from '../types'

export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (params: Record<string, any>) => [...productKeys.lists(), params] as const,
  details: () => [...productKeys.all, 'detail'] as const,
  detail: (id: string) => [...productKeys.details(), id] as const,
}

export function useProducts(params: {
  seller_id: string
  page?: number
  status?: string
  category?: string
}) {
  return useQuery({
    queryKey: productKeys.list(params),
    queryFn: async () => {
      const { data } = await api.get<ProductListResponse>('/products/', {
        params,
      })
      return data
    },
    staleTime: 1000 * 60 * 5, // 5 دقائق
  })
}

export function useCreateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ProductCreate & { seller_id: string }) => {
      const { seller_id, ...productData } = data
      const { data: response } = await api.post<Product>(
        `/products/?seller_id=${seller_id}`,
        productData
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(productKeys.list({
        seller_id: variables.seller_id,
      }))
      toast.success('تم إنشاء المنتج بنجاح')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'فشل إنشاء المنتج')
    },
  })
}
```

---

## 9. إدارة الحالة State Management

### 9.1 استراتيجية إدارة الحالة

| نوع الحالة | الأداة | السبب | أمثلة |
|------------|--------|-------|-------|
| **Server State** | React Query | تلقائي caching, retry, refetch | منتجات، إرسالات، بائعين |
| **UI State** | Zustand | بسيط، سريع، لا boilerplate | قائمة جانبية، ثيم، لغة |
| **Form State** | React Hook Form | بدون re-render، أداء عالي | نماذج المنتجات، الدخول |
| **Auth State** | React Context | مدمج مع التوثيق | مستخدم، توكين |

### 9.2 Zustand Stores

```typescript
// store/ui.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark'
  locale: 'ar' | 'en'
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  setLocale: (locale: 'ar' | 'en') => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      locale: 'ar',
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      setLocale: (locale) => set({ locale }),
    }),
    {
      name: 'crazy-lister-ui',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
        locale: state.locale,
      }),
    }
  )
)
```

---

## 10. نظام التوثيق والأمان

### 10.1 مخطط OAuth2 مع Amazon

```
┌─────────┐     ┌──────────┐     ┌───────────────┐     ┌──────────┐
│فرونت-إند │     │باك-إند   │     │Amazon LWA     │     │Amazon    │
│          │     │FastAPI   │     │               │     │SP-API    │
└────┬─────┘     └────┬─────┘     └───────┬───────┘     └────┬─────┘
     │                │                   │                   │
     │ 1. طلب auth-url│                   │                   │
     │───────────────>│                   │                   │
     │                │ 2. بناء Auth URL  │                   │
     │                │──────────────────>│                   │
     │ 3. Auth URL    │                   │                   │
     │<───────────────│                   │                   │
     │                │                   │                   │
     │ 4. Redirect User إلى Amazon LWA                        │
     │───────────────────────────────────────────────────────>│
     │                │                   │                   │
     │ 5. صفحة تسجيل دخول Amazon                              │
     │<───────────────────────────────────────────────────────│
     │                │                   │                   │
     │ 6. إدخال بيانات + OTP                                   │
     │───────────────────────────────────────────────────────>│
     │                │                   │                   │
     │ 7. Authorization Code                                   │
     │<───────────────────────────────────────────────────────│
     │                │                   │                   │
     │ 8. POST /oauth/callback?code=...                      │
     │───────────────>│                   │                   │
     │                │ 9. Exchange Code  │                   │
     │                │──────────────────>│                   │
     │                │ 10. Refresh Token │                   │
     │                │<──────────────────│                   │
     │ 11. JWT Token  │                   │                   │
     │<───────────────│                   │                   │
     │                │                   │                   │
     │ 12. تخزين Token + Redirect                               │
     │                │                   │                   │
```

### 10.2 أمن البيانات

| الحماية | التنفيذ | الوصف |
|---------|---------|-------|
| **HTTPS** | إجباري | تشفير كل الاتصالات |
| **JWT Tokens** | Access + Refresh | توكينات قصيرة العمر |
| **CSP Headers** | Content-Security-Policy | منع XSS |
| **XSS Protection** | React escaping | تصفية المدخلات |
| **CSRF Protection** | SameSite Cookies | منع CSRF |
| **Rate Limiting** | API Level | 60 طلب/دقيقة |
| **Input Validation** | Zod Schema | التحقق من صحة البيانات |
| **Secure Storage** | httpOnly Cookies | تخزين آمن للتوكينات |

---

## 11. المراحل التنفيذية الخمس

### المرحلة 1: ✅ الإعداد والبنية الأساسية (مكتملة)

**الإنجازات:**
- ✅ مشروع React + TypeScript + Vite
- ✅ Tailwind CSS v4 + ألوان Amazon
- ✅ React Router + حماية المسارات
- ✅ React Query + Zustand
- ✅ Axios + Interceptors
- ✅ Layout + Sidebar + Header
- ✅ صفحة تسجيل الدخول
- ✅ صفحة Dashboard
- ✅ صفحة إضافة منتج (5 تبويبات)
- ✅ TypeScript Types
- ✅ API Endpoints

**المدة:** أسبوع  
**الحالة:** ✅ مكتملة

---

### المرحلة 2: 🔲 التوثيق وربط الـ API (الأسبوع 3-4)

**المهام:**
- [ ] OAuth2 مع Amazon LWA
  - [ ] زر تسجيل الدخول مع Amazon
  - [ ] استقبال Callback
  - [ ] تخزين JWT Token
  - [ ] Refresh Token تلقائي
- [ ] ربط صفحة المنتجات بالـ API
  - [ ] GET /products
  - [ ] POST /products
  - [ ] PUT /products/:id
  - [ ] DELETE /products/:id
- [ ] DataTable كامل
  - [ ] Pagination
  - [ ] Sorting
  - [ ] Filtering
  - [ ] Bulk Actions
- [ ] صفحة تعديل المنتج
  - [ ] جلب بيانات المنتج
  - [ ] ملء النموذج
  - [ ] حفظ التغييرات
- [ ] صفحة تفاصيل المنتج
  - [ ] عرض كل البيانات
  - [ ] تاريخ الإرسالات
  - [ ] إجراءات سريعة
- [ ] حماية المسارات
  - [ ] Auth Guard
  - [ ] Role-based Access
  - [ ] Token Expiry Handling

**المخرجات:**
- نظام توثيق كامل مع Amazon
- CRUD كامل للمنتجات
- DataTable احترافي

---

### المرحلة 3: 🔲 الرفع الآلي والنتائج (الأسبوع 5-7)

**المهام:**
- [ ] صفحة طابور الرفع
  - [ ] عرض الطابور
  - [ ] إرسال Listing
  - [ ] Retry Failed
  - [ ] Cancel Pending
- [ ] WebSocket Real-time
  - [ ] إعداد WebSocket
  - [ ] تتبع تقدم المهام
  - [ ] إشعارات فورية
- [ ] صفحة النتائج الحية
  - [ ] جدول النتائج
  - [ ] روابط Amazon
  - [ ] تصدير CSV/Excel
- [ ] الرسوم البيانية
  - [ ] Recharts إعداد
  - [ ] رسم الإرسالات
  - [ ] رسم نسبة النجاح
  - [ ] رسم المخزون
- [ ] Bulk Submit
  - [ ] اختيار منتجات متعددة
  - [ ] إرسال جماعي
  - [ ] تتبع التقدم
- [ ] نظام الإشعارات
  - [ ] Toast Notifications
  - [ ] WebSocket Notifications
  - [ ] Notification Center

**المخرجات:**
- نظام رفع آلي كامل
- إشعارات real-time
- تقارير ورسوم بيانية

---

### المرحلة 4: 🔲 التحسين والإضافات (الأسبوع 8-9)

**المهام:**
- [ ] تحسين الأداء
  - [ ] Code Splitting
  - [ ] Lazy Loading
  - [ ] Image Optimization
  - [ ] Bundle Analysis
- [ ] PWA
  - [ ] Service Worker
  - [ ] Offline Support
  - [ ] Install Prompt
  - [ ] App Manifest
- [ ] الترجمة
  - [ ] i18next إعداد
  - [ ] ترجمة عربية كاملة
  - [ ] ترجمة إنجليزية
  - [ ] تبديل اللغة
- [ ] إمكانية الوصول
  - [ ] WCAG 2.1 AA
  - [ ] Keyboard Navigation
  - [ ] Screen Reader Support
  - [ ] Color Contrast
- [ ] الوضع الداكن
  - [ ] Dark Theme
  - [ ] Light Theme
  - [ ] System Preference
  - [ ] Toggle Button

**المخرجات:**
- تطبيق محسّن
- PWA جاهز
- دعم متعدد اللغات

---

### المرحلة 5: 🔲 الاختبارات والنشر (الأسبوع 10-12)

**المهام:**
- [ ] Unit Tests
  - [ ] Vitest إعداد
  - [ ] اختبارات المكونات
  - [ ] اختبارات Hooks
  - [ ] اختبارات Utils
- [ ] Integration Tests
  - [ ] اختبارات النماذج
  - [ ] اختبارات API
  - [ ] اختبارات Routing
- [ ] E2E Tests
  - [ ] Playwright إعداد
  - [ ] اختبار تسجيل الدخول
  - [ ] اختبار إضافة منتج
  - [ ] اختبار الرفع الآلي
- [ ] Docker + Nginx
  - [ ] Dockerfile
  - [ ] Nginx Config
  - [ ] docker-compose.yml
- [ ] CI/CD
  - [ ] GitHub Actions
  - [ ] Lint + Type Check
  - [ ] Tests
  - [ ] Build
  - [ ] Deploy
- [ ] المراقبة
  - [ ] Sentry (أخطاء)
  - [ ] Analytics (زوار)
  - [ ] Performance Monitoring

**المخرجات:**
- اختبارات تغطي 80%+
- CI/CD كامل
- تطبيق جاهز للإنتاج

---

## 12. نظام الاختبارات

### 12.1 استراتيجية الاختبارات

```
┌─────────────────────────────────────────────────────────────┐
│                  Testing Pyramid                             │
│                                                             │
│                       ╱  E2E Tests (10%)                    │
│                      ╱   Playwright                         │
│                     ╱   - User Flows                        │
│                    ╱   - Critical Paths                     │
│                   ╱                                          │
│                  ╱   Integration Tests (20%)                 │
│                 ╱   React Testing Library                    │
│                ╱   - Component Integration                   │
│               ╱   - Form Validation                          │
│              ╱   - API Calls                                 │
│             ╱                                                 │
│            ╱   Unit Tests (70%)                              │
│           ╱   Vitest + RTL                                   │
│          ╱   - Utils/Helpers                                 │
│         ╱   - Hooks                                          │
│        ╱   - Components                                      │
│       ╱                                                      │
│      ╱   Types/TypeScript                                    │
│     ╱   tsc --noEmit (Compile-time)                          │
│    ╱                                                         │
└─────────────────────────────────────────────────────────────┘
```

### 12.2 أمثلة اختبارات

```typescript
// __tests__/ProductForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ProductForm } from '@/components/forms/ProductForm'
import { describe, it, expect, vi } from 'vitest'

describe('ProductForm', () => {
  it('يجب أن يعرض جميع التبويبات الخمسة', () => {
    render(<ProductForm onSubmit={vi.fn()} />)

    expect(screen.getByText('المعلومات الأساسية')).toBeInTheDocument()
    expect(screen.getByText('التسعير والمخزون')).toBeInTheDocument()
    expect(screen.getByText('الصور والوسائط')).toBeInTheDocument()
    expect(screen.getByText('الخصائص المتقدمة')).toBeInTheDocument()
    expect(screen.getByText('الإعلانات المتعددة')).toBeInTheDocument()
  })

  it('يجب أن يظهر خطأ عند SKU فارغ', async () => {
    render(<ProductForm onSubmit={vi.fn()} />)

    fireEvent.click(screen.getByText('حفظ المنتج'))

    await waitFor(() => {
      expect(screen.getByText(/SKU مطلوب/i)).toBeInTheDocument()
    })
  })

  it('يجب أن يظهر خطأ عند سعر سالب', async () => {
    render(<ProductForm onSubmit={vi.fn()} />)

    const priceInput = screen.getByLabelText(/السعر/i)
    fireEvent.change(priceInput, { target: { value: '-10' } })
    fireEvent.blur(priceInput)

    await waitFor(() => {
      expect(screen.getByText(/السعر يجب أن يكون رقم موجب/i))
        .toBeInTheDocument()
    })
  })
})
```

---

## 13. الأداء والتحسين

### 13.1 معايير الأداء المستهدفة

| المقياس | الهدف | الأداة |
|---------|-------|--------|
| First Contentful Paint | < 1.5s | Lighthouse |
| Largest Contentful Paint | < 2.5s | Lighthouse |
| Time to Interactive | < 3.5s | Lighthouse |
| Cumulative Layout Shift | < 0.1 | Lighthouse |
| Total Blocking Time | < 200ms | Lighthouse |
| Bundle Size (Gzip) | < 200KB | Webpack Bundle Analyzer |

### 13.2 استراتيجيات التحسين

| الاستراتيجية | الأداة | التأثير |
|--------------|--------|---------|
| **Code Splitting** | React.lazy + Suspense | تقليل Bundle 60% |
| **Route-based Splitting** | React Router lazy | تحميل الصفحة فقط |
| **Lazy Images** | react-lazy-load-image | تحسين LCP |
| **Virtualization** | react-virtuoso | جداول بدون تجميد |
| **Memoization** | React.memo + useMemo | منع re-render |
| **Compression** | Brotli + Gzip | تقليل الملفات 70% |
| **CDN** | Cloudflare | سرعة عالمية |
| **Caching** | React Query + Service Worker | تقليل طلبات API |

---

## 14. التوزيع والنشر

### 14.1 Dockerfile للإنتاج

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 14.2 Nginx Configuration

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA Routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy (اختياري)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket Proxy
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Cache Static Assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
```

### 14.3 CI/CD Pipeline

```yaml
# .github/workflows/frontend.yml
name: Frontend CI/CD

on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run type-check
      - run: cd frontend && npm test -- --coverage
      - run: cd frontend && npm run build

  e2e:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: cd frontend && npm ci
      - run: npx playwright install --with-deps
      - run: cd frontend && npm run test:e2e

  deploy:
    needs: [quality, e2e]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          cd frontend
          docker build -t crazy-lister-frontend .
          docker push your-registry/crazy-lister-frontend:latest
```

---

## 15. خطة الطوارئ

### 15.1 سيناريوهات الطوارئ

| السيناريو | التأثير | الحل |
|-----------|---------|------|
| **API Down** | لا يمكن تحميل البيانات | عرض cached data + رسالة خطأ |
| **WebSocket Down** | لا إشعارات real-time | Polling كل 30 ثانية |
| **Token Expired** | المستخدم مفصول | Refresh Token تلقائي |
| **Network Slow** | بطء التحميل | Skeleton Loading + Pagination |
| **Browser Old** | لا يدعم الميزات | رسالة ترقية المتصفح |
| **Storage Full** | لا يمكن التخزين | Clear Cache تلقائي |

### 15.2 Error Boundaries

```typescript
// components/common/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info)
    // Send to Sentry
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-8 text-center">
          <h2 className="text-xl font-bold text-red-600">حدث خطأ غير متوقع</h2>
          <p className="text-gray-600 mt-2">{this.state.error?.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-amazon-orange rounded-lg"
          >
            إعادة تحميل الصفحة
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
```

---

##  الملاحق

### أ. قائمة المهام الكاملة (Checklist)

```markdown
## المرحلة 1: ✅ الإعداد (مكتملة)
- [x] React + TypeScript + Vite
- [x] Tailwind CSS v4
- [x] React Router
- [x] React Query + Zustand
- [x] Axios + Interceptors
- [x] Layout + Sidebar + Header
- [x] LoginPage
- [x] DashboardPage
- [x] ProductCreatePage (5 tabs)
- [x] TypeScript Types
- [x] API Endpoints

## المرحلة 2: 🔲 التوثيق والـ API
- [ ] OAuth2 مع Amazon LWA
- [ ] ربط المنتجات بالـ API
- [ ] DataTable كامل
- [ ] صفحة تعديل المنتج
- [ ] صفحة تفاصيل المنتج
- [ ] حماية المسارات

## المرحلة 3: 🔲 الرفع والنتائج
- [ ] طابور الرفع
- [ ] WebSocket Real-time
- [ ] صفحة النتائج
- [ ] الرسوم البيانية
- [ ] Bulk Submit
- [ ] نظام الإشعارات

## المرحلة 4: 🔲 التحسين
- [ ] Code Splitting
- [ ] PWA
- [ ] الترجمة (عربي/إنجليزي)
- [ ] إمكانية الوصول
- [ ] الوضع الداكن

## المرحلة 5: 🔲 الاختبارات والنشر
- [ ] Unit Tests
- [ ] Integration Tests
- [ ] E2E Tests
- [ ] Docker + Nginx
- [ ] CI/CD Pipeline
- [ ] Sentry Monitoring
```

### ب. جدول المراجع السريعة

| المرجع | الرابط |
|--------|--------|
| React Docs | https://react.dev |
| TypeScript Handbook | https://www.typescriptlang.org/docs |
| Tailwind CSS | https://tailwindcss.com/docs |
| React Query | https://tanstack.com/query/latest |
| Zustand | https://zustand.docs.pmnd.rs |
| React Hook Form | https://react-hook-form.com |
| Zod | https://zod.dev |
| Recharts | https://recharts.org |
| i18next | https://www.i18next.com |

---

**آخر تحديث:** 9 أبريل 2026  
**المسؤول:** Senior Frontend Engineer  
**المراجعة التالية:** نهاية المرحلة 2
