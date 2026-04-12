import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Package, DollarSign, Image, Save, Loader2, AlertTriangle, CheckCircle, Search } from 'lucide-react'
import { useCreateProduct } from '@/api/hooks'
import { productsApi } from '@/api/endpoints'
import { MediaUploader } from '@/components/common/MediaUploader'
import toast from 'react-hot-toast'

// ==================== ثابتات القوائم المنسدلة ====================

const PRODUCT_TYPES = [
  { value: 'HOME_ORGANIZERS_AND_STORAGE', label: 'أدوات تنظيم وتخزين المنزل' },
  { value: 'BABY_PRODUCT', label: 'منتجات أطفال' },
  { value: 'APPAREL', label: 'ملابس وأزياء' },
]

const CONDITIONS = [
  { value: 'New', label: 'جديد' },
  { value: 'New - Open Box', label: 'جديد - علبة مفتوحة' },
  { value: 'New - OEM', label: 'جديد - مصنع' },
  { value: 'Refurbished', label: 'مُجدد' },
  { value: 'Used - Like New', label: 'مستعمل - كالجديد' },
  { value: 'Used - Very Good', label: 'مستعمل - جيد جداً' },
  { value: 'Used - Good', label: 'مستعمل - جيد' },
  { value: 'Used - Acceptable', label: 'مستعمل - مقبول' },
]

const FULFILLMENT = [
  { value: 'MFN', label: 'الشحن على البائع (MFN)' },
  { value: 'AFN', label: 'الشحن على Amazon - FBA' },
]

const ID_TYPES = [
  { value: 'UPC', label: 'UPC (12 رقم)' },
  { value: 'EAN', label: 'EAN (13 رقم)' },
  { value: 'ASIN', label: 'ASIN (Amazon)' },
]

const COUNTRIES = [
  { value: 'CN', label: '🇨🇳 الصين' },
  { value: 'EG', label: '🇪🇬 مصر' },
  { value: 'TR', label: '🇹🇷 تركيا' },
  { value: 'IN', label: '🇮🇳 الهند' },
  { value: 'DE', label: '🇩🇪 ألمانيا' },
  { value: 'US', label: '🇺🇸 أمريكا' },
  { value: 'GB', label: '🇬🇧 بريطانيا' },
]

const DIMENSION_UNITS = [
  { value: 'Centimeters', label: 'سم' },
  { value: 'Inches', label: 'بوصة' },
]

const WEIGHT_UNITS = [
  { value: 'Kilograms', label: 'كجم' },
  { value: 'Grams', label: 'جرام' },
  { value: 'Pounds', label: 'رطل' },
]

// ==================== أنواع البيانات ====================

interface RequiredFields {
  name: string
  product_type: string
  id_type: string
  product_id: string
  gtin_exempt: boolean
  price: string
  quantity: string
  description: string
}

interface OptionalFields {
  brand: string
  condition: string
  fulfillment_channel: string
  model_number: string
  manufacturer: string
  country_of_origin: string
  weight: string
  weight_unit: string
  length: string
  width: string
  height: string
  dimension_unit: string
}

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const createMutation = useCreateProduct()

  // الصفحات الثلاث
  const [page, setPage] = useState(1)

  // بيانات إجبارية
  const [required, setRequired] = useState<RequiredFields>({
    name: '',
    product_type: 'HOME_ORGANIZERS_AND_STORAGE',
    id_type: 'EAN',
    product_id: '',
    gtin_exempt: false,
    price: '',
    quantity: '0',
    description: '',
  })

  // بيانات اختيارية
  const [optional, setOptional] = useState<OptionalFields>({
    brand: 'Generic',
    condition: 'New',
    fulfillment_channel: 'MFN',
    model_number: '',
    manufacturer: '',
    country_of_origin: 'CN',
    weight: '',
    weight_unit: 'Kilograms',
    length: '',
    width: '',
    height: '',
    dimension_unit: 'Centimeters',
  })

  // صور وعدد الإعلانات
  const [images, setImages] = useState<string[]>([])
  const [listingCopies, setListingCopies] = useState(1)

  // حالة البحث
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupResult, setLookupResult] = useState<{ available: boolean; reason: string; asin?: string; title?: string } | null>(null)

  // ==================== دوال المساعدة ====================

  const updateRequired = (field: keyof RequiredFields, value: any) =>
    setRequired(prev => ({ ...prev, [field]: value }))

  const updateOptional = (field: keyof OptionalFields, value: any) =>
    setOptional(prev => ({ ...prev, [field]: value }))

  // بحث عن المنتج في Amazon
  const handleLookup = async () => {
    if (required.gtin_exempt) {
      setLookupResult({ available: true, reason: 'معفي من الباركود - تخطي البحث' })
      return
    }
    if (!required.product_id) {
      toast.error('ادخل رقم الباركود أو ASIN الأول')
      return
    }

    setLookingUp(true)
    setLookupResult(null)

    try {
      const { data } = await productsApi.lookup(required.product_id, required.id_type)
      setLookupResult(data)

      if (!data.available) {
        toast.error(`المنتج موجود على Amazon!\nASIN: ${data.asin}\n${data.title}`)
      } else {
        toast.success('المنتج مش موجود على Amazon - يمكنك إضافته')
      }
    } catch (error: any) {
      setLookupResult({ available: true, reason: `فشل البحث: ${error.message}` })
    } finally {
      setLookingUp(false)
    }
  }

  // حفظ المنتج
  const handleSubmit = async () => {
    // تحقق إجباري
    if (!required.name.trim() || required.name.length < 5) {
      toast.error('اسم المنتج لازم 5 أحرف على الأقل')
      return
    }
    if (!required.description.trim() || required.description.length < 10) {
      toast.error('الوصف لازم 10 أحرف على الأقل')
      return
    }
    if (!required.price || parseFloat(required.price) <= 0) {
      toast.error('السعر لازم يكون أكبر من صفر')
      return
    }
    if (!required.gtin_exempt && !required.product_id) {
      toast.error('لازم تدخل UPC/EAN/ASIN أو تختار "معفي"')
      return
    }

    // بحث تلقائي قبل الحفظ
    if (!lookupResult || lookupResult.available === false) {
      await handleLookup()
      if (lookupResult?.available === false) return
    }

    // بناء payload
    const payload: Record<string, unknown> = {
      sku: `AUTO-${Date.now()}`,
      seller_id: '',  // هيتحط من الـ hook
      name: required.name.trim(),
      brand: optional.brand || 'Generic',
      price: parseFloat(required.price),
      quantity: parseInt(required.quantity) || 0,
      description: required.description.trim(),
      product_type: required.product_type,
      condition: optional.condition,
      fulfillment_channel: optional.fulfillment_channel,
      country_of_origin: optional.country_of_origin,
      listing_copies: listingCopies,
      bullet_points: required.description.split(/[.\n]/).filter((s: string) => s.trim().length > 10).slice(0, 5),
      images: images,
      attributes: {
        model_number: optional.model_number || undefined,
        manufacturer: optional.manufacturer || undefined,
        weight: optional.weight ? parseFloat(optional.weight) : undefined,
        weight_unit: optional.weight_unit || undefined,
        dimensions: optional.length && optional.width && optional.height
          ? {
              length: parseFloat(optional.length),
              width: parseFloat(optional.width),
              height: parseFloat(optional.height),
              unit: optional.dimension_unit,
            }
          : undefined,
      },
    }

    // UPC/EAN/ASIN
    if (!required.gtin_exempt) {
      if (required.id_type === 'UPC') payload.upc = required.product_id
      else if (required.id_type === 'EAN') payload.ean = required.product_id
      else if (required.id_type === 'ASIN') {
        payload.attributes = { ...payload.attributes, asin: required.product_id }
      }
    }

    try {
      await createMutation.mutateAsync(payload as any)
      toast.success('تم حفظ المنتج وإرساله لـ Amazon!')
      navigate('/products')
    } catch (error: any) {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join('\n'))
      } else if (typeof detail === 'string') {
        toast.error(detail)
      } else {
        toast.error('فشل في حفظ البيانات')
      }
    }
  }

  // ==================== مؤشرات الصفحات ====================

  const StepIndicator = () => (
    <div className="flex items-center justify-center gap-2 mb-6">
      {[
        { n: 1, label: 'البيانات الأساسية' },
        { n: 2, label: 'بيانات إضافية' },
        { n: 3, label: 'الصور والإعلانات' },
      ].map(step => (
        <button
          key={step.n}
          onClick={() => setPage(step.n)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
            ${page === step.n
              ? 'bg-blue-600 text-white shadow-lg'
              : page > step.n
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
            }`}
        >
          {page > step.n ? <CheckCircle className="w-4 h-4" /> : <span>{step.n}</span>}
          <span>{step.label}</span>
        </button>
      ))}
    </div>
  )

  // ==================== حقل إدخال ====================

  const Field = ({
    label, children, required, error,
  }: { label: string; children: React.ReactNode; required?: boolean; error?: string }) => (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
        {required && <span className="text-red-500 mr-1">*</span>}
      </label>
      {children}
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  )

  const Select = ({
    value, onChange, options,
  }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) => (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
    >
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  )

  const Input = ({
    value, onChange, type = 'text', placeholder, disabled,
  }: { value: string; onChange: (v: string) => void; type?: string; placeholder?: string; disabled?: boolean }) => (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
    />
  )

  // ==================== الصفحات الثلاث ====================

  const renderPage1 = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <Package className="w-5 h-5" />
        البيانات الأساسية (إجبارية)
      </h2>

      <Field label="اسم المنتج" required>
        <Input value={required.name} onChange={v => updateRequired('name', v)} placeholder="مثال: منظم ملابس داخلي 6 قطع" />
        {required.name.length > 0 && required.name.length < 5 && (
          <p className="text-amber-500 text-xs mt-1">الاسم لازم 5 أحرف على الأقل ({required.name.length}/5)</p>
        )}
      </Field>

      <Field label="نوع المنتج" required>
        <Select value={required.product_type} onChange={v => updateRequired('product_type', v)} options={PRODUCT_TYPES} />
      </Field>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="نوع المعرف" required>
          <Select value={required.id_type} onChange={v => updateRequired('id_type', v)} options={ID_TYPES} />
        </Field>

        <Field label={required.id_type === 'ASIN' ? 'ASIN' : required.id_type === 'UPC' ? 'UPC (12 رقم)' : 'EAN (13 رقم)'}>
          <div className="flex gap-2">
            <Input
              value={required.product_id}
              onChange={v => updateRequired('product_id', v)}
              placeholder={required.id_type === 'UPC' ? '12 رقم' : required.id_type === 'EAN' ? '13 رقم' : 'B0XXXXXXXX'}
              disabled={required.gtin_exempt}
            />
            <button
              onClick={handleLookup}
              disabled={lookingUp || required.gtin_exempt}
              className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
            >
              {lookingUp ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
          </div>
        </Field>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={required.gtin_exempt}
          onChange={e => { updateRequired('gtin_exempt', e.target.checked); if (e.target.checked) { updateRequired('product_id', ''); setLookupResult(null) } }}
          className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-700 dark:text-gray-300">معفي من الباركود (GTIN Exempt)</span>
      </label>

      {lookupResult && (
        <div className={`p-3 rounded-lg flex items-start gap-2 ${
          lookupResult.available
            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
        }`}>
          {lookupResult.available ? <CheckCircle className="w-5 h-5 shrink-0" /> : <AlertTriangle className="w-5 h-5 shrink-0" />}
          <div className="text-sm">
            <p className="font-medium">{lookupResult.reason}</p>
            {lookupResult.title && <p className="text-xs mt-1 opacity-75">{lookupResult.title}</p>}
            {lookupResult.asin && <p className="text-xs mt-1 opacity-75">ASIN: {lookupResult.asin}</p>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="السعر (EGP)" required>
          <Input type="number" value={required.price} onChange={v => updateRequired('price', v)} placeholder="0.00" />
        </Field>

        <Field label="الكمية" required>
          <Input type="number" value={required.quantity} onChange={v => updateRequired('quantity', v)} placeholder="0" />
        </Field>
      </div>

      <Field label="وصف المنتج" required>
        <textarea
          value={required.description}
          onChange={e => updateRequired('description', e.target.value)}
          placeholder="وصف تفصيلي للمنتج... (هيتم استخراج نقاط البيع تلقائياً)"
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 resize-none"
        />
        {required.description.length > 0 && required.description.length < 10 && (
          <p className="text-amber-500 text-xs mt-1">الوصف لازم 10 أحرف على الأقل ({required.description.length}/10)</p>
        )}
      </Field>
    </div>
  )

  const renderPage2 = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <DollarSign className="w-5 h-5" />
        بيانات إضافية (اختيارية)
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="البراند">
          <Input value={optional.brand} onChange={v => updateOptional('brand', v)} placeholder="Generic" />
        </Field>

        <Field label="حالة المنتج">
          <Select value={optional.condition} onChange={v => updateOptional('condition', v)} options={CONDITIONS} />
        </Field>

        <Field label="طريقة الشحن">
          <Select value={optional.fulfillment_channel} onChange={v => updateOptional('fulfillment_channel', v)} options={FULFILLMENT} />
        </Field>

        <Field label="بلد المنشأ">
          <Select value={optional.country_of_origin} onChange={v => updateOptional('country_of_origin', v)} options={COUNTRIES} />
        </Field>

        <Field label="رقم الموديل">
          <Input value={optional.model_number} onChange={v => updateOptional('model_number', v)} placeholder="اختياري" />
        </Field>

        <Field label="المصنع">
          <Input value={optional.manufacturer} onChange={v => updateOptional('manufacturer', v)} placeholder="اختياري" />
        </Field>
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">الوزن</h3>
        <div className="grid grid-cols-2 gap-4">
          <Input type="number" value={optional.weight} onChange={v => updateOptional('weight', v)} placeholder="0.0" />
          <Select value={optional.weight_unit} onChange={v => updateOptional('weight_unit', v)} options={WEIGHT_UNITS} />
        </div>
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">الأبعاد (طول × عرض × ارتفاع)</h3>
        <div className="grid grid-cols-4 gap-2">
          <Input type="number" value={optional.length} onChange={v => updateOptional('length', v)} placeholder="الطول" />
          <Input type="number" value={optional.width} onChange={v => updateOptional('width', v)} placeholder="العرض" />
          <Input type="number" value={optional.height} onChange={v => updateOptional('height', v)} placeholder="الارتفاع" />
          <Select value={optional.dimension_unit} onChange={v => updateOptional('dimension_unit', v)} options={DIMENSION_UNITS} />
        </div>
      </div>
    </div>
  )

  const renderPage3 = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <Image className="w-5 h-5" />
        الصور والإعلانات
      </h2>

      <Field label="صور المنتج">
        <MediaUploader
          images={images}
          onChange={setImages}
          maxImages={9}
        />
        <p className="text-xs text-gray-500 mt-1">الصورة الأولى هتكون الصورة الرئيسية. يوصى بـ 1000×1000 بكسل على الأقل.</p>
      </Field>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <Field label="عدد الإعلانات (نسخ من نفس المنتج)">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setListingCopies(Math.max(1, listingCopies - 1))}
              className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-lg font-bold hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              -
            </button>
            <span className="text-2xl font-bold w-12 text-center">{listingCopies}</span>
            <button
              onClick={() => setListingCopies(Math.min(50, listingCopies + 1))}
              className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-lg font-bold hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              +
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            لو عايز ترفع أكثر من إعلان لنفس المنتج (مثلاً ألوان مختلفة).
            كل إعلان هياخد SKU مختلف تلقائياً.
          </p>
        </Field>
      </div>
    </div>
  )

  // ==================== العرض الرئيسي ====================

  return (
    <div className="max-w-3xl mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">إضافة منتج جديد</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">أدخل بيانات المنتج وسيتم إرساله لـ Amazon تلقائياً</p>
      </div>

      <StepIndicator />

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        {page === 1 && renderPage1()}
        {page === 2 && renderPage2()}
        {page === 3 && renderPage3()}
      </div>

      <div className="flex justify-between mt-6">
        <button
          onClick={() => page > 1 ? setPage(page - 1) : navigate('/products')}
          className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
        >
          {page > 1 ? '→ السابق' : 'إلغاء'}
        </button>

        {page < 3 ? (
          <button
            onClick={() => setPage(page + 1)}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            التالي ←
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={createMutation.isPending}
            className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
          >
            {createMutation.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحفظ...</>
            ) : (
              <><Save className="w-4 h-4" /> حفظ وإرسال لـ Amazon</>
            )}
          </button>
        )}
      </div>
    </div>
  )
}
