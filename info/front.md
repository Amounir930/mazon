🚀 خطة تطوير فرونت-إند شامل لـ Crazy Lister v2.0
📋 فهرس الخطة
تحليل الوضع الحالي
الأهداف والتوجه العام
التقنيات المختارة
هندسة الفرونت-إند
هيكل الصفحات والشاشات
تخطيط التصميم UI/UX
تكامل الـ API
خطة التنفيذ (5 مراحل)
إدارة الحالة State Management
الأمان والتوثيق
الأداء والتحسين
الاختبارات
التوزيع والنشر
1. تحليل الوضع الحالي
فرونت-إند قديم (Tkinter - Crazy Lister.py)
الميزة	الوصف	التقييم
تسجيل دخول آلي	دخول حساب أمازون + OTP	⚠️ يحتاج تحديث للـ SP-API
إضافة منتج متقدم	نموذج 5 تبويبات (بيانات أساسية، تسعير، صور، خصائص، إعلانات متعددة)	✅ ممتاز من حيث المحتوى
إدارة المنتجات	جدول + أزرار CRUD	✅ جيد
طابور الرفع	قائمة المنتجات في الانتظار	✅ جيد
النتائج الحية	إحصائيات + روابط أمازون	✅ جيد
تصدير تقارير	TXT + CSV	✅ مفيد
واجهة عربية RTL	كامل الواجهة بالعربية	✅ ممتاز
نظام إعلانات متعددة	إنشاء نسخ متعددة من نفس المنتج	✅ فريد
مشاكل الفرونت-إند القديم
Tkinter Desktop - لا يعمل على الموبايل، لا يمكن الوصول من أي مكان
لا يوجد توثيق - بيانات الدخول مخزنة في JSON
لا يوجد إشعارات - لا يعرف المستخدم حالة المهام
لا يوجد مشاركة - لا يمكن للمستخدمين العمل معاً
واجهة بطيئة - Tkinter ثقيل على الأنظمة القديمة
لا يوجد تصحيح أخطاء - صعب تتبع المشاكل
2. الأهداف والتوجه العام
الرؤية
“تحويل Crazy Lister من تطبيق سطح مكتب إلى منصة ويب احترافية عالمية تعمل على كل الأجهزة”

الأهداف الرئيسية
الهدف	الوصف	الأولوية
تجربة مستخدم حديثة	واجهة سريعة، جميلة، سهلة الاستخدام	🔴 عالية
تصميم متجاوب	يعمل على Desktop + Tablet + Mobile	🔴 عالية
دعم كامل للغة العربية	RTL كامل مع إمكانية التبديل للإنجليزية	🔴 عالية
حالة实时 للمهام	WebSocket لعرض تقدم الرفع الآلي لحظة بلحظة	🟡 متوسطة
نظام إشعارات	إشعارات فورية عند نجاح/فشل المهام	🟡 متوسطة
أداء عالي	تحميل سريع، تجزئة الكود، التخزين المؤقت	🔴 عالية
إمكانية الوصول	دعم قارئات الشاشة، تباين الألوان	🟢 منخفضة
3. التقنيات المختارة
🏗️ الهيكل التقني الأساسي
الفرونت-إند: React 18 + TypeScript + Vite
├── التصميم: Tailwind CSS + shadcn/ui
├── إدارة الحالة: Zustand + React Query
├── النماذج: React Hook Form + Zod
├── الإشعارات: WebSocket + React Hot Toast
├── التوجيه: React Router v6
├── الرسوم البيانية: Recharts
└── الترجمة: i18next (عربي/إنجليزي)
لماذا هذه التقنيات؟
التقنية	السبب
React 18	مجتمع ضخم، مكونات جاهزة، أداء ممتاز
TypeScript	أمان النوع، إكمال تلقائي، تقليل الأخطاء
Vite	بناء سريع جداً، HMR فوري
Tailwind CSS	تصميم سريع، ملف صغير، تخصيص كامل
shadcn/ui	مكونات احترافية، قابلة للتخصيص، RTL مدعوم
Zustand	إدارة حالة بسيطة وخفيفة
React Query	إدارة البيانات من الـ API بشكل ذكي
React Hook Form	نماذج سريعة بدون re-render زائد
Zod	تحقق من صحة البيانات متوافق مع الـ backend
4. هندسة الفرونت-إند
هيكل المشروع المقترح
frontend/
├── public/
│   ├── favicon.ico
│   ├── logo.svg
│   └── robots.txt
├── src/
│   ├── main.tsx                    # نقطة الدخول
│   ├── App.tsx                     # المكون الرئيسي
│   ├── router.tsx                  # إعداد التوجيه
│   │
│   ├── api/                        # طبقة الـ API
│   │   ├── client.ts               # عميل HTTP (Axios/fetch)
│   │   ├── endpoints.ts            # جميع نقاط الـ API
│   │   ├── types.ts                # أنواع TypeScript
│   │   └── hooks/                  # React Query hooks
│   │       ├── useProducts.ts
│   │       ├── useListings.ts
│   │       ├── useSellers.ts
│   │       └── useFeeds.ts
│   │
│   ├── components/                 # مكونات قابلة لإعادة الاستخدام
│   │   ├── ui/                     # مكونات shadcn/ui
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── tabs.tsx
│   │   │   └── ...
│   │   ├── layout/                 # مكونات التخطيط
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Layout.tsx
│   │   ├── forms/                  # مكونات النماذج
│   │   │   ├── ProductForm.tsx
│   │   │   ├── SellerForm.tsx
│   │   │   └── ListingForm.tsx
│   │   ├── common/                 # مكونات مشتركة
│   │   │   ├── Loading.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── Pagination.tsx
│   │   │   └── StatusBadge.tsx
│   │   └── charts/                 # رسوم بيانية
│   │       ├── ListingStats.tsx
│   │       └── InventoryChart.tsx
│   │
│   ├── pages/                      # صفحات التطبيق
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── OAuthCallback.tsx
│   │   ├── dashboard/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── StatsCards.tsx
│   │   │   └── RecentListings.tsx
│   │   ├── products/
│   │   │   ├── ProductListPage.tsx
│   │   │   ├── ProductCreatePage.tsx
│   │   │   ├── ProductEditPage.tsx
│   │   │   └── ProductDetailPage.tsx
│   │   ├── listings/
│   │   │   ├── ListingQueuePage.tsx
│   │   │   ├── ListingResultsPage.tsx
│   │   │   └── BulkSubmitPage.tsx
│   │   ├── sellers/
│   │   │   ├── SellerListPage.tsx
│   │   │   ├── SellerRegisterPage.tsx
│   │   │   └── SellerDetailPage.tsx
│   │   ├── reports/
│   │   │   ├── ReportsPage.tsx
│   │   │   └── ExportPage.tsx
│   │   └── settings/
│   │       ├── SettingsPage.tsx
│   │       └── ProfilePage.tsx
│   │
│   ├── store/                      # إدارة الحالة (Zustand)
│   │   ├── auth.ts
│   │   ├── products.ts
│   │   ├── listings.ts
│   │   ├── ui.ts
│   │   └── index.ts
│   │
│   ├── hooks/                      # Custom Hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   ├── useToast.ts
│   │   ├── usePagination.ts
│   │   └── useLocalStorage.ts
│   │
│   ├── utils/                      # أدوات مساعدة
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   │
│   ├── lib/                        # مكتبات خارجية مهيأة
│   │   ├── utils.ts
│   │   ├── queryClient.ts
│   │   └── axios.ts
│   │
│   ├── assets/                     # صور، أيقونات، خطوط
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── i18n/                       # الترجمة
│   │   ├── locales/
│   │   │   ├── ar.json
│   │   │   └── en.json
│   │   └── config.ts
│   │
│   └── types/                      # أنواع TypeScript
│       ├── api.ts
│       ├── product.ts
│       ├── listing.ts
│       └── seller.ts
│
├── index.html
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
├── package.json
└── .env.example
5. هيكل الصفحات والشاشات
5.1 الصفحة الرئيسية (Dashboard)
┌─────────────────────────────────────────────────────────────┐
│  🟠 Crazy Lister          [بحث] [إشعارات] [الحساب]         │
├─────────────────────────────────────────────────────────────┤
│  📊 لوحة التحكم                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 📦 1,234 │ │ ⏳ 56    │ │ ✅ 1,178 │ │ ❌ 12    │      │
│  │ المنتجات │ │ في الطابور│ │ منشورة  │ │ فاشلة   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                            │
│  📈 رسم بياني: الإرسالات خلال الشهر                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [رسم بياني شريطي يعرض النجاح/الفشل يومياً]          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ⏳ آخر الإرسالات                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ المنتج | SKU | الحالة | الوقت | زر عرض               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
5.2 صفحة إضافة منتج (من الفرونت القديم)
التبويبات الخمسة:

المعلومات الأساسية - SKU, الاسم, الفئة, الماركة, UPC/EAN, الوصف
التسعير والمخزون - السعر, التكلفة, الكمية, الوزن
الصور والوسائط - الصورة الرئيسية + 8 صور إضافية
الخصائص المتقدمة - الأبعاد, اللون, الحجم, المادة, الكلمات المفتاحية
الإعلانات المتعددة - عدد النسخ, تغيير SKU تلقائي, تغيير السعر
5.3 صفحة طابور الرفع
┌─────────────────────────────────────────────────────────────┐
│  🚀 طابور الرفع الآلي                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [رفع الكل] [إيقاف مؤقت] [مسح الطابور] [تحديث]        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌────┬────────────┬──────┬──────────┬──────────┬───────┐ │
│  │ #  │ المنتج     │ SKU  │ الحالة   │ الوقت    │ إجراء │ │
│  ├────┼────────────┼──────┼──────────┼──────────┼───────┤ │
│  │ 1  │ تيشرت أحمر│ T001 │  منشور │ 10:30    │ 🔗    │ │
│  │ 2  │ بنطال أزرق│ P002 │ 🟡 جاري   │ 10:31    │ ⏳    │ │
│  │ 3  │ حذاء رياضي│ S003 │ 🔴 فشل    │ 10:32    │ 🔄    │ │
│  └────┴────────────┴──────┴──────────┴──────────┴───────┘ │
│                                                            │
│  📊 الإحصائيات: ✅ 45 | ❌ 3 | ⏳ 8                         │
└─────────────────────────────────────────────────────────────┘
5.4 صفحة النتائج الحية
┌─────────────────────────────────────────────────────────────┐
│  📊 النتائج الحية                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ ✅ 85%   │ │ 📦 234   │ │ ⏱️ 2.3s  │                     │
│  │ نسبة النجاح│ │ إجمالي   │ │ متوسط الوقت│                     │
│  └──────────┘ └────────── └──────────┘                     │
│                                                            │
│  [تصدير CSV] [تصدير PDF] [تصدير Excel]                    │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ رسم بياني دائري: موزع النتائج (نجاح/فشل)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
6. تخطيط التصميم UI/UX
6.1 نظام التصميم (Design System)
// tailwind.config.ts
const config = {
  theme: {
    extend: {
      colors: {
        // ألوان Amazon الأصلية
        amazon: {
          dark: '#131921',      // الهيدر الداكن
          orange: '#FF9900',    // اللون البرتقالي
          blue: '#232F3E',      // الأزرق الداكن
          light: '#FEBD69',     // البرتقالي الفاتح
        },
        // ألوان الحالة
        status: {
          success: '#22c55e',
          warning: '#eab308',
          error: '#ef4444',
          info: '#3b82f6',
        },
      },
      fontFamily: {
        arabic: ['Cairo', 'Tajawal', 'sans-serif'],
        english: ['Inter', 'sans-serif'],
      },
    },
  },
}
6.2 المبادئ التصميمية
المبدأ	التطبيق
البساطة	واجهة نظيفة، عناصر ضرورية فقط
السرعة	تحميل < 2 ثانية، تفاعل فوري
الوضوح	ألوان حالة واضحة، رسائل خطأ مفهومة
الاتساق	نفس المكونات، نفس الألوان في كل مكان
إمكانية الوصول	تباين عالي، دعم لوحة المفاتيح
RTL أصيل	تصميم من اليمين لليسار بشكل طبيعي
6.3 مكونات رئيسية
ProductCard - بطاقة المنتج في القائمة
ListingStatusBadge - شارة حالة الإرسال
BulkUploadModal - نافذة الرفع الجماعي
ProductFormTabs - تبويبات نموذج المنتج
StatsCard - بطاقة إحصائيات
WebSocketNotification - إشعارات实时
7. تكامل الـ API
7.1 عميل HTTP
// api/client.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor للتوثيق
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor للأخطاء
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // إعادة التوجيه لصفحة الدخول
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
7.2 أنواع TypeScript
// types/product.ts
export interface Product {
  id: string;
  seller_id: string;
  sku: string;
  name: string;
  category: string;
  brand: string;
  upc?: string;
  ean?: string;
  description: string;
  bullet_points: string[];
  keywords: string[];
  price: number;
  compare_price?: number;
  cost?: number;
  quantity: number;
  weight?: number;
  dimensions?: {
    length: number;
    width: number;
    height: number;
    unit: 'cm';
  };
  images: string[];
  attributes: Record<string, any>;
  status: 'draft' | 'queued' | 'processing' | 'published' | 'failed';
  optimized_data?: {
    optimized_title: string;
    optimized_description: string;
    optimized_bullet_points: string[];
    keywords: string[];
    confidence_score: number;
  };
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}
7.3 React Query Hooks
// api/hooks/useProducts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { Product, ProductListResponse, ProductCreate } from '../types';

export const PRODUCT_KEYS = {
  all: ['products'] as const,
  lists: () => [...PRODUCT_KEYS.all, 'list'] as const,
  list: (params: any) => [...PRODUCT_KEYS.lists(), params] as const,
  details: () => [...PRODUCT_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...PRODUCT_KEYS.details(), id] as const,
};

export function useProducts(params: {
  seller_id: string;
  page?: number;
  status?: string;
}) {
  return useQuery({
    queryKey: PRODUCT_KEYS.list(params),
    queryFn: async () => {
      const { data } = await api.get<ProductListResponse>('/products/', {
        params,
      });
      return data;
    },
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (product: ProductCreate) => {
      const { data } = await api.post<Product>('/products/', product);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(PRODUCT_KEYS.lists());
    },
  });
}
8. خطة التنفيذ (5 مراحل)
المرحلة 1: الإعداد والبنية الأساسية (الأسبوع 1-2)
المهام:

[ ] إنشاء مشروع React + TypeScript + Vite
[ ] تثبيت وإعداد Tailwind CSS
[ ] إعداد shadcn/ui
[ ] إعداد React Router
[ ] إعداد React Query + Zustand
[ ] إعداد Axios مع Interceptors
[ ] إعداد i18n (عربي/إنجليزي)
[ ] إنشاء هيكل المجلدات
[ ] إعداد ESLint + Prettier
[ ] إنشاء Components الأساسية (Button, Input, etc.)
المخرجات:

مشروع React يعمل
نظام تصميم أساسي
تهيئة API client
المرحلة 2: التوثيق والصفحات الأساسية (الأسبوع 3-4)
المهام:

[ ] صفحة تسجيل الدخول
[ ] صفحة التسجيل
[ ] OAuth Callback من Amazon
[ ] صفحة Dashboard الرئيسية
[ ] Sidebar + Header
[ ] نظام التوثيق (JWT)
[ ] حماية المسارات (Protected Routes)
[ ] صفحة الإعدادات
المخرجات:

نظام توثيق كامل
واجهة أساسية جاهزة
حماية المسارات
المرحلة 3: إدارة المنتجات (الأسبوع 5-7)
المهام:

[ ] صفحة قائمة المنتجات (جدول + بحث + تصفية)
[ ] صفحة إضافة منتج (5 تبويبات من الفرونت القديم)
[ ] صفحة تعديل المنتج
[ ] صفحة تفاصيل المنتج
[ ] نموذج ProductForm مع React Hook Form + Zod
[ ] رفع الصور (Drag & Drop)
[ ] التحقق من صحة البيانات
[ ] Pagination + Sorting
المخرجات:

CRUD كامل للمنتجات
نموذج إضافة منتج مطابق للفرونت القديم
رفع صور
المرحلة 4: الرفع الآلي والنتائج (الأسبوع 8-10)
المهام:

[ ] صفحة طابور الرفع
[ ] صفحة النتائج الحية
[ ] WebSocket للإشعارات实时
[ ] رسوم بيانية (Recharts)
[ ] تصدير التقارير (CSV, PDF, Excel)
[ ] Bulk Submit
[ ] Retry Failed Listings
[ ] إحصائيات مفصلة
المخرجات:

نظام رفع آلي كامل
إشعارات实时
تقارير وإحصائيات
المرحلة 5: التحسين والنشر (الأسبوع 11-12)
المهام:

[ ] تحسين الأداء (Code Splitting, Lazy Loading)
[ ] PWA (Progressive Web App)
[ ] تحسين SEO
[ ] اختبارات شاملة (Unit + E2E)
[ ] Dockerize Frontend
[ ] CI/CD Pipeline
[ ] مراقبة الأخطاء (Sentry)
[ ] تحليلات (Google Analytics)
[ ] التوثيق النهائي
المخرجات:

تطبيق محسّن وجاهز للإنتاج
اختبارات تغطي 80%+
CI/CD كامل
PWA يعمل offline
9. إدارة الحالة State Management
9.1 Zustand Stores
// store/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
      updateUser: (user) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...user } : null,
        })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token, user }),
    }
  )
);
9.2 React Query للبيانات الخارجية
البيانات	React Query	Zustand
قائمة المنتجات	✅	❌
تفاصيل منتج	✅	❌
طابور الرفع	✅	❌
بيانات المستخدم	❌	✅
إعدادات UI	❌	✅
حالة WebSocket	❌	✅
10. الأمان والتوثيق
10.1 نظام التوثيق
1. المستخدم يدخل بياناته → POST /api/v1/sellers/auth-url
2. يُحوَّل لصفحة Amazon LWA
3. Amazon يرد بـ authorization code
4. الفرونت يرسل code → POST /api/v1/sellers/oauth/callback
5. يستلم access_token + refresh_token
6. يُخزَّن في localStorage
7. يُرسل مع كل طلب كـ Bearer token
10.2 حماية المسارات
// router.tsx
const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      {
        path: 'dashboard',
        element: (
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        ),
      },
      // ...
    ],
  },
  { path: '/login', element: <LoginPage /> },
]);
10.3 أمن البيانات
✅ HTTPS إجباري
✅ CSP Headers
✅ XSS Protection
✅ CSRF Protection
✅ Rate Limiting
✅ Input Validation (Zod)
✅ Sanitization
11. الأداء والتحسين
11.1 استراتيجيات التحسين
الاستراتيجية	الأداة	التأثير
Code Splitting	React.lazy + Suspense	تقليل حجم الـ bundle الأولي
Lazy Loading Images	react-lazy-load-image	تحسين LCP
Virtualization	react-virtuoso	جداول كبيرة بدون تجميد
Caching	React Query cache	تقليل طلبات الـ API
Compression	Brotli + Gzip	تقليل حجم الملفات 70%
CDN	Cloudflare	سرعة التحميل عالمياً
11.2 معايير الأداء المستهدفة
المقياس	الهدف	الأداة
First Contentful Paint	< 1.5s	Lighthouse
Largest Contentful Paint	< 2.5s	Lighthouse
Cumulative Layout Shift	< 0.1	Lighthouse
Time to Interactive	< 3.5s	Lighthouse
Bundle Size (Gzip)	< 200KB	Webpack Bundle Analyzer
12. الاختبارات
12.1 استراتيجية الاختبارات
├── Unit Tests (Jest + React Testing Library)  → 60%
├── Integration Tests (React Testing Library)  → 25%
├── E2E Tests (Playwright)                     → 15%
└── Visual Tests (Chromatic)                   → Optional
12.2 أمثلة اختبارات
// __tests__/ProductForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductForm } from '@/components/forms/ProductForm';

describe('ProductForm', () => {
  it('يجب أن يعرض جميع الحقول المطلوبة', () => {
    render(<ProductForm onSubmit={jest.fn()} />);

    expect(screen.getByLabelText(/اسم المنتج/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/SKU/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/السعر/i)).toBeInTheDocument();
  });

  it('يجب أن يظهر خطأ عند إدخال سعر غير صحيح', async () => {
    render(<ProductForm onSubmit={jest.fn()} />);

    const priceInput = screen.getByLabelText(/السعر/i);
    fireEvent.change(priceInput, { target: { value: '-10' } });
    fireEvent.blur(priceInput);

    expect(await screen.findByText(/السعر يجب أن يكون رقم موجب/i))
      .toBeInTheDocument();
  });
});
13. التوزيع والنشر
13.1 Docker Frontend
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
13.2 Nginx Configuration
# nginx.conf
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # SPA Routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Cache Static Assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
}
13.3 CI/CD Pipeline
# .github/workflows/frontend.yml
name: Frontend CI/CD

on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run type-check
      - run: cd frontend && npm test -- --coverage
      - run: cd frontend && npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          cd frontend
          docker build -t crazy-lister-frontend .
          docker push your-registry/crazy-lister-frontend:latest
📊 ملخص الميزات مقارنة بالفرونت القديم
الميزة	الفرونت القديم (Tkinter)	الفرونت الجديد (React)
المنصة	Desktop فقط	Web (Desktop + Mobile + Tablet)
اللغة	عربي فقط	عربي + إنجليزي
التوثيق	بيانات في JSON	OAuth2 + JWT + Refresh Token
الواجهة	Tkinter	React + Tailwind + shadcn/ui
الحالة	Tkinter Threads	WebSocket + React Query
الإشعارات	messagebox فقط	Toast + WebSocket + Email
الرسوم البيانية	غير موجود	Recharts تفاعلية
التصدير	TXT فقط	CSV, PDF, Excel, JSON
الأداء	بطيء على الأنظمة القديمة	سريع مع Code Splitting
الاختبارات	غير موجود	Jest + Playwright
التوثيق	غير موجود	Swagger + Storybook
PWA	غير ممكن	✅ يعمل Offline