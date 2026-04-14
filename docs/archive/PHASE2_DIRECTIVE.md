# 🎯 ENGINEERING DIRECTIVE — Phase 2: Product Create Page Rebuild

> **من: القائد التقني**
> **إلى: مهندس الـ Frontend**
> **الموضوع: إعادة بناء صفحة إنشاء المنتجات (5 tabs, 29 حقل مطلوب من Amazon)**
> **الأولوية: 🔴 عالية جداً**

---

## 📋 Executive Summary

المرحلة الأولى نجحت 100% — SP-API شغال في Backend وبيقبل المنتجات من Amazon.
**المشكلة الحالية**: صفحة `ProductCreatePage.tsx` مش مصممة لنظام SP-API — فيها 3 steps بسيطة ومش شايلة الـ 29 حقل المطلوب.

**المطلوب**: إعادة بناء الصفحة كاملة بـ **5 tabs شاملة** تغطي كل حقول Amazon SP-API مع validation مخفف و auto-fill ذكي.

---

## 🗺️ الخريطة الكاملة (A → Z)

```
┌─────────────────────────────────────────────────────────────┐
│          Phase 2: Product Create Page Rebuild               │
│                                                              │
│  Tab 1: الهوية الأساسية (8 حقول)                            │
│  Tab 2: الوصف والتفاصيل (8 حقول)                            │
│  Tab 3: التسعير والكمية (5 حقول)                            │
│  Tab 4: الشحن والأبعاد (7 حقول)                             │
│  Tab 5: الصور والإرسال (3 حقول + أزرار)                     │
│                                                              │
│  Total: 31 حقل (29 مطلوب من Amazon + 2 إضافي)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📐 الهيكل التفصيلي لكل Tab

### Tab 1: الهوية الأساسية (Product Identity)

| # | الحقل | النوع | مطلوب؟ | Default | ملاحظات |
|---|-------|-------|--------|---------|----------|
| 1 | `name_ar` | Text | ✅ نعم | — | اسم المنتج بالعربي (min 5 chars) |
| 2 | `name_en` | Text | ✅ نعم | — | اسم المنتج بالإنجليزي (min 5 chars) |
| 3 | `product_type` | Select | ✅ نعم | `HOME_ORGANIZERS_AND_STORAGE` | من قائمة محدودة |
| 4 | `id_type` | Radio | ✅ نعم | `EAN` | EAN / UPC / ASIN / معفي |
| 5 | `ean` | Text | ✅ نعم (لو مش معفي) | — | 13 رقم |
| 6 | `brand` | Text | ✅ نعم | `Generic` | |
| 7 | `model_number` | Text | ✅ نعم | `SKU` | |
| 8 | `manufacturer` | Text | ✅ نعم | `Generic` | |
| 9 | `country_of_origin` | Select | ✅ نعم | `CN` | من قائمة دول |

**UI:**
```
┌─────────────────────────────────────────┐
│  Tab 1: الهوية الأساسية                 │
├─────────────────────────────────────────┤
│  اسم المنتج (عربي) *                   │
│  [___________________________________] │
│                                         │
│  اسم المنتج (English) *                │
│  [___________________________________] │
│                                         │
│  نوع المنتج *                          │
│  [أدوات تنظيم وتخزين المنزل ▼]         │
│                                         │
│  الباركود *                             │
│  ○ EAN (13 رقم)  ○ UPC  ○ ASIN  ○ معفي │
│  [___________________________________] │
│                                         │
│  البراند *            الموديل *         │
│  [Generic_________]  [SKU____________] │
│                                         │
│  المصنع *             بلد المنشأ *      │
│  [Generic_________]  [🇨🇳 الصين_____▼] │
└─────────────────────────────────────────┘
```

---

### Tab 2: الوصف والتفاصيل (Description & Details)

| # | الحقل | النوع | مطلوب؟ | Default | ملاحظات |
|---|-------|-------|--------|---------|----------|
| 1 | `description_ar` | TextArea | ✅ نعم | — | وصف بالعربي (min 10 chars) |
| 2 | `description_en` | TextArea | ✅ نعم | — | وصف بالإنجليزي (min 10 chars) |
| 3 | `bullet_points` | Array(5) | ✅ نعم | — | 5 نقاط بيعية |
| 4 | `browse_node_id` | Select | ✅ نعم | `21863799031` | من قائمة الفئات |
| 5 | `keywords` | Text (tags) | ❌ اختياري | — | 15 كلمة مفتاحية |
| 6 | `material` | Text | ❌ اختياري | — | المادة المصنوع منها |
| 7 | `included_components` | Text | ✅ نعم | اسم المنتج | المكونات المرفقة |
| 8 | `unit_count` | Number | ✅ نعم | `1` | عدد الوحدات |
| 9 | `unit_count_type` | Select | ✅ نعم | `count` | نوع الوحدة |

**UI:**
```
┌─────────────────────────────────────────┐
│  Tab 2: الوصف والتفاصيل                 │
├─────────────────────────────────────────┤
│  الوصف (عربي) *                         │
│  [___________________________________] │
│  [___________________________________] │
│  [___________________________________] │
│                                         │
│  الوصف (English) *                      │
│  [___________________________________] │
│  [___________________________________] │
│  [___________________________________] │
│                                         │
│  النقاط البيعية (5 نقاط) *              │
│  1. [________________________________] │
│  2. [________________________________] │
│  3. [________________________________] │
│  4. [________________________________] │
│  5. [________________________________] │
│                                         │
│  الفئة (Browse Node) *                  │
│  [المنزل والمطبخ > التخزين ▼]          │
│                                         │
│  المكونات المرفقة *                     │
│  [1x المنتج_________________________] │
│                                         │
│  عدد الوحدات *       نوع الوحدة *       │
│  [1______________]  [count________▼]  │
│                                         │
│  الكلمات المفتاحية (اختياري)            │
│  [أضف كلمة... +]                        │
│  [كلمة1 ×] [كلمة2 ×] [كلمة3 ×]        │
└─────────────────────────────────────────┘
```

---

### Tab 3: التسعير والكمية (Pricing & Quantity)

| # | الحقل | النوع | مطلوب؟ | Default | ملاحظات |
|---|-------|-------|--------|---------|----------|
| 1 | `price` | Number | ✅ نعم | — | السعر (أكبر من 0) |
| 2 | `compare_price` | Number | ❌ اختياري | — | سعر قبل الخصم |
| 3 | `cost` | Number | ❌ اختياري | — | التكلفة |
| 4 | `quantity` | Number | ✅ نعم | `0` | الكمية |
| 5 | `sale_price` | Number | ❌ اختياري | — | سعر التخفيض |
| 6 | `sale_start_date` | Date | ❌ اختياري | — | بداية التخفيض |
| 7 | `sale_end_date` | Date | ❌ اختياري | — | نهاية التخفيض |

**UI:**
```
┌─────────────────────────────────────────┐
│  Tab 3: التسعير والكمية                 │
├─────────────────────────────────────────┤
│  السعر (EGP) *                          │
│  [______________] ج.م                   │
│                                         │
│  سعر قبل الخصم (اختياري)                │
│  [______________] ج.م                   │
│                                         │
│  التكلفة (اختياري)                      │
│  [______________] ج.م                   │
│                                         │
│  الكمية *                               │
│  [______________]                       │
│                                         │
│  ─── تخفيض (اختياري) ───                │
│  سعر التخفيض:      [______________]     │
│  من تاريخ:         [__/__/____]         │
│  إلى تاريخ:        [__/__/____]         │
└─────────────────────────────────────────┘
```

---

### Tab 4: الشحن والأبعاد (Shipping & Dimensions)

| # | الحقل | النوع | مطلوب؟ | Default | ملاحظات |
|---|-------|-------|--------|---------|----------|
| 1 | `condition` | Select | ✅ نعم | `New` | حالة المنتج |
| 2 | `fulfillment_channel` | Radio | ✅ نعم | `MFN` | MFN / AFN |
| 3 | `handling_time` | Number | ❌ اختياري | `1` | أيام التجهيز |
| 4 | `package_dimensions.length` | Number | ✅ نعم | `25` | طول الباكج (سم) |
| 5 | `package_dimensions.width` | Number | ✅ نعم | `10` | عرض الباكج (سم) |
| 6 | `package_dimensions.height` | Number | ✅ نعم | `15` | ارتفاع الباكج (سم) |
| 7 | `item_weight` | Number | ✅ نعم | `0.5` | وزن المنتج (كجم) |
| 8 | `package_weight` | Number | ✅ نعم | `0.7` | وزن الباكج (كجم) |
| 9 | `number_of_boxes` | Number | ✅ نعم | `1` | عدد الصناديق |
| 10 | `package_quantity` | Number | ❌ اختياري | `1` | عدد القطع بالباكج |

**UI:**
```
┌─────────────────────────────────────────┐
│  Tab 4: الشحن والأبعاد                  │
├─────────────────────────────────────────┤
│  حالة المنتج *                          │
│  [جديد ▼]                              │
│                                         │
│  قناة الشحن *                           │
│  ○ الشحن على البائع (MFN)              │
│  ○ الشحن على Amazon (FBA)              │
│                                         │
│  أيام التجهيز (اختياري)                │
│  [1______________] يوم                 │
│                                         │
│  ─── أبعاد الباكج (سم) * ───            │
│  الطول: [25____]  العرض: [10____]      │
│  الارتفاع: [15____]                    │
│                                         │
│  ─── الأوزان (كجم) * ───                │
│  وزن المنتج: [0.5____]                 │
│  وزن الباكج: [0.7____]                 │
│                                         │
│  عدد الصناديق *     عدد القطع بالباكج   │
│  [1______________]  [1______________]  │
└─────────────────────────────────────────┘
```

---

### Tab 5: الصور والإرسال (Media & Submit)

| # | الحقل | النوع | مطلوب؟ | Default | ملاحظات |
|---|-------|-------|--------|---------|----------|
| 1 | `main_image` | Upload | ✅ نعم | — | الصورة الرئيسية |
| 2 | `extra_images` | Upload(8) | ❌ اختياري | — | 8 صور فرعية |
| 3 | `listing_copies` | Number | ❌ اختياري | `1` | عدد النسخ (1-50) |

**UI:**
```
┌─────────────────────────────────────────┐
│  Tab 5: الصور والإرسال                  │
├─────────────────────────────────────────┤
│  الصورة الرئيسية *                      │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │      [📁 اختر صورة]               │  │
│  │      أو اسحب وأفلت               │  │
│  │                                   │  │
│  │      1000×1000 بكسل على الأقل    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  صور إضافية (حتى 8 صور - اختياري)       │
│  [📁 +] [📁 +] [📁 +] [📁 +]           │
│  [📁 +] [📁 +] [📁 +] [📁 +]           │
│                                         │
│  ─────────────────────────────────────  │
│  عدد النسخ (اختياري): [1____] (1-50)   │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  [💾 حفظ في المخزون]              │  │
│  │  [🚀 حفظ وإرسال لـ Amazon]        │  │
│  │  [👁️ معاينة Amazon Feed]         │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 🔧 الأكواد المطلوبة

### 1. تحديث القوائم المنسدلة (Constants)

```typescript
// src/pages/products/ProductCreatePage.tsx — Constants

const PRODUCT_TYPES = [
  { value: 'HOME_ORGANIZERS_AND_STORAGE', label: 'أدوات تنظيم وتخزين المنزل' },
  { value: 'BABY_PRODUCT', label: 'منتجات أطفال' },
  { value: 'APPAREL', label: 'ملابس وأزياء' },
]

const BROWSE_NODES = [
  { value: '21863799031', label: 'المنزل والمطبخ > التخزين والتنظيم المنزلي' },
  { value: '21863899031', label: 'المنزل والمطبخ > سلال وصناديق التخزين' },
  { value: '21863898031', label: 'المنزل والمطبخ > خزائن التخزين والملابس' },
  // ... add more from temp.txt
]

const CONDITIONS = [
  { value: 'New', label: 'جديد' },
  { value: 'New - Open Box', label: 'جديد - علبة مفتوحة' },
  { value: 'Used - Like New', label: 'مستعمل - كالجديد' },
]

const COUNTRIES = [
  { value: 'CN', label: '🇨🇳 الصين' },
  { value: 'EG', label: '🇪🇬 مصر' },
  { value: 'TR', label: '🇹🇷 تركيا' },
  { value: 'IN', label: '🇮🇳 الهند' },
]

const UNIT_TYPES = [
  { value: 'count', label: 'عدد' },
  { value: 'grams', label: 'جرام' },
  { value: 'kilograms', label: 'كيلوجرام' },
  { value: 'pieces', label: 'قطعة' },
]
```

### 2. State Management

```typescript
// Required fields (Tab 1 + Tab 2 + Tab 3 + Tab 4)
const [required, setRequired] = useState({
  // Tab 1
  name_ar: '',
  name_en: '',
  product_type: 'HOME_ORGANIZERS_AND_STORAGE',
  id_type: 'EAN' as 'EAN' | 'UPC' | 'ASIN' | 'EXEMPT',
  ean: '',
  brand: 'Generic',
  model_number: '',
  manufacturer: 'Generic',
  country_of_origin: 'CN',
  
  // Tab 2
  description_ar: '',
  description_en: '',
  bullet_points: ['', '', '', '', ''],
  browse_node_id: '21863799031',
  included_components: '',
  unit_count: '1',
  unit_count_type: 'count',
  
  // Tab 3
  price: '',
  quantity: '0',
  
  // Tab 4
  condition: 'New',
  fulfillment_channel: 'MFN',
  package_length: '25',
  package_width: '10',
  package_height: '15',
  item_weight: '0.5',
  package_weight: '0.7',
  number_of_boxes: '1',
});

// Optional fields
const [optional, setOptional] = useState({
  keywords: [] as string[],
  material: '',
  compare_price: '',
  cost: '',
  sale_price: '',
  sale_start_date: '',
  sale_end_date: '',
  handling_time: '1',
  package_quantity: '1',
});

// Media
const [mainImage, setMainImage] = useState<string>('')
const [extraImages, setExtraImages] = useState<string[]>([])
const [listingCopies, setListingCopies] = useState(1)
```

### 3. Validation Function

```typescript
const validate = (): { valid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  // Tab 1
  if (required.name_ar.trim().length < 5) errors.push('اسم المنتج بالعربي لازم 5 أحرف على الأقل')
  if (required.name_en.trim().length < 5) errors.push('اسم المنتج بالإنجليزي لازم 5 أحرف على الأقل')
  if (required.id_type !== 'EXEMPT' && required.ean.length !== 13) errors.push('الباركود لازم 13 رقم')
  
  // Tab 2
  if (required.description_ar.trim().length < 10) errors.push('الوصف بالعربي لازم 10 أحرف على الأقل')
  if (required.description_en.trim().length < 10) errors.push('الوصف بالإنجليزي لازم 10 أحرف على الأقل')
  
  // Tab 3
  if (!required.price || parseFloat(required.price) <= 0) errors.push('السعر لازم يكون أكبر من صفر')
  
  // Tab 5
  if (!mainImage) errors.push('لازم ترفع صورة رئيسية')
  
  return { valid: errors.length === 0, errors }
}
```

### 4. Submit Handler — Save to Local DB

```typescript
const handleSave = async () => {
  const { valid, errors } = validate()
  if (!valid) {
    toast.error(errors.join('\n'))
    return
  }
  
  const payload = {
    // Basic info
    sku: `AUTO-${Date.now()}`,
    name: required.name_en.trim(),
    name_ar: required.name_ar.trim(),
    name_en: required.name_en.trim(),
    brand: required.brand,
    price: parseFloat(required.price),
    quantity: parseInt(required.quantity),
    
    // Product type & condition
    product_type: required.product_type,
    condition: required.condition,
    fulfillment_channel: required.fulfillment_channel,
    
    // Barcode
    ean: required.id_type === 'EAN' ? required.ean : '',
    upc: required.id_type === 'UPC' ? required.ean : '',
    
    // Description
    description: required.description_en.trim(),
    description_ar: required.description_ar.trim(),
    bullet_points: required.bullet_points.filter(bp => bp.trim().length > 0),
    
    // Manufacturer info
    manufacturer: required.manufacturer,
    model_number: required.model_number,
    country_of_origin: required.country_of_origin,
    
    // Browse node
    browse_node_id: required.browse_node_id,
    
    // Dimensions
    dimensions: {
      length: parseFloat(required.package_length),
      width: parseFloat(required.package_width),
      height: parseFloat(required.package_height),
      unit: 'centimeters',
    },
    
    // Weight
    weight: parseFloat(required.item_weight),
    
    // Additional
    number_of_boxes: parseInt(required.number_of_boxes),
    unit_count: { value: parseFloat(required.unit_count), type: required.unit_count_type },
    included_components: required.included_components,
    
    // Pricing
    compare_price: optional.compare_price ? parseFloat(optional.compare_price) : undefined,
    cost: optional.cost ? parseFloat(optional.cost) : undefined,
    sale_price: optional.sale_price ? parseFloat(optional.sale_price) : undefined,
    
    // Media
    images: [mainImage, ...extraImages].filter(Boolean),
  }
  
  try {
    const response = await productsApi.create(payload)
    toast.success('✅ تم حفظ المنتج!')
    
    // If "Save & Submit to Amazon" was clicked
    if (submitToAmazon) {
      await productsApi.submitToAmazon(response.data.id)
      toast.success('🚀 تم إرسال المنتج لـ Amazon!')
    }
    
    navigate('/products')
  } catch (error: any) {
    toast.error('فشل الحفظ: ' + (error.response?.data?.detail || error.message))
  }
}
```

### 5. Backend Endpoint — Submit to Amazon

هذا endpoint موجود بالفعل من Phase 1:

```
POST /api/v1/sp-api/submit/{product_id}
```

---

## 📋 Checklist للمهندس

بعد التنفيذ، تأكد من:

- [ ] الصفحة فيها 5 tabs شاملة
- [ ] كل الـ 29 حقل مطلوب موجودين
- [ ] Validation مخفف (مش صارم)
- [ ] Auto-fill defaults شغال (brand=Generic, condition=New, etc.)
- [ ] رفع الصور شغال (رئيسية + 8 فرعية)
- [ ] زر "حفظ في المخزون" بيحفظ في الـ DB
- [ ] زر "حفظ وإرسال لـ Amazon" بيحفظ و يبعث لـ SP-API
- [ ] زر "معاينة Amazon Feed" بيعرض البيانات قبل الإرسال
- [ ] رسالة خطأ واضحة لو validation فشل
- [ ] Toast notifications شغالة
- [ ] Responsive design على الموبايل

---

## ⚠️ ملاحظات مهمة

1. **Auto-fill Defaults** — خلّي الصفحة مليانة قيم افتراضية عشان المستخدم مش محتامل يملأ كل حاجة:
   ```
   brand: Generic
   condition: New
   fulfillment_channel: MFN
   country_of_origin: CN
   number_of_boxes: 1
   package_quantity: 1
   handling_time: 1
   unit_count: 1
   unit_count_type: count
   ```

2. **Validation مخفف** — السماح بـ:
   - صور اختيارية مؤقتاً
   - أسماء أقصر (3 أحرف بدل 5)
   - أوصاف أقصر (5 أحرف بدل 10)

3. **Browse Node Dropdown** — لازم يكون فيه قائمة منسدلة بكل الفئات من `Data/temp.txt`

---

## 🔴 توجيهات معمارية ملزمة من القائد التقني (تُنفذ حرفياً قبل البدء)

### 1. القيم الافتراضية الصارمة (Strict Defaults)
بما أننا نستخدم "Validation مخفف" لراحة المستخدم، فمن **الممنوع** إرسال `null` أو `undefined` للحقول الإجبارية الـ 29 المطلوبة من Amazon SP-API. 

**القاعدة:** إذا كان الحقل مخفياً أو اختيارياً للمستخدم، يجب على كود الـ Frontend حقن **قيم افتراضية صالحة** في الـ Payload النهائي قبل الإرسال:

```typescript
const buildFinalPayload = (formData: FormData) => ({
  ...formData,
  // Strict defaults for Amazon's 29 required fields
  brand: formData.brand || "Generic",
  condition: formData.condition || "New",
  country_of_origin: formData.country_of_origin || "CN",
  number_of_boxes: formData.number_of_boxes || 1,
  package_quantity: formData.package_quantity || 1,
  handling_time: formData.handling_time || 1,
  unit_count: formData.unit_count || 1,
  unit_count_type: formData.unit_count_type || "count",
  item_weight: formData.item_weight || 0.5,
  package_weight: formData.package_weight || 0.7,
  package_length: formData.package_length || 25,
  package_width: formData.package_width || 10,
  package_height: formData.package_height || 15,
})
```

### 2. منطق الـ Submit — ممنوع رسالة نجاح نهائي
في Phase 1 أسسنا أن أمازون ترد بـ `ACCEPTED` كاستلام مبدئي، وبعدين بيتم عمل `Polling` في الخلفية لمدة 5 دقائق لمعرفة هل المنتج اتقبل فعلياً (`ACTIVE`) ولا اترفض (`INVALID`).

**الممنوعات:**
- ❌ `toast.success('🚀 تم إرسال المنتج لـ Amazon!')`
- ❌ `navigate('/products')`

**المطلوب:**
- ✅ `toast.info('⏳ تم حفظ المنتج وإرسال الطلب لأمازون. جاري المعالجة...')`
- ✅ `navigate('/listings')` — عشان المستخدم يتابع حالة الـ Polling

```typescript
// الصحيح:
const handleSubmitToAmazon = async () => {
  await productsApi.submitToAmazon(productId)
  toast.info('⏳ تم الاستلام — جاري المعالجة لدى أمازون')
  navigate('/listings') // NOT /products!
}
```

### 3. الفصل المعماري — الـ Frontend مش شغل أمازون
الـ Frontend **ماينفعش** يكون عنده أي فكرة عن تعقيدات قاموس أمازون (`ar_AE`, `attributeProperties`, `item_package_dimensions`).

**القاعدة:**
- ✅ الـ Frontend بيبعت JSON بسيط ومسطح يتطابق مع الـ `Pydantic Schema` بتاعة الباك إند
- ✅ الباك إند (`sp_api_client.py`) هو اللي بيترجم ويرسل لـ Amazon

```typescript
// الـ Frontend بيبعت ده (بسيط ومسطح):
{
  "name": "Electric Hand Mixer",
  "brand": "Generic",
  "price": 350,
  "quantity": 25,
  "ean": "1245768907654",
  // ... simple fields
}

// الباك إند بيحول ده لـ (معقد ومتداخل):
{
  "productType": "HOME_ORGANIZERS_AND_STORAGE",
  "requirements": "LISTING",
  "attributes": {
    "item_name": [{"value": "Electric Hand Mixer", "language_tag": "ar_AE"}],
    // ... 29 required fields with correct nested structure
  }
}
```

### 4. القوائم المنسدلة — ممنوع الـ Hardcoding
كل الـ Dropdowns (أنواع المنتجات، الفئات، بلدان المنشأ) لازم تتحمل من:
- ✅ ملف `constants.ts` مركزي مستقل (`src/constants/amazon.ts`)
- ✅ أو من الباك إند عبر `GET /api/v1/sp-api/schema/{product_type}`

**ممنوع** كتابة القيم يدوياً جوا الـ Components.

---

## 📋 Checklist النهائية للمهندس (بعد التعديلات)

بعد التنفيذ، تأكد من:

- [ ] الصفحة فيها 5 tabs شاملة
- [ ] كل الـ 29 حقل مطلوب موجودين (لكن UI مخفف)
- [ ] **Strict Defaults** مطبقة — مفيش `null` أو `undefined` في الـ Payload
- [ ] Auto-fill defaults شغال (brand=Generic, condition=New, etc.)
- [ ] رفع الصور شغال (رئيسية + 8 فرعية)
- [ ] زر "حفظ في المخزون" بيحفظ في الـ DB
- [ ] زر "حفظ وإرسال لـ Amazon" بيحفظ و يبعث لـ SP-API
- [ ] **رسالة الـ Toast**: `⏳ تم الاستلام — جاري المعالجة لدى أمازون` (مش نجاح أخضر!)
- [ ] **الـ Redirect** بيروح لـ `/listings` (مش `/products`!)
- [ ] الـ Frontend مش شايل أي حاجة خاصة بـ Amazon structure (ar_AE, attributeProperties)
- [ ] القوائم المنسدلة مش Hardcoded جوا الـ Components
- [ ] رسالة خطأ واضحة لو validation فشل
- [ ] Toast notifications شغالة
- [ ] Responsive design على الموبايل

---

**انطلق! 🚀**
