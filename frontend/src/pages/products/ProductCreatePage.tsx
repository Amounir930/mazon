import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowRight, Package, DollarSign, Image, Save, Loader2, AlertTriangle, CheckCircle, Search, Upload, X, FileSpreadsheet, Eye, Download } from 'lucide-react'
import { useCreateProduct } from '@/api/hooks'
import { productsApi, imagesApi } from '@/api/endpoints'
import { generateTemplateExcel } from '@/services/excel_import_service'
import toast from 'react-hot-toast'
import * as XLSX from 'xlsx'

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
  name_en: string
  product_type: string
  id_type: string
  product_id: string
  gtin_exempt: boolean
  price: string
  quantity: string
  description: string
  description_en: string
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
  // حقول إضافية مطلوبة لـ Amazon
  handling_time: string
  package_quantity: string
  browse_node_id: string
  keywords: string
  material: string
  number_of_items: string
  unit_count: string
  unit_count_type: string
  target_audience: string
  sale_price: string
  compare_price: string
  cost: string
  sale_start_date: string
  sale_end_date: string
}

// ==================== مكونات UI منفصلة (BRA الـ component الرئيسي) ====================

// ✅ Input مستقل - مش بيتعرف كل مرة
const TextInput = ({
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

// ✅ Select مستقل
const SelectInput = ({
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

// ✅ Field wrapper مستقل
const Field = ({
  label, children, required: isRequired,
}: { label: string; children: React.ReactNode; required?: boolean }) => (
  <div className="space-y-1">
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
      {label}
      {isRequired && <span className="text-red-500 mr-1">*</span>}
    </label>
    {children}
  </div>
)

// ✅ StepIndicator مستقل
const StepIndicator = ({ currentPage, onNavigate }: { currentPage: number; onNavigate: (page: number) => void }) => (
  <div className="flex items-center justify-center gap-2 mb-6">
    {[
      { n: 1, label: 'البيانات الأساسية' },
      { n: 2, label: 'بيانات إضافية' },
      { n: 3, label: 'الصور والإعلانات' },
    ].map(step => (
      <button
        key={step.n}
        onClick={() => onNavigate(step.n)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
          ${currentPage === step.n
            ? 'bg-blue-600 text-white shadow-lg'
            : currentPage > step.n
              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
          }`}
      >
        {currentPage > step.n ? <CheckCircle className="w-4 h-4" /> : <span>{step.n}</span>}
        <span>{step.label}</span>
      </button>
    ))}
  </div>
)

// ==================== المكون الرئيسي ====================

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const createMutation = useCreateProduct()

  // Check if we're in "complete data" mode for an incomplete product
  const completeMode = (location.state as any)?.completeMode || false
  const editProduct = (location.state as any)?.editProduct as any

  const [page, setPage] = useState(1)

  // بيانات إجبارية
  const [required, setRequired] = useState<RequiredFields>({
    name: '',
    name_en: '',
    product_type: 'HOME_ORGANIZERS_AND_STORAGE',
    id_type: 'EAN',
    product_id: '',
    gtin_exempt: false,
    price: '',
    quantity: '0',
    description: '',
    description_en: '',
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
    handling_time: '1',
    package_quantity: '1',
    browse_node_id: '',
    keywords: '',
    material: '',
    number_of_items: '1',
    unit_count: '',
    unit_count_type: 'Count',
    target_audience: '',
    sale_price: '',
    compare_price: '',
    cost: '',
    sale_start_date: '',
    sale_end_date: '',
  })

  // صور (1 رئيسية + 8 فرعية) - URLs بعد الرفع
  const [mainImageUrl, setMainImageUrl] = useState<string>('')
  const [extraImageUrls, setExtraImageUrls] = useState<string[]>([])

  // حالة الرفع
  const [uploadingImages, setUploadingImages] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  // صورة مؤقتة للعرض (base64) قبل الرفع
  const [mainImagePreview, setMainImagePreview] = useState<string>('')

  // عدد الإعلانات
  const [listingCopiesStr, setListingCopiesStr] = useState('1')
  const listingCopies = parseInt(listingCopiesStr) || 1

  // حالة البحث
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupResult, setLookupResult] = useState<{ available: boolean; reason: string; asin?: string; title?: string } | null>(null)

  // حالة المعاينة
  const [showPreview, setShowPreview] = useState(false)
  const [previewData, setPreviewData] = useState<any[]>([])

  // Amazon Feed Preview
  const [showAmazonPreview, setShowAmazonPreview] = useState(false)
  const [amazonFeedData, setAmazonFeedData] = useState<any>(null)
  const [previewTab, setPreviewTab] = useState<'summary' | 'json' | 'xml'>('summary')
  const [previewLoading, setPreviewLoading] = useState(false)

  // حالة استيراد Excel
  const [showExcelImport, setShowExcelImport] = useState(false)
  const [excelData, setExcelData] = useState<any[] | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ==================== Edit/Complete Mode: Populate fields from existing product ====================
  useEffect(() => {
    if (editProduct) {
      // Populate required fields
      setRequired({
        name: editProduct.name_ar || editProduct.name || '',
        name_en: editProduct.name_en || editProduct.name || '',
        product_type: editProduct.product_type || 'HOME_ORGANIZERS_AND_STORAGE',
        id_type: editProduct.ean ? 'EAN' : editProduct.upc ? 'UPC' : 'EAN',
        product_id: editProduct.ean || editProduct.upc || '',
        gtin_exempt: !editProduct.ean && !editProduct.upc,
        price: String(editProduct.price || ''),
        quantity: String(editProduct.quantity || '0'),
        description: editProduct.description || '',
        description_en: editProduct.description_en || editProduct.description || '',
      })

      // Populate optional fields
      setOptional({
        brand: editProduct.brand || 'Generic',
        condition: editProduct.condition || 'New',
        fulfillment_channel: editProduct.fulfillment_channel || 'MFN',
        model_number: editProduct.model_number || '',
        manufacturer: editProduct.manufacturer || '',
        country_of_origin: editProduct.country_of_origin || 'CN',
        weight: String(editProduct.weight || ''),
        weight_unit: 'Kilograms',
        length: '',
        width: '',
        height: '',
        dimension_unit: 'Centimeters',
      })

      // Populate images from existing product
      if (editProduct.images && editProduct.images.length > 0) {
        const firstImg = editProduct.images[0]
        // لو URL كاملة أو relative path
        if (firstImg.startsWith('http') || firstImg.startsWith('/api/')) {
          setMainImageUrl(firstImg)
        } else {
          // لو relative path بدون /api
          setMainImageUrl(`/api/v1/images/static/${firstImg}`)
        }
        const restImgs = editProduct.images.slice(1, 9).map((img: string) =>
          img.startsWith('http') || img.startsWith('/api/') ? img : `/api/v1/images/static/${img}`
        )
        setExtraImageUrls(restImgs)
      }
    }
  }, [editProduct])

  // Calculate missing fields for edit/complete mode
  const isEditMode = !!editProduct
  const missingFields = useMemo(() => {
    if (!isEditMode) return []

    const missing: string[] = []
    if (!mainImageUrl && (!editProduct.images || editProduct.images.length === 0)) missing.push('صورة رئيسية')
    if (!required.product_id && !required.gtin_exempt) missing.push('باركود (UPC/EAN)')
    if (!optional.brand || optional.brand === 'Generic') missing.push('براند حقيقي')
    if (!required.product_type || required.product_type === 'HOME_ORGANIZERS_AND_STORAGE') missing.push('نوع المنتج')
    if (optional.brand === 'Generic') missing.push('براند (ليس Generic)')

    return missing
  }, [completeMode, editProduct, mainImageUrl, required, optional])

  // ==================== دوال مساعدة ====================

  const updateRequired = useCallback((field: keyof RequiredFields, value: string | boolean) =>
    setRequired(prev => ({ ...prev, [field]: value })), [])

  const updateOptional = useCallback((field: keyof OptionalFields, value: string) =>
    setOptional(prev => ({ ...prev, [field]: value })), [])

  // ==================== رفع الصور ====================

  // رفع الصورة الرئيسية
  const handleMainImageUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // عرض preview مؤقت
    const reader = new FileReader()
    reader.onload = () => setMainImagePreview(reader.result as string)
    reader.readAsDataURL(file)

    // رفع للسيرفر
    setUploadingImages(true)
    setUploadProgress(10)
    try {
      const { data } = await imagesApi.upload(file)
      setMainImageUrl(data.url)
      setUploadProgress(100)
      toast.success('✅ تم رفع الصورة الرئيسية')
    } catch (error: any) {
      toast.error('فشل رفع الصورة: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploadingImages(false)
    }
  }, [])

  // رفع صور فرعية
  const handleExtraImagesUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    const remaining = 8 - extraImageUrls.length
    const toAdd = Array.from(files).slice(0, remaining)

    setUploadingImages(true)
    let uploaded = 0

    for (const file of toAdd) {
      try {
        setUploadProgress(Math.round((uploaded / toAdd.length) * 100))
        const { data } = await imagesApi.upload(file)
        setExtraImageUrls(prev => [...prev, data.url])
        uploaded++
      } catch (error: any) {
        toast.error(`فشل رفع صورة: ${error.response?.data?.detail || error.message}`)
      }
    }

    setUploadProgress(100)
    setUploadingImages(false)
    if (uploaded > 0) toast.success(`✅ تم رفع ${uploaded} صورة`)
  }, [extraImageUrls.length])

  const removeMainImage = useCallback(() => { setMainImageUrl(''); setMainImagePreview('') }, [])
  const removeExtraImage = useCallback((idx: number) => setExtraImageUrls(prev => prev.filter((_, i) => i !== idx)), [])

  // بحث Amazon
  const handleLookup = useCallback(async () => {
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
  }, [required.product_id, required.id_type, required.gtin_exempt])

  // ==================== معاينة البيانات ====================

  const handlePreview = useCallback(() => {
    // نفس الـ validation زي الـ handleSubmit
    if (!required.name.trim() || required.name.length < 5) { toast.error('اسم المنتج لازم 5 أحرف'); return }
    if (!required.name_en.trim() || required.name_en.length < 5) { toast.error('اسم المنتج بالإنجليزي لازم 5 أحرف'); return }
    if (!required.description.trim() || required.description.length < 10) { toast.error('الوصف لازم 10 أحرف'); return }
    if (!required.description_en.trim() || required.description_en.length < 10) { toast.error('الوصف بالإنجليزي لازم 10 أحرف'); return }
    if (!required.price || parseFloat(required.price) <= 0) { toast.error('السعر لازم أكبر من صفر'); return }
    if (!mainImageUrl) { toast.error('لازم ترفع صورة رئيسية'); return }

    const basePayload: Record<string, unknown> = {
      name: required.name_en.trim(),
      name_ar: required.name.trim(),
      name_en: required.name_en.trim(),
      brand: optional.brand || 'Generic',
      price: parseFloat(required.price),
      quantity: Math.floor((parseInt(required.quantity) || 0) / listingCopies),
      product_type: required.product_type,
      condition: optional.condition,
      fulfillment_channel: optional.fulfillment_channel,
      country_of_origin: optional.country_of_origin,
      images: [mainImageUrl, ...extraImageUrls],
      description: required.description_en.trim(),
      description_ar: required.description.trim(),
      attributes: {
        model_number: optional.model_number || undefined,
        weight: optional.weight ? parseFloat(optional.weight) : undefined,
      },
    }

    const payloads: Record<string, unknown>[] = []
    for (let i = 1; i <= listingCopies; i++) {
      const suffix = listingCopies > 1 ? ` - Variant ${i}` : ''
      payloads.push({
        ...basePayload,
        sku: `AUTO-${Date.now()}-${i}`,
        name: `${required.name_en.trim()}${suffix}`,
        description: `${required.description_en.trim()}${suffix}`,
        description_ar: `${required.description.trim()}${suffix}`,
      })
    }

    setPreviewData(payloads)
    setShowPreview(true)
  }, [required, optional, mainImageUrl, extraImageUrls, listingCopies])

  // ==================== معاينة Amazon Feed ====================

  const handleAmazonPreview = useCallback(async () => {
    if (!required.name_en.trim() || !required.price) {
      toast.error('املأ البيانات الأساسية الأول')
      return
    }

    setPreviewLoading(true)
    setPreviewTab('summary')

    const payload = {
      sku: `AUTO-${Date.now()}`,
      name: required.name_en.trim(),
      name_ar: required.name.trim(),
      name_en: required.name_en.trim(),
      brand: optional.brand || 'Generic',
      price: parseFloat(required.price),
      quantity: parseInt(required.quantity) || 0,
      description: required.description_en.trim(),
      description_ar: required.description.trim(),
      description_en: required.description_en.trim(),
      product_type: required.product_type,
      condition: optional.condition,
      fulfillment_channel: optional.fulfillment_channel,
      country_of_origin: optional.country_of_origin,
      images: [mainImageUrl, ...extraImageUrls],
      upc: required.id_type === 'UPC' && !required.gtin_exempt ? required.product_id : undefined,
      ean: required.id_type === 'EAN' && !required.gtin_exempt ? required.product_id : undefined,
      bullet_points: required.description_en.split(/[.\n]/).filter((s: string) => s.trim().length > 10).slice(0, 5),
      keywords: optional.keywords ? optional.keywords.split(/\s+/).slice(0, 15) : [],
      handling_time: parseInt(optional.handling_time) || 1,
      package_quantity: parseInt(optional.package_quantity) || 1,
      browse_node_id: optional.browse_node_id || undefined,
      material: optional.material || undefined,
      number_of_items: parseInt(optional.number_of_items) || 1,
      target_audience: optional.target_audience || undefined,
      manufacturer: optional.manufacturer || undefined,
      model_number: optional.model_number || undefined,
      weight: optional.weight ? parseFloat(optional.weight) : undefined,
      dimensions: optional.length && optional.width && optional.height
        ? { length: parseFloat(optional.length), width: parseFloat(optional.width), height: parseFloat(optional.height), unit: optional.dimension_unit }
        : undefined,
      compare_price: optional.compare_price ? parseFloat(optional.compare_price) : undefined,
      cost: optional.cost ? parseFloat(optional.cost) : undefined,
      sale_price: optional.sale_price ? parseFloat(optional.sale_price) : undefined,
    }

    try {
      const { data } = await productsApi.previewFeed(payload as any)
      setAmazonFeedData(data)
      setShowAmazonPreview(true)
    } catch (error: any) {
      toast.error('فشل توليد المعاينة: ' + (error.response?.data?.detail || error.message))
    } finally {
      setPreviewLoading(false)
    }
  }, [required, optional, mainImageUrl, extraImageUrls])

  // ==================== حفظ المنتج ====================
  const handleSubmit = useCallback(async () => {
    if (!required.name.trim() || required.name.length < 5) {
      toast.error('اسم المنتج لازم 5 أحرف على الأقل')
      return
    }
    if (!required.name_en.trim() || required.name_en.length < 5) {
      toast.error('اسم المنتج بالإنجليزي لازم 5 أحرف على الأقل')
      return
    }
    if (!required.description.trim() || required.description.length < 10) {
      toast.error('الوصف (عربي) لازم 10 أحرف على الأقل')
      return
    }
    if (!required.description_en.trim() || required.description_en.length < 10) {
      toast.error('الوصف (English) لازم 10 أحرف على الأقل')
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
    if (!mainImageUrl) {
      toast.error('لازم ترفع صورة رئيسية واحدة على الأقل')
      return
    }

    // بناء payload أساسي
    const basePayload: Record<string, unknown> = {
      // seller_id هيتم تحديده تلقائياً من الـ backend
      name: required.name_en.trim(),
      name_ar: required.name.trim(),
      name_en: required.name_en.trim(),
      brand: optional.brand || 'Generic',
      price: parseFloat(required.price),
      quantity: Math.floor((parseInt(required.quantity) || 0) / listingCopies),
      product_type: required.product_type,
      condition: optional.condition,
      fulfillment_channel: optional.fulfillment_channel,
      country_of_origin: optional.country_of_origin,
      images: [mainImageUrl, ...extraImageUrls],
      // حقول Amazon الإضافية
      handling_time: parseInt(optional.handling_time) || 1,
      package_quantity: parseInt(optional.package_quantity) || 1,
      browse_node_id: optional.browse_node_id || undefined,
      keywords: optional.keywords ? optional.keywords.split(/\s+/).slice(0, 15) : [],
      material: optional.material || undefined,
      number_of_items: parseInt(optional.number_of_items) || 1,
      unit_count: optional.unit_count ? { value: parseFloat(optional.unit_count), type: optional.unit_count_type } : undefined,
      target_audience: optional.target_audience || undefined,
      // Pricing
      compare_price: optional.compare_price ? parseFloat(optional.compare_price) : undefined,
      cost: optional.cost ? parseFloat(optional.cost) : undefined,
      sale_price: optional.sale_price ? parseFloat(optional.sale_price) : undefined,
      sale_start_date: optional.sale_start_date || undefined,
      sale_end_date: optional.sale_end_date || undefined,
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

    if (!required.gtin_exempt) {
      if (required.id_type === 'UPC') basePayload.upc = required.product_id
      else if (required.id_type === 'EAN') basePayload.ean = required.product_id
      else if (required.id_type === 'ASIN') {
        basePayload.attributes = { ...basePayload.attributes, asin: required.product_id }
      }
    }

    // إنشاء نسخ متعددة باختلافات بسيطة
    const payloads: Record<string, unknown>[] = []

    for (let i = 1; i <= listingCopies; i++) {
      const variantSuffix = listingCopies > 1 ? ` - Variant ${i}` : ''
      const variantSuffixAr = listingCopies > 1 ? ` - نسخة ${i}` : ''

      const payload = {
        ...basePayload,
        sku: `AUTO-${Date.now()}-${i}`,
        name: `${required.name_en.trim()}${variantSuffix}`,
        description: `${required.description_en.trim()}${variantSuffix}`,
        description_ar: `${required.description.trim()}${variantSuffixAr}`,
        bullet_points: required.description_en.split(/[.\n]/).filter((s: string) => s.trim().length > 10).slice(0, 5),
      }

      payloads.push(payload)
    }

    try {
      if (listingCopies === 1) {
        // نسخة واحدة - إرسال عادي
        await createMutation.mutateAsync(payloads[0] as any)
        toast.success('✅ تم حفظ المنتج! يمكنك مزامنته لـ Amazon من صفحة المنتجات')
      } else {
        // نسخ متعددة - إرسال واحد واحد
        toast.loading(`جاري إنشاء ${listingCopies} منتج...`)
        let successCount = 0
        let failCount = 0

        for (let i = 0; i < payloads.length; i++) {
          try {
            await createMutation.mutateAsync(payloads[i] as any)
            successCount++
          } catch {
            failCount++
          }
        }

        toast.dismiss()
        if (failCount === 0) {
          toast.success(`✅ تم إنشاء ${successCount} منتج! يمكنك مزامنتها لـ Amazon من صفحة المنتجات`)
        } else {
          toast.error(`✅ نجح: ${successCount} | ❌ فشل: ${failCount}`)
        }
      }

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
  }, [required, optional, mainImageUrl, extraImageUrls, listingCopies, createMutation, navigate])

  // ==================== Excel Import ====================

  const handleExcelFile = useCallback(async (file: File) => {
    try {
      const buffer = await file.arrayBuffer()
      const workbook = XLSX.read(buffer, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const sheet = workbook.Sheets[sheetName]
      const data: any[] = XLSX.utils.sheet_to_json(sheet)

      if (data.length === 0) {
        toast.error('الملف فاضي')
        return
      }

      setExcelData(data)
      toast.success(`تم قراءة ${data.length} منتج من الملف - اختار واحد`)
    } catch (error: any) {
      toast.error(`فشل قراءة الملف: ${error.message}`)
    }
  }, [])

  const handleRowSelect = useCallback((rowIndex: number) => {
    if (!excelData) return
    const row = excelData[rowIndex]

    // خريطة شاملة لكل الأعمدة (إجبارية + اختيارية + جديدة)
    const mappings: Record<string, { target: 'required' | 'optional'; field: string }> = {
      // ===== إجبارية =====
      'اسم المنتج': { target: 'required', field: 'name' },
      'name': { target: 'required', field: 'name' },
      'product_name': { target: 'required', field: 'name' },
      'title': { target: 'required', field: 'name' },
      'الاسم': { target: 'required', field: 'name' },

      'اسم المنتج بالانجليزية': { target: 'required', field: 'name_en' },
      'name_en': { target: 'required', field: 'name_en' },
      'english_name': { target: 'required', field: 'name_en' },
      'اسم المنتج بالإنجليزي': { target: 'required', field: 'name_en' },

      'نوع المنتج': { target: 'required', field: 'product_type' },
      'product_type': { target: 'required', field: 'product_type' },
      'type': { target: 'required', field: 'product_type' },

      'نوع المعرف': { target: 'required', field: 'id_type' },
      'id_type': { target: 'required', field: 'id_type' },

      'الباركود': { target: 'required', field: 'product_id' },
      'product_id': { target: 'required', field: 'product_id' },
      'upc': { target: 'required', field: 'product_id' },
      'ean': { target: 'required', field: 'product_id' },
      'asin': { target: 'required', field: 'product_id' },
      'barcode': { target: 'required', field: 'product_id' },

      'السعر': { target: 'required', field: 'price' },
      'price': { target: 'required', field: 'price' },
      'amount': { target: 'required', field: 'price' },
      'cost': { target: 'required', field: 'price' },

      'الكمية': { target: 'required', field: 'quantity' },
      'quantity': { target: 'required', field: 'quantity' },
      'stock': { target: 'required', field: 'quantity' },
      'inventory': { target: 'required', field: 'quantity' },
      'المخزون': { target: 'required', field: 'quantity' },

      'الوصف': { target: 'required', field: 'description' },
      'description': { target: 'required', field: 'description' },
      'details': { target: 'required', field: 'description' },
      'تفاصيل': { target: 'required', field: 'description' },

      'الوصف بالانجليزية': { target: 'required', field: 'description_en' },
      'description_en': { target: 'required', field: 'description_en' },
      'english_description': { target: 'required', field: 'description_en' },

      // ===== اختيارية =====
      'البراند': { target: 'optional', field: 'brand' },
      'brand': { target: 'optional', field: 'brand' },

      'حالة المنتج': { target: 'optional', field: 'condition' },
      'condition': { target: 'optional', field: 'condition' },
      'status': { target: 'optional', field: 'condition' },

      'طريقة الشحن': { target: 'optional', field: 'fulfillment_channel' },
      'fulfillment': { target: 'optional', field: 'fulfillment_channel' },
      'fulfillment_channel': { target: 'optional', field: 'fulfillment_channel' },
      'shipping': { target: 'optional', field: 'fulfillment_channel' },

      'بلد المنشأ': { target: 'optional', field: 'country_of_origin' },
      'country': { target: 'optional', field: 'country_of_origin' },
      'country_of_origin': { target: 'optional', field: 'country_of_origin' },
      'origin': { target: 'optional', field: 'country_of_origin' },

      'رقم الموديل': { target: 'optional', field: 'model_number' },
      'model': { target: 'optional', field: 'model_number' },
      'model_number': { target: 'optional', field: 'model_number' },

      'المصنع': { target: 'optional', field: 'manufacturer' },
      'manufacturer': { target: 'optional', field: 'manufacturer' },

      'الوزن': { target: 'optional', field: 'weight' },
      'weight': { target: 'optional', field: 'weight' },

      'وحدة الوزن': { target: 'optional', field: 'weight_unit' },
      'weight_unit': { target: 'optional', field: 'weight_unit' },

      'الطول': { target: 'optional', field: 'length' },
      'length': { target: 'optional', field: 'length' },

      'العرض': { target: 'optional', field: 'width' },
      'width': { target: 'optional', field: 'width' },

      'الارتفاع': { target: 'optional', field: 'height' },
      'height': { target: 'optional', field: 'height' },

      'وحدة الأبعاد': { target: 'optional', field: 'dimension_unit' },
      'dimension_unit': { target: 'optional', field: 'dimension_unit' },

      // حقول جديدة
      'الخامة': { target: 'optional', field: 'material' },
      'material': { target: 'optional', field: 'material' },
      'الفئة المستهدفة': { target: 'optional', field: 'target_audience' },
      'target_audience': { target: 'optional', field: 'target_audience' },
      'وقت التجهيز': { target: 'optional', field: 'handling_time' },
      'handling_time': { target: 'optional', field: 'handling_time' },
      'عدد القطع': { target: 'optional', field: 'package_quantity' },
      'package_quantity': { target: 'optional', field: 'package_quantity' },
      'Browse Node': { target: 'optional', field: 'browse_node_id' },
      'browse_node_id': { target: 'optional', field: 'browse_node_id' },
      'كلمات البحث': { target: 'optional', field: 'keywords' },
      'keywords': { target: 'optional', field: 'keywords' },
      'search_terms': { target: 'optional', field: 'keywords' },
      'عدد العناصر': { target: 'optional', field: 'number_of_items' },
      'number_of_items': { target: 'optional', field: 'number_of_items' },
    }

    const newRequired = { ...required }
    const newOptional = { ...optional }

    for (const [excelCol, mapping] of Object.entries(mappings)) {
      const value = row[excelCol]
      if (value === undefined || value === null) continue
      const strValue = String(value).trim()
      if (!strValue) continue
      if (mapping.target === 'required') {
        (newRequired as any)[mapping.field] = strValue
      } else {
        (newOptional as any)[mapping.field] = strValue
      }
    }

    // صور
    const imageCol = row['الصور'] || row['images'] || row['image'] || row['صورة']
    if (imageCol) {
      const imageList = String(imageCol).split(',').map((u: string) => u.trim()).filter((u: string) => u)
      if (imageList.length > 0 && imageList[0]) {
        // لو URL مباشر - استخدمه
        if (imageList[0].startsWith('http')) {
          setMainImageUrl(imageList[0])
        }
        // لو base64 - اعرضه فقط (مش هنرفعه تلقائياً)
      }
    }

    setRequired(newRequired)
    setOptional(newOptional)
    setShowExcelImport(false)
    toast.success('✅ تم تعبئة البيانات من الملف - راجع قبل الحفظ')
  }, [excelData, required, optional])

  // ==================== الصفحة 1 ====================

  const renderPage1 = useMemo(() => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <Package className="w-5 h-5" />
        البيانات الأساسية (إجبارية)
      </h2>

      <Field label="اسم المنتج (عربي)" required>
        <TextInput value={required.name} onChange={v => updateRequired('name', v)} placeholder="مثال: منظم ملابس داخلي 6 قطع" />
        {required.name.length > 0 && required.name.length < 5 && (
          <p className="text-amber-500 text-xs mt-1">الاسم لازم 5 أحرف على الأقل ({required.name.length}/5)</p>
        )}
      </Field>

      <Field label="اسم المنتج (English)" required>
        <TextInput value={required.name_en} onChange={v => updateRequired('name_en', v)} placeholder="e.g. Underwear Organizer 6 Pieces" />
        {required.name_en.length > 0 && required.name_en.length < 5 && (
          <p className="text-amber-500 text-xs mt-1">Name must be at least 5 chars ({required.name_en.length}/5)</p>
        )}
      </Field>

      <Field label="نوع المنتج" required>
        <SelectInput value={required.product_type} onChange={v => updateRequired('product_type', v)} options={PRODUCT_TYPES} />
      </Field>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="نوع المعرف" required>
          <SelectInput value={required.id_type} onChange={v => updateRequired('id_type', v)} options={ID_TYPES} />
        </Field>

        <Field label={required.id_type === 'ASIN' ? 'ASIN' : required.id_type === 'UPC' ? 'UPC (12 رقم)' : 'EAN (13 رقم)'}>
          <div className="flex gap-2">
            <TextInput
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
          <TextInput type="number" value={required.price} onChange={v => updateRequired('price', v)} placeholder="0.00" />
        </Field>

        <Field label="الكمية" required>
          <TextInput type="number" value={required.quantity} onChange={v => updateRequired('quantity', v)} placeholder="0" />
        </Field>
      </div>

      <Field label="وصف المنتج (عربي)" required>
        <textarea
          value={required.description}
          onChange={e => updateRequired('description', e.target.value)}
          placeholder="وصف تفصيلي للمنتج بالعربي..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 resize-none"
        />
        {required.description.length > 0 && required.description.length < 10 && (
          <p className="text-amber-500 text-xs mt-1">الوصف لازم 10 أحرف على الأقل ({required.description.length}/10)</p>
        )}
      </Field>

      <Field label="وصف المنتج (English)" required>
        <textarea
          value={required.description_en}
          onChange={e => updateRequired('description_en', e.target.value)}
          placeholder="Detailed product description in English..."
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 resize-none"
        />
        {required.description_en.length > 0 && required.description_en.length < 10 && (
          <p className="text-amber-500 text-xs mt-1">Description must be at least 10 chars ({required.description_en.length}/10)</p>
        )}
        <p className="text-xs text-gray-500 mt-1">📌 الوصف بالإنجليزي هيتم إرساله لـ Amazon - الوصف بالعربي للـ dashboard فقط</p>
      </Field>
    </div>
  ), [required, lookingUp, lookupResult, updateRequired, handleLookup])

  // ==================== الصفحة 2 ====================

  const UNIT_COUNT_TYPES = [
    { value: 'Count', label: 'قطعة' },
    { value: ' ounces', label: 'أونصة' },
    { value: 'Pounds', label: 'رطل' },
    { value: 'Grams', label: 'جرام' },
    { value: 'Kilograms', label: 'كجم' },
    { value: 'Milliliters', label: 'مل' },
    { value: 'Liters', label: 'لتر' },
    { value: 'Meters', label: 'متر' },
    { value: 'Centimeters', label: 'سم' },
    { value: 'Inches', label: 'بوصة' },
    { value: 'Square Feet', label: 'قدم مربع' },
  ]

  const renderPage2 = useMemo(() => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <DollarSign className="w-5 h-5" />
        بيانات إضافية (اختيارية)
      </h2>

      {/* ===== قسم: معلومات المنتج ===== */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Package className="w-4 h-4" />
          معلومات المنتج
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="البراند">
            <TextInput value={optional.brand} onChange={v => updateOptional('brand', v)} placeholder="Generic" />
          </Field>
          <Field label="حالة المنتج">
            <SelectInput value={optional.condition} onChange={v => updateOptional('condition', v)} options={CONDITIONS} />
          </Field>
          <Field label="المصنع">
            <TextInput value={optional.manufacturer} onChange={v => updateOptional('manufacturer', v)} placeholder="اسم المصنع" />
          </Field>
          <Field label="رقم الموديل">
            <TextInput value={optional.model_number} onChange={v => updateOptional('model_number', v)} placeholder="Model-123" />
          </Field>
          <Field label="بلد المنشأ">
            <SelectInput value={optional.country_of_origin} onChange={v => updateOptional('country_of_origin', v)} options={COUNTRIES} />
          </Field>
          <Field label="الخامة / المادة">
            <TextInput value={optional.material} onChange={v => updateOptional('material', v)} placeholder="مثال: Plastic, Cotton" />
          </Field>
          <Field label="الفئة المستهدفة">
            <TextInput value={optional.target_audience} onChange={v => updateOptional('target_audience', v)} placeholder="مثال: Adults, Kids" />
          </Field>
        </div>
      </div>

      {/* ===== قسم: الشحن والتغليف ===== */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Image className="w-4 h-4" />
          الشحن والتغليف
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="طريقة الشحن">
            <SelectInput value={optional.fulfillment_channel} onChange={v => updateOptional('fulfillment_channel', v)} options={FULFILLMENT} />
            <p className="text-xs text-gray-500 mt-1">MFN = شحن ذاتي | AFN = FBA (شحن أمازون)</p>
          </Field>
          <Field label="وقت التجهيز (أيام)">
            <TextInput type="number" value={optional.handling_time} onChange={v => updateOptional('handling_time', v)} placeholder="1" />
            <p className="text-xs text-gray-500 mt-1">عدد الأيام قبل شحن المنتج</p>
          </Field>
          <Field label="عدد القطع في العبوة">
            <TextInput type="number" value={optional.package_quantity} onChange={v => updateOptional('package_quantity', v)} placeholder="1" />
            <p className="text-xs text-gray-500 mt-1">كم قطعة العميل هيشتري في مرة واحدة</p>
          </Field>
          <Field label="Browse Node ID">
            <TextInput value={optional.browse_node_id} onChange={v => updateOptional('browse_node_id', v)} placeholder="85363278031" />
            <p className="text-xs text-gray-500 mt-1">معرف التصنيف في أمازون - اختياري بس بيحسن ظهور المنتج</p>
          </Field>
        </div>
      </div>

      {/* ===== قسم: الوزن والأبعاد ===== */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          📐 الوزن والأبعاد
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Field label="الوزن">
              <div className="grid grid-cols-2 gap-2">
                <TextInput type="number" value={optional.weight} onChange={v => updateOptional('weight', v)} placeholder="0.0" />
                <SelectInput value={optional.weight_unit} onChange={v => updateOptional('weight_unit', v)} options={WEIGHT_UNITS} />
              </div>
            </Field>
          </div>
          <div>
            <Field label="العدد / الكمية">
              <div className="grid grid-cols-2 gap-2">
                <TextInput type="number" value={optional.number_of_items} onChange={v => updateOptional('number_of_items', v)} placeholder="1" />
                <TextInput value={optional.unit_count} onChange={v => updateOptional('unit_count', v)} placeholder="مثال: 500" />
              </div>
            </Field>
            <Field label="نوع الوحدة">
              <SelectInput value={optional.unit_count_type} onChange={v => updateOptional('unit_count_type', v)} options={UNIT_COUNT_TYPES} />
            </Field>
          </div>
        </div>
        <div>
          <Field label="الأبعاد (طول × عرض × ارتفاع)">
            <div className="grid grid-cols-4 gap-2">
              <TextInput type="number" value={optional.length} onChange={v => updateOptional('length', v)} placeholder="الطول" />
              <TextInput type="number" value={optional.width} onChange={v => updateOptional('width', v)} placeholder="العرض" />
              <TextInput type="number" value={optional.height} onChange={v => updateOptional('height', v)} placeholder="الارتفاع" />
              <SelectInput value={optional.dimension_unit} onChange={v => updateOptional('dimension_unit', v)} options={DIMENSION_UNITS} />
            </div>
          </Field>
        </div>
      </div>

      {/* ===== قسم: التسعير ===== */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          💰 التسعير
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="سعر قبل الخصم (Compare Price)">
            <TextInput type="number" value={optional.compare_price} onChange={v => updateOptional('compare_price', v)} placeholder="مثال: 200" />
            <p className="text-xs text-gray-500 mt-1">السعر القديم - هيظهر خط عليه (اختياري)</p>
          </Field>
          <Field label="سعر التكلفة (للحساب)">
            <TextInput type="number" value={optional.cost} onChange={v => updateOptional('cost', v)} placeholder="مثال: 80" />
            <p className="text-xs text-gray-500 mt-1">سعر الشراء - مش هيظهر للعميل (لحساب الهامش)</p>
          </Field>
          <Field label="سعر التخفيضات">
            <TextInput type="number" value={optional.sale_price} onChange={v => updateOptional('sale_price', v)} placeholder="مثال: 120" />
          </Field>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="بداية التخفيضات">
            <TextInput type="date" value={optional.sale_start_date} onChange={v => updateOptional('sale_start_date', v)} />
          </Field>
          <Field label="نهاية التخفيضات">
            <TextInput type="date" value={optional.sale_end_date} onChange={v => updateOptional('sale_end_date', v)} />
          </Field>
        </div>
      </div>

      {/* ===== قسم: تحسين البحث ===== */}
      <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          🔍 تحسين البحث (SEO)
        </h3>
        <Field label="كلمات البحث (Search Terms)">
          <textarea
            value={optional.keywords}
            onChange={e => updateOptional('keywords', e.target.value)}
            placeholder="كلمات بحث العملاء... (مفصولة بمسافات، حد أقصى 250 حرف)"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <p className="text-xs text-gray-500 mt-1">{optional.keywords.length}/250 حرف</p>
        </Field>
      </div>
    </div>
  ), [optional, updateOptional])

  // ==================== الصفحة 3 ====================

  const renderPage3 = useMemo(() => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <Image className="w-5 h-5" />
        الصور والإعلانات
      </h2>

      <Field label="الصورة الرئيسية" required>
        {mainImageUrl ? (
          <div className="relative inline-block">
            <img src={mainImageUrl} alt="Main" className="w-48 h-48 object-cover rounded-lg border-2 border-blue-500" />
            <button onClick={removeMainImage} className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600">
              <X className="w-4 h-4" />
            </button>
            <span className="absolute bottom-0 left-0 right-0 bg-green-500 text-white text-xs text-center py-1 rounded-b-lg">✅ مرفوعة</span>
          </div>
        ) : mainImagePreview ? (
          <div className="relative inline-block">
            <img src={mainImagePreview} alt="Preview" className="w-48 h-48 object-cover rounded-lg border-2 border-amber-500 opacity-75" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
            </div>
            <span className="absolute bottom-0 left-0 right-0 bg-amber-500 text-white text-xs text-center py-1 rounded-b-lg">جاري الرفع...</span>
          </div>
        ) : (
          <label className="flex flex-col items-center justify-center w-48 h-48 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-blue-500 transition-colors">
            <Upload className="w-8 h-8 text-gray-400 mb-2" />
            <span className="text-sm text-gray-500">اختر صورة رئيسية</span>
            <input type="file" accept="image/*" onChange={handleMainImageUpload} className="hidden" disabled={uploadingImages} />
          </label>
        )}
      </Field>

      <Field label="صور إضافية (حتى 8)">
        <div className="flex flex-wrap gap-3">
          {extraImageUrls.length < 8 && (
            <label className="flex flex-col items-center justify-center w-24 h-24 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-blue-500 transition-colors">
              <Upload className="w-6 h-6 text-gray-400" />
              <span className="text-xs text-gray-500 mt-1">+ إضافة</span>
              <input type="file" accept="image/*" multiple onChange={handleExtraImagesUpload} className="hidden" disabled={uploadingImages} />
            </label>
          )}
          {extraImageUrls.map((url, idx) => (
            <div key={idx} className="relative group">
              <img src={url} alt={`Extra ${idx}`} className="w-24 h-24 object-cover rounded-lg border border-gray-300 dark:border-gray-600" />
              <button onClick={() => removeExtraImage(idx)} className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">{extraImageUrls.length}/8 صور إضافية</p>
      </Field>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
        <Field label="عدد الإعلانات (نسخ من نفس المنتج)">
          <div className="flex items-center gap-3">
            <button onClick={() => setListingCopiesStr(String(Math.max(1, listingCopies - 1)))} className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-lg font-bold hover:bg-gray-100 dark:hover:bg-gray-700">-</button>
            <input
              type="number"
              min={1}
              max={50}
              value={listingCopiesStr}
              onChange={e => setListingCopiesStr(e.target.value)}
              className="w-16 text-center text-2xl font-bold bg-transparent border-b-2 border-gray-300 dark:border-gray-600 focus:border-blue-500 outline-none"
            />
            <button onClick={() => setListingCopiesStr(String(Math.min(50, listingCopies + 1)))} className="w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 flex items-center justify-center text-lg font-bold hover:bg-gray-100 dark:hover:bg-gray-700">+</button>
          </div>
          <p className="text-xs text-gray-500 mt-1">كل إعلان هياخد SKU مختلف تلقائياً</p>
        </Field>
      </div>
    </div>
  ), [mainImageUrl, extraImageUrls, listingCopies, listingCopiesStr, removeMainImage, removeExtraImage, handleMainImageUpload, handleExtraImagesUpload, uploadingImages, mainImagePreview])

  // ==================== Excel Modal ====================

  const renderExcelModal = () => {
    if (!showExcelImport || !excelData) return null

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">اختار منتج من الملف</h3>
            <button onClick={() => setShowExcelImport(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="p-4 space-y-2">
            {excelData.map((row, idx) => (
              <button
                key={idx}
                onClick={() => handleRowSelect(idx)}
                className="w-full text-right p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              >
                <div className="font-medium text-gray-900 dark:text-white">{row['اسم المنتج'] || row['name'] || row['title'] || `منتج ${idx + 1}`}</div>
                <div className="text-sm text-gray-500">{row['السعر'] || row['price'] ? `EGP ${row['السعر'] || row['price']}` : ''}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // ==================== Preview Modal ====================

  const renderPreviewModal = () => {
    if (!showPreview || previewData.length === 0) return null

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-3xl w-full max-h-[85vh] overflow-auto">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center sticky top-0 bg-white dark:bg-gray-800">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              👁️ معاينة البيانات ({previewData.length} منتج)
            </h3>
            <button onClick={() => setShowPreview(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-4 space-y-4">
            {previewData.map((product, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-bold px-2 py-1 rounded">
                    منتج {idx + 1}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">{product.sku}</span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">الاسم (EN):</span>
                    <p className="font-medium text-gray-900 dark:text-white">{product.name}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">الاسم (AR):</span>
                    <p className="font-medium text-gray-900 dark:text-white">{product.name_ar}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">الوصف (EN):</span>
                    <p className="text-gray-700 dark:text-gray-300 line-clamp-2">{product.description}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">الوصف (AR):</span>
                    <p className="text-gray-700 dark:text-gray-300 line-clamp-2">{product.description_ar}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">السعر:</span>
                    <p className="font-bold text-green-600">{product.price} EGP</p>
                  </div>
                  <div>
                    <span className="text-gray-500">الكمية:</span>
                    <p className="font-medium">{product.quantity}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">البراند:</span>
                    <p>{product.brand}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">الحالة:</span>
                    <p>{product.condition}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">نوع المنتج:</span>
                    <p className="text-xs">{product.product_type}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">بلد المنشأ:</span>
                    <p>{product.country_of_origin}</p>
                  </div>
                </div>

                {/* JSON Toggle */}
                <details className="mt-3">
                  <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-700">
                    📋 عرض JSON كامل
                  </summary>
                  <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-auto max-h-48">
                    {JSON.stringify(product, null, 2)}
                  </pre>
                </details>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center sticky bottom-0 bg-white dark:bg-gray-800">
            <button
              onClick={() => setShowPreview(false)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              إغلاق
            </button>
            <button
              onClick={() => { setShowPreview(false); handleSubmit() }}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              حفظ المنتجات
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ==================== العرض الرئيسي ====================

  return (
    <div className="max-w-3xl mx-auto py-6" dir="rtl">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isEditMode ? (completeMode ? 'إكمال بيانات المنتج' : 'تعديل المنتج') : 'إضافة منتج جديد'}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
              {isEditMode
                ? (completeMode ? 'أكمل البيانات الناقصة عشان المنتج يتقبل على Amazon' : 'عدّل بيانات المنتج')
                : 'أدخل بيانات المنتج وسيتم إرساله لـ Amazon تلقائياً'
              }
            </p>
          </div>
          <button
            onClick={() => {
              const buffer = generateTemplateExcel()
              const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = 'crazy_lister_template.xlsx'
              a.click()
              URL.revokeObjectURL(url)
              toast.success('تم تحميل القالب')
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <Download className="w-4 h-4" /> تحميل قالب Excel
          </button>
        </div>

        {/* Edit Mode: Missing Fields Banner */}
        {isEditMode && missingFields.length > 0 && (
          <div className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-amber-800 dark:text-amber-300">البيانات الناقصة:</h3>
                <ul className="mt-2 text-sm text-amber-700 dark:text-amber-400 space-y-1">
                  {missingFields.map((field, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-amber-500 rounded-full" />
                      {field}
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-amber-600 dark:text-amber-500 mt-2">
                  ⚠️ المنتج هيترفض من Amazon لو البيانات دي ناقصة
                </p>
              </div>
            </div>
          </div>
        )}

        {isEditMode && missingFields.length === 0 && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700 rounded-lg">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <CheckCircle className="w-5 h-5" />
              <p className="text-sm font-medium">✅ البيانات كاملة - المنتج جاهز للرفع على Amazon</p>
            </div>
          </div>
        )}
      </div>

      <StepIndicator currentPage={page} onNavigate={setPage} />

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        {page === 1 && renderPage1}
        {page === 2 && renderPage2}
        {page === 3 && renderPage3}
      </div>

      <div className="flex justify-between mt-6">
        <button
          onClick={() => page > 1 ? setPage(page - 1) : navigate('/products')}
          className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
        >
          {page > 1 ? '→ السابق' : 'إلغاء'}
        </button>

        {page < 3 ? (
          <button onClick={() => setPage(page + 1)} className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            التالي ←
          </button>
        ) : (
          <div className="flex gap-3">
            {/* زر معاينة البيانات المحلية */}
            <button
              onClick={handlePreview}
              className="px-6 py-2.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 flex items-center gap-2"
            >
              <Eye className="w-4 h-4" /> معاينة البيانات
            </button>
            {/* زر معاينة Amazon Feed */}
            <button
              onClick={handleAmazonPreview}
              disabled={previewLoading}
              className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
            >
              {previewLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4" />}
              📦 معاينة Amazon
            </button>
            {/* زر الحفظ */}
            <button
              onClick={handleSubmit}
              disabled={createMutation.isPending}
              className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              {createMutation.isPending ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> جاري الحفظ...</>
              ) : completeMode ? (
                <><Save className="w-4 h-4" /> حفظ وإكمال البيانات</>
              ) : (
                <><Save className="w-4 h-4" /> حفظ المنتجات</>
              )}
            </button>
          </div>
        )}
      </div>

      {renderExcelModal()}
      {renderPreviewModal()}

      {/* ==================== Amazon Feed Preview Modal ==================== */}
      {showAmazonPreview && amazonFeedData && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-5xl w-full max-h-[90vh] overflow-auto">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center sticky top-0 bg-white dark:bg-gray-800 z-10">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">📦 معاينة بيانات Amazon Feed</h3>
                <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
                  amazonFeedData.summary.ready_for_amazon
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {amazonFeedData.summary.ready_for_amazon ? '✅ جاهز' : '❌ ناقص'}
                </span>
              </div>
              <button onClick={() => setShowAmazonPreview(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200 dark:border-gray-700 px-4">
              {[
                { key: 'summary' as const, label: '📊 ملخص', icon: '' },
                { key: 'json' as const, label: '📋 JSON', icon: '' },
                { key: 'xml' as const, label: '📄 XML Feed', icon: '' },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setPreviewTab(tab.key)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    previewTab === tab.key
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="p-6">
              {/* Summary Tab */}
              {previewTab === 'summary' && (
                <div className="space-y-6">
                  {/* Stats */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-blue-600">{amazonFeedData.summary.total_fields}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">حقول مملوءة</div>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-green-600">✅</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">جاهز لـ Amazon</div>
                    </div>
                    <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-red-600">{amazonFeedData.summary.errors}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">أخطاء</div>
                    </div>
                    <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg text-center">
                      <div className="text-2xl font-bold text-amber-600">{amazonFeedData.summary.warnings}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">تحذيرات</div>
                    </div>
                  </div>

                  {/* Validation */}
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">✅ الحقول المرسلة لـ Amazon</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(amazonFeedData.json_payload).map(([key, value]) => (
                        value && (
                          <div key={key} className="flex justify-between p-2 bg-gray-50 dark:bg-gray-900 rounded">
                            <span className="text-gray-500">{key}:</span>
                            <span className="font-mono text-gray-900 dark:text-white truncate ml-2">
                              {typeof value === 'object' ? JSON.stringify(value).slice(0, 50) : String(value)}
                            </span>
                          </div>
                        )
                      ))}
                    </div>
                  </div>

                  {/* Errors */}
                  {amazonFeedData.validation.errors.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-red-600 mb-2">❌ أخطاء (تمنع الإرسال)</h4>
                      {amazonFeedData.validation.errors.map((err: any, i: number) => (
                        <div key={i} className="p-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded mb-1 text-sm">
                          <strong>{err.field}:</strong> {err.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Warnings */}
                  {amazonFeedData.validation.warnings.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-amber-600 mb-2">⚠️ تحذيرات (مش بتوقف)</h4>
                      {amazonFeedData.validation.warnings.map((warn: any, i: number) => (
                        <div key={i} className="p-2 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded mb-1 text-sm">
                          <strong>{warn.field}:</strong> {warn.message}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* JSON Tab */}
              {previewTab === 'json' && (
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold text-gray-900 dark:text-white">📋 JSON Payload</h4>
                    <button
                      onClick={() => navigator.clipboard.writeText(JSON.stringify(amazonFeedData.json_payload, null, 2))}
                      className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                    >
                      📋 نسخ
                    </button>
                  </div>
                  <pre className="p-4 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-auto max-h-[60vh] font-mono">
                    {JSON.stringify(amazonFeedData.json_payload, null, 2)}
                  </pre>
                </div>
              )}

              {/* XML Tab */}
              {previewTab === 'xml' && (
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold text-gray-900 dark:text-white">📄 Amazon XML Feed</h4>
                    <button
                      onClick={() => navigator.clipboard.writeText(amazonFeedData.xml_feed)}
                      className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                    >
                      📋 نسخ
                    </button>
                  </div>
                  <pre className="p-4 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-auto max-h-[60vh] font-mono whitespace-pre">
                    {amazonFeedData.xml_feed}
                  </pre>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center sticky bottom-0 bg-white dark:bg-gray-800">
              <button
                onClick={() => setShowAmazonPreview(false)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                إغلاق
              </button>
              <button
                onClick={() => { setShowAmazonPreview(false); handleSubmit() }}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <Save className="w-4 h-4" /> حفظ وإرسال لـ Amazon
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
