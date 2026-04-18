/**
 * Product Create Page - Phase 3: AI + Instructions
 *
 * 4 Pages Architecture:
 * Page 0: مساعد الذكاء الاصطناعي (واجهة أولى)
 * Page 1: الحقول الإجبارية (29 حقل مطلوب من Amazon)
 * Page 2: الحقول الاختيارية
 * Page 3: الصور + عدد الإعلانات + أزرار الإرسال
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Package, DollarSign, Image as ImageIcon, Save, Loader2,
  AlertTriangle, CheckCircle, Upload, X, FileSpreadsheet, Eye,
  Truck, ShoppingCart, Tag, Globe, Sparkles, Store, Zap
} from 'lucide-react'
import { useCreateProduct } from '@/api/hooks'
import { useSellersList } from '@/api/hooks'
import { productsApi, imagesApi } from '@/api/endpoints'
import { aiApi } from '@/api/ai'
import { AIAssistantPanel } from '@/components/ai/AIAssistantPanel'
import type { AIMergedProduct } from '@/types/ai'
import { NeonButton } from '@/components/common'
import {
  PRODUCT_TYPES, PRODUCT_TYPE_CATEGORIES, BROWSE_NODES, BROWSE_NODES_BY_TYPE,
  CONDITIONS, FULFILLMENT_CHANNELS,
  ID_TYPES, COUNTRIES, UNIT_TYPES, WEIGHT_UNITS, DIMENSION_UNITS,
  DEFAULT_VALUES, VALIDATION_RULES
} from '@/constants/amazon'
import toast from 'react-hot-toast'

// ==================== Shared UI Components ====================

const TextInput = ({
  value, onChange, type = 'text', placeholder, disabled,
}: {
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  disabled?: boolean
}) => (
  <input
    type={type}
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    disabled={disabled}
    className="neon-input disabled:opacity-50"
  />
)

const NumberInput = ({
  value, onChange, placeholder, min, step,
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  min?: string
  step?: string
}) => (
  <input
    type="number"
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    min={min}
    step={step}
    className="neon-input neon-input--green"
  />
)

const SelectInput = ({
  value, onChange, options,
}: {
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
}) => (
  <select
    value={value}
    onChange={e => onChange(e.target.value)}
    className="neon-input neon-select"
  >
    {options.map(opt => (
      <option key={opt.value} value={opt.value}>
        {opt.icon ? `${opt.icon} ${opt.label}` : opt.label}
      </option>
    ))}
  </select>
)

const Field = ({
  label, children, required: isRequired, hint, isAiGenerated,
}: {
  label: string
  children: React.ReactNode
  required?: boolean
  hint?: string
  isAiGenerated?: boolean
}) => (
  <div className="space-y-1 group">
    <div className="flex items-center justify-between">
      <label className="text-sm font-bold text-text-primary flex items-center gap-1.5">
        {label}
        {isRequired && <span className="text-neon-red font-black text-xs">*</span>}
        {isAiGenerated && (
          <span className="flex items-center gap-0.5 text-[9px] bg-amazon-orange/10 text-amazon-orange px-1.5 py-0.5 rounded border border-amazon-orange/20">
            <Sparkles className="w-2.5 h-2.5" /> AI
          </span>
        )}
      </label>
      {hint && (
        <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] text-text-muted bg-white/5 px-2 py-0.5 rounded-full border border-white/10">
          <Zap className="w-3 h-3 text-amazon-orange" />
          {hint}
        </div>
      )}
    </div>
    <div className="relative">
      {children}
    </div>
  </div>
)

const RadioGroup = ({
  name, options, value, onChange,
}: {
  name: string
  options: { value: string; label: string }[]
  value: string
  onChange: (v: string) => void
}) => (
  <div className="flex flex-wrap gap-3">
    {options.map(opt => (
      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name={name}
          checked={value === opt.value}
          onChange={() => onChange(opt.value)}
          className="neon-radio"
        />
        <span className="text-sm text-text-secondary">{opt.label}</span>
      </label>
    ))}
  </div>
)

// ==================== Step Indicator ====================

const StepIndicator = ({
  currentPage,
  onNavigate,
}: {
  currentPage: number
  onNavigate: (page: number) => void
}) => (
  <div className="flex items-center justify-center gap-2 mb-6 flex-wrap">
    {[
      { n: 0, label: 'مساعد AI', icon: Sparkles },
      { n: 1, label: 'الحقول الإجبارية', icon: Tag },
      { n: 2, label: 'الحقول الاختيارية', icon: ShoppingCart },
      { n: 3, label: 'الصور والإرسال', icon: ImageIcon },
    ].map(step => {
      const Icon = step.icon
      return (
        <button
          key={step.n}
          onClick={() => onNavigate(step.n)}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all
            ${currentPage === step.n
              ? 'bg-gradient-to-r from-amazon-orange to-amazon-light text-white shadow-lg'
              : currentPage > step.n
                ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20'
                : 'bg-bg-elevated text-text-muted border border-border-subtle'
            }`}
        >
          {currentPage > step.n ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <Icon className="w-4 h-4" />
          )}
          <span>{step.label}</span>
        </button>
      )
    })}
  </div>
)

// ==================== Main Component ====================

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const createMutation = useCreateProduct()
  const { data: sellersData, isLoading: sellersLoading } = useSellersList()

  const editProduct = (location.state as any)?.editProduct as any
  const isEditMode = !!editProduct

  const [page, setPage] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  // ==================== Seller Selection ====================
  const sellers = sellersData?.sellers ?? []
  const [selectedSellerId, setSelectedSellerId] = useState<string>('')

  // Initialize selectedSellerId once sellers are loaded
  useEffect(() => {
    if (sellers.length > 0 && !selectedSellerId) {
      setSelectedSellerId(
        editProduct?.seller_id || sellers[0].id
      )
    }
  }, [sellers, editProduct?.seller_id, selectedSellerId])

  // ==================== PAGE 1: الحقول الإجبارية ====================
  const [required, setRequired] = useState({
    // Tab 1: الهوية الأساسية
    name_ar: '',
    name_en: '',
    product_type: DEFAULT_VALUES.product_type,
    id_type: DEFAULT_VALUES.id_type as string,
    ean: '',
    has_product_identifier: false, // GTIN exemption checkbox
    brand: DEFAULT_VALUES.brand,
    model_number: '',
    model_name: '', // [NEW] Required by SP-API
    manufacturer: DEFAULT_VALUES.brand,
    country_of_origin: DEFAULT_VALUES.country_of_origin,

    // Tab 2: الوصف والتفاصيل
    description_ar: '',
    description_en: '',
    bullet_points: ['', '', '', '', ''],
    browse_node_id: DEFAULT_VALUES.browse_node_id,
    included_components: '',
    unit_count: String(DEFAULT_VALUES.unit_count),
    unit_count_type: DEFAULT_VALUES.unit_count_type,

    // Tab 3: التسعير والكمية
    price: '',
    quantity: '0',

    // Tab 4: الشحن والأبعاد (MFN ثابت)
    condition: DEFAULT_VALUES.condition,
    package_length: String(DEFAULT_VALUES.package_length),
    package_width: String(DEFAULT_VALUES.package_width),
    package_height: String(DEFAULT_VALUES.package_height),
    item_weight: String(DEFAULT_VALUES.item_weight),
    package_weight: String(DEFAULT_VALUES.package_weight),
    number_of_boxes: String(DEFAULT_VALUES.number_of_boxes),
  })

  // ==================== PAGE 2: الحقول الاختيارية ====================
  const [optional, setOptional] = useState({
    keywords: [] as string[],
    keywordInput: '',
    material: '',
    target_audience: '',
    compare_price: '',
    cost: '',
    sale_price: '',
    sale_start_date: '',
    sale_end_date: '',
    handling_time: String(DEFAULT_VALUES.handling_time),
    package_quantity: String(DEFAULT_VALUES.package_quantity),
    // Technical Specifications (Electrical)
    voltage: '',
    wattage: '',
    operating_frequency: '',
    power_plug_type: '',
  })

  // ==================== PAGE 3: الصور والإرسال ====================
  const [mainImageUrl, setMainImageUrl] = useState<string>('')
  const [mainImagePreview, setMainImagePreview] = useState<string>('')
  const [extraImageUrls, setExtraImageUrls] = useState<string[]>([])
  const [extraImagePreviews, setExtraImagePreviews] = useState<string[]>([])
  const [uploadingImages, setUploadingImages] = useState(false)
  const [listingCopies, setListingCopies] = useState(1)

  // ==================== AI Generated Products ====================
  const [aiProducts, setAiProducts] = useState<AIMergedProduct[]>([])
  const [selectedAiProduct, setSelectedAiProduct] = useState<number | null>(null)

  // ==================== Task 3: Amazon Import by ASIN/UPC/EAN ====================
  const [importSearch, setImportSearch] = useState('')
  const [importType, setImportType] = useState('ASIN')
  const [importing, setImporting] = useState(false)

  const handleImportFromAmazon = useCallback(async () => {
    if (!importSearch.trim()) { toast.error('أدخل ASIN أو UPC أو EAN'); return }
    setImporting(true)
    try {
      const response = await fetch('/api/v1/ai/import-from-amazon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_value: importSearch.trim(), search_type: importType }),
      })
      const data = await response.json()
      if (!data.found) {
        toast.error(data.message || 'لم يتم العثور على المنتج')
        return
      }
      // Fill form with imported data
      setRequired(prev => ({
        ...prev,
        name_ar: data.title || prev.name_ar,
        name_en: data.title || prev.name_en,
        description_ar: data.description || prev.description_ar,
        description_en: data.description || prev.description_en,
        bullet_points: [...(data.bullet_points || []), '', '', '', '', ''].slice(0, 5),
        brand: data.brand || prev.brand,
        manufacturer: data.manufacturer || prev.manufacturer,
        product_type: data.product_type || prev.product_type,
        country_of_origin: data.country_of_origin || prev.country_of_origin,
      }))
      // Set images if available
      if (data.images && data.images.length > 0) {
        setMainImageUrl(data.images[0])
        setExtraImageUrls(data.images.slice(1, 9))
      }
      toast.success('تم استيراد البيانات من Amazon!')
      setPage(1)
    } catch (e: any) {
      toast.error('فشل الاستيراد')
    } finally {
      setImporting(false)
    }
  }, [importSearch, importType])

  const fileInputRef = useRef<HTMLInputElement>(null)
  const extraFileInputRef = useRef<HTMLInputElement>(null)

  // ==================== Edit Mode: Populate fields ====================
  useEffect(() => {
    if ((location.state as any)?.completeMode) {
      setPage(1) // Jump to form directly
    }
  }, [location.state])

  useEffect(() => {
    if (editProduct) {
      const bullets = Array.isArray(editProduct.bullet_points)
        ? editProduct.bullet_points
        : []
      const filledBullets = [...bullets, '', '', '', '', ''].slice(0, 5)

      const dims = editProduct.dimensions as any

      setRequired({
        name_ar: editProduct.name_ar || editProduct.name || '',
        name_en: editProduct.name_en || editProduct.name || '',
        product_type: editProduct.product_type || DEFAULT_VALUES.product_type,
        id_type: editProduct.ean ? 'EAN' : editProduct.upc ? 'UPC' : DEFAULT_VALUES.id_type,
        ean: editProduct.ean || editProduct.upc || '',
        has_product_identifier: editProduct.has_product_identifier || false,
        brand: editProduct.brand || DEFAULT_VALUES.brand,
        model_number: editProduct.model_number || '',
        manufacturer: editProduct.manufacturer || DEFAULT_VALUES.brand,
        country_of_origin: editProduct.country_of_origin || DEFAULT_VALUES.country_of_origin,
        description_ar: editProduct.description_ar || editProduct.description || '',
        description_en: editProduct.description_en || editProduct.description || '',
        bullet_points: filledBullets,
        browse_node_id: editProduct.browse_node_id || DEFAULT_VALUES.browse_node_id,
        included_components: editProduct.name || '',
        unit_count: String(editProduct.number_of_items || DEFAULT_VALUES.unit_count),
        unit_count_type: DEFAULT_VALUES.unit_count_type,
        price: String(editProduct.price || ''),
        quantity: String(editProduct.quantity || '0'),
        condition: editProduct.condition || DEFAULT_VALUES.condition,
        fulfillment_channel: editProduct.fulfillment_channel || DEFAULT_VALUES.fulfillment_channel,
        package_length: String(dims?.length || DEFAULT_VALUES.package_length),
        package_width: String(dims?.width || DEFAULT_VALUES.package_width),
        package_height: String(dims?.height || DEFAULT_VALUES.package_height),
        item_weight: String(editProduct.weight || DEFAULT_VALUES.item_weight),
        package_weight: String(DEFAULT_VALUES.package_weight),
        number_of_boxes: String(DEFAULT_VALUES.number_of_boxes),
      })

      setOptional({
        keywords: Array.isArray(editProduct.keywords) ? editProduct.keywords : [],
        keywordInput: '',
        material: editProduct.material || '',
        target_audience: editProduct.target_audience || '',
        compare_price: String(editProduct.compare_price || ''),
        cost: String(editProduct.cost || ''),
        sale_price: String(editProduct.sale_price || ''),
        sale_start_date: editProduct.sale_start_date ? editProduct.sale_start_date.split('T')[0] : '',
        sale_end_date: editProduct.sale_end_date ? editProduct.sale_end_date.split('T')[0] : '',
        handling_time: String(editProduct.handling_time || DEFAULT_VALUES.handling_time),
        package_quantity: String(editProduct.package_quantity || DEFAULT_VALUES.package_quantity),
        // Technical Specifications (Electrical)
        voltage: editProduct.voltage || '',
        wattage: editProduct.wattage || '',
        operating_frequency: editProduct.operating_frequency || '',
        power_plug_type: editProduct.power_plug_type || '',
      })

      const images = editProduct.images || []
      if (images.length > 0) {
        setMainImageUrl(images[0])
        setExtraImageUrls(images.slice(1, 9))
      }
    }
  }, [editProduct])

  // ==================== AI: Handle generated products ====================
  // ⚠️ IMPORTANT: When AI generates products, listingCopies is automatically synced
  // to match the AI count. This ensures:
  // - AI generates 3 products → listingCopies = 3 → 3 listings created
  // - AI generates 1 product → listingCopies = 1 → 1 listing created
  // The user can manually override listingCopies after AI generation if needed.
  const handleAiProductsGenerated = useCallback((products: AIMergedProduct[]) => {
    setAiProducts(products)
    if (products.length > 0) {
      setSelectedAiProduct(0)
      fillFormFromAi(products[0])
      // Task 6: Sync listingCopies = AI-generated count (direct)
      // This ensures each AI product gets its own listing/ad on Amazon
      setListingCopies(products.length)
      toast.success(`✅ تم توليد ${products.length} منتج — عدد الإعلانات تم ضبطه لـ ${products.length}`)
    }
  }, [])

  const fillFormFromAi = useCallback((product: AIMergedProduct) => {
    // Fill ALL fields directly from AI - no partial fill
    setRequired(prev => ({
      ...prev,
      // الهوية الأساسية
      name_ar: product.name_ar,
      name_en: product.name_en,
      product_type: product.product_type,
      id_type: product.ean ? 'EAN' : (product.upc ? 'UPC' : 'EAN'),
      ean: product.ean || '',
      has_product_identifier: !product.ean && !product.upc, // Automatically check exemption if barcode is empty

      // ⚠️ FIXED FIELDS - AI CANNOT modify these (user/seller settings only)
      brand: product.brand || prev.brand,
      manufacturer: product.manufacturer || prev.manufacturer,
      country_of_origin: product.country_of_origin || prev.country_of_origin,
      model_number: product.model_number,
      model_name: product.model_name || '', // [NEW]

      // الوصف والتفاصيل - ملئ مباشر
      description_ar: product.description_ar,
      description_en: product.description_en,
      bullet_points: [...product.bullet_points_ar, '', '', '', '', ''].slice(0, 5),
      included_components: product.included_components || '', // كلمة واحدة
      unit_count: String(DEFAULT_VALUES.unit_count),
      unit_count_type: DEFAULT_VALUES.unit_count_type,

      // التسعير والكمية - AI يتركها فاضي (اختياري)
      price: product.price ? String(product.price) : '', // فاضي لو null
      quantity: '0',

      // الشحن والأبعاد
      condition: product.condition || DEFAULT_VALUES.condition,
      fulfillment_channel: product.fulfillment_channel || DEFAULT_VALUES.fulfillment_channel,
      package_length: String(DEFAULT_VALUES.package_length),
      package_width: String(DEFAULT_VALUES.package_width),
      package_height: String(DEFAULT_VALUES.package_height),
      item_weight: String(DEFAULT_VALUES.item_weight),
      package_weight: String(DEFAULT_VALUES.package_weight),
      number_of_boxes: String(DEFAULT_VALUES.number_of_boxes),

      // AI-selected browse_node_id — الفئة المناسبة حسب المنتج
      browse_node_id: product.browse_node_id
        || (BROWSE_NODES_BY_TYPE[product.product_type]?.[0]?.value)
        || prev.browse_node_id,
    }))

    // الحقول الاختيارية
    setOptional(prev => ({
      ...prev,
      keywords: product.keywords || [],
      keywordInput: '',
      material: product.material || '',
      target_audience: product.target_audience || '',
      compare_price: '',
      cost: '',
      sale_price: '',
      sale_start_date: '',
      sale_end_date: '',
      handling_time: String(DEFAULT_VALUES.handling_time),
      package_quantity: String(DEFAULT_VALUES.package_quantity),
    }))
  }, [])

  // ==================== Task 5: SEO Improvement via AI ====================
  const [improving, setImproving] = useState(false)

  const handleImproveWithAI = useCallback(async () => {
    setImproving(true)
    try {
      const nameToImprove = required.name_ar.trim() || required.name_en.trim() || ''
      const descToImprove = required.description_ar.trim() || required.description_en.trim() || ''
      const bullets = required.bullet_points.filter(bp => bp.trim().length > 0).join(' | ')

      // FIX: Build specs properly — ensure min_length=5 for backend
      let specs = ''
      if (descToImprove && bullets) {
        specs = `${descToImprove} | ${bullets}`
      } else if (descToImprove) {
        specs = descToImprove
      } else if (bullets) {
        specs = bullets
      } else {
        // Fallback: use product_type or name as specs
        specs = required.product_type || nameToImprove
      }

      // FIX: Ensure name meets backend min_length=2 requirement
      if (nameToImprove.length < 2) {
        toast.error('اكتب اسم المنتج الأول عشان الـ AI يقدر يحسنه')
        setImproving(false)
        return
      }

      // FIX: Ensure specs meets backend min_length=5 requirement
      if (specs.length < 5) {
        specs = `منتج ${nameToImprove}`
      }

      const result = await aiApi.generateProduct({
        name: nameToImprove,
        specs: specs,
        copies: 1,
      })

      if (result.variants.length > 0) {
        const v = result.variants[0]
        const b = result.base_product
        
        // Construct a merged product object for fillFormFromAi
        const merged: AIMergedProduct = {
          ...b,
          ...v,
          variant_number: v.variant_number,
          name_ar: v.name_ar,
          name_en: v.name_en,
          description_ar: v.description_ar,
          description_en: v.description_en,
          suggested_sku: v.suggested_sku,
          model_name: v.model_name || b.model_name || '',
        }

        fillFormFromAi(merged)
        toast.success('تم تحسين وتحديث كافة البيانات بالذكاء الاصطناعي!')
      }
    } catch (e: any) {
      // FIX: Properly extract error message from FastAPI 422 response
      let errorMsg = 'فشل التحسين'
      const detail = e?.response?.data?.detail

      if (Array.isArray(detail)) {
        // FastAPI validation errors (422) — new format: [{field, message}, ...]
        errorMsg = detail.map((err: any) => {
          const field = err.field || err.loc?.join('.') || ''
          const msg = err.message || err.msg || err.message || ''
          return `${field}: ${msg}`
        }).join('\n')
      } else if (typeof detail === 'string') {
        errorMsg = detail
      } else if (typeof detail === 'object' && detail !== null) {
        errorMsg = JSON.stringify(detail, null, 2)
      } else if (typeof e?.message === 'string') {
        errorMsg = e.message
      }

      toast.error('فشل التحسين: ' + errorMsg)
      console.error('AI Improve error:', e)
    } finally {
      setImproving(false)
    }
  }, [required, setRequired, setOptional])

  // ==================== Validation ====================
  const validate = (): { valid: boolean; errors: string[] } => {
    const errors: string[] = []

    // Validate seller selection
    if (!selectedSellerId) {
      errors.push('لازم تختار تاجر أولاً')
    }

    // Page 1 - Required fields
    if (required.name_ar.trim().length < VALIDATION_RULES.name_ar.min)
      errors.push('اسم المنتج بالعربي لازم 3 أحرف على الأقل')
    if (required.name_en.trim().length < VALIDATION_RULES.name_en.min)
      errors.push('اسم المنتج بالإنجليزي لازم 3 أحرف على الأقل')
    // Task 2: Barcode is MANDATORY - EAN (13 digits) or UPC (12 digits) only
    // UNLESS "has_product_identifier" is checked (GTIN exemption)
    if (!required.has_product_identifier) {
      const idLen = required.id_type === 'UPC' ? 12 : 13
      if (!required.ean || required.ean.length !== idLen)
        errors.push(`الباركود (${required.id_type}) لازم يكون ${idLen} رقم — إجباري`)
    } else {
      // GTIN exemption: product doesn't have a product identifier
      if (required.ean && required.ean.trim()) {
        const idLen = required.id_type === 'UPC' ? 12 : 13
        if (required.ean.length !== idLen)
          errors.push(`الباركود (${required.id_type}) لازم يكون ${idLen} رقم لو هتدخله`)
      }
    }
    if (!required.brand || required.brand.trim().length < 1)
      errors.push('البراند مطلوب')
    if (!required.manufacturer || required.manufacturer.trim().length < 1)
      errors.push('المصنع مطلوب')
    if (required.model_number.trim().length < 1)
      errors.push('رقم الموديل مطلوب')
    if (required.model_name.trim().length < 1)
      errors.push('اسم الموديل مطلوب (Model Name)')
    if (required.description_ar.trim().length < 50)
      errors.push('الوصف بالعربي لازم يكون وصف كامل - 3 سطور على الأقل (50 حرف كحد أدنى)')
    if (required.description_en.trim().length < 50)
      errors.push('الوصف بالإنجليزي لازم يكون وصف كامل - 3 سطور على الأقل (50 حرف كحد أدنى)')
    if (!required.included_components || required.included_components.trim().length < 1)
      errors.push('المكونات المضمنة مطلوبة (Included Components)')
    // النقاط البيعية - اختيارية (ممنوع إجباري)
    // التسعير والكمية - اختياري (ممنوع إجباري)
    // No validation on price/quantity - they are optional
    if (!mainImageUrl)
      errors.push('لازم ترفع صورة رئيسية — إجباري لأمازون')

    return { valid: errors.length === 0, errors }
  }

  // ==================== Image Upload ====================
  const handleMainImageUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/') || file.size > 5 * 1024 * 1024) {
      toast.error('الملف لازم يكون صورة وأقل من 5MB')
      return
    }

    const reader = new FileReader()
    reader.onload = () => setMainImagePreview(reader.result as string)
    reader.readAsDataURL(file)

    setUploadingImages(true)
    try {
      const res = await imagesApi.upload(file)
      setMainImageUrl(res.data.url)
      toast.success('تم رفع الصورة الرئيسية')
    } catch {
      toast.error('فشل رفع الصورة')
    } finally {
      setUploadingImages(false)
    }
  }, [])

  // ==================== Upload Images to GitHub (Manual Button) ====================
  const [uploadingToGitHub, setUploadingToGitHub] = useState(false)

  const handleUploadToGitHub = async () => {
    const allFiles = [mainImagePreview, ...extraImagePreviews].filter(Boolean)
    if (allFiles.length === 0) {
      toast.error('لازم ترفع صور الأول')
      return
    }

    setUploadingToGitHub(true)
    try {
      const githubUrls = await uploadImagesToGitHub()
      if (githubUrls.length > 0) {
        toast.success(`✅ تم رفع ${githubUrls.length} من ${allFiles.length} صورة على GitHub`)
      }
    } catch (err: any) {
      toast.error('❌ ' + err.message)
    } finally {
      setUploadingToGitHub(false)
    }
  }

  const uploadImagesToGitHub = async (): Promise<string[]> => {
    const allFiles = [mainImagePreview, ...extraImagePreviews].filter(Boolean)
    if (allFiles.length === 0) {
      return [] // No images to upload
    }

    let successCount = 0
    let failedCount = 0
    let githubUrls: string[] = []

    for (let i = 0; i < allFiles.length; i++) {
      const previewUrl = allFiles[i]
      try {
        // Convert preview URL to File
        const response = await fetch(previewUrl)
        const blob = await response.blob()
        const file = new File([blob], `image_${i}.jpg`, { type: blob.type })

        const res = await imagesApi.uploadToGitHub(file)
        if (res.data.success) {
          githubUrls.push(res.data.image_url)
          successCount++
        } else {
          failedCount++
          toast.error(`⚠️ صورة ${i + 1} فشلت: ${res.data.error}`)
        }
      } catch (err: any) {
        failedCount++
        toast.error(`⚠️ صورة ${i + 1} فشلت: ${err?.response?.data?.error || err.message}`)
      }
    }

    if (successCount > 0) {
      // Update image URLs with GitHub URLs
      if (githubUrls.length > 0) {
        setMainImageUrl(githubUrls[0])
        setExtraImageUrls(githubUrls.slice(1))
      }
    }

    if (failedCount > 0 && successCount === 0) {
      throw new Error(`فشل رفع جميع الصور (${failedCount} صورة)`)
    }

    return githubUrls
  }

  const handleExtraImageUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    // Filter valid files
    const validFiles = Array.from(files).filter(file => {
      if (!file.type.startsWith('image/')) {
        toast.error(`الملف ${file.name} مش صورة`)
        return false
      }
      if (file.size > 5 * 1024 * 1024) {
        toast.error(`الملف ${file.name} أكبر من 5MB`)
        return false
      }
      return true
    })

    if (validFiles.length === 0) return

    // Check if we have space for all files
    const remainingSlots = 8 - extraImageUrls.length - extraImagePreviews.length
    const filesToUpload = validFiles.slice(0, remainingSlots)

    if (validFiles.length > remainingSlots) {
      toast.error(`⚠️ فيه ${validFiles.length - remainingSlots} صورة مش هتترفع - مفيش أماكن فاضية كافية`)
    }

    // Upload each file
    let uploadedCount = 0
    for (const file of filesToUpload) {
      // Preview
      const previewUrl = await new Promise<string>((resolve) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result as string)
        reader.readAsDataURL(file)
      })

      setUploadingImages(true)
      try {
        const res = await imagesApi.upload(file)
        setExtraImageUrls(prev => [...prev, res.data.url])
        setExtraImagePreviews(prev => [...prev, previewUrl])
        uploadedCount++
      } catch {
        toast.error(`فشل رفع الصورة: ${file.name}`)
      }
    }

    setUploadingImages(false)
    if (uploadedCount > 0) {
      toast.success(`✅ تم رفع ${uploadedCount} صورة`)
    }

    // Reset input so same files can be re-selected
    e.target.value = ''
  }, [extraImageUrls.length, extraImagePreviews.length])

  const removeExtraImage = useCallback((index: number) => {
    setExtraImageUrls(prev => prev.filter((_, i) => i !== index))
    setExtraImagePreviews(prev => prev.filter((_, i) => i !== index))
  }, [])

  // ==================== Build Payload ====================
  const buildPayload = (variantIndex = 0, overrideImages?: string[], isDraft = false) => {
    const allImages = overrideImages || [mainImageUrl, ...extraImageUrls].filter(Boolean)
    // Unique SKU: timestamp + variant index + 2 random segments separated by dashes to prevent duplicates
    const skuTimestamp = Date.now()
    const rand1 = Math.random().toString(36).substring(2, 5).toUpperCase()
    const rand2 = Math.random().toString(36).substring(2, 5).toUpperCase()
    
    const aiData = aiProducts[variantIndex] || null

    let finalNameAr = required.name_ar.trim()
    let finalNameEn = required.name_en.trim()
    let finalDescAr = required.description_ar.trim()
    let finalDescEn = required.description_en.trim()

    // If AI generated this variant, use its unique data instead of repeating
    if (aiData) {
      finalNameAr = aiData.name_ar || finalNameAr
      finalNameEn = aiData.name_en || finalNameEn
      finalDescAr = aiData.description_ar || finalDescAr
      finalDescEn = aiData.description_en || finalDescEn
    } else if (variantIndex > 0) {
      // Fallback only if no AI data exists
      finalNameAr += ` - نسخة ${variantIndex + 1}`
      finalNameEn += ` - Copy ${variantIndex + 1}`
    }

    const sku = isEditMode ? editProduct.sku : (aiData?.suggested_sku || `AUTO-${skuTimestamp}-${variantIndex}-${rand1}-${rand2}`)

    return {
      sku,
      status: isDraft ? 'incomplete' : 'active',
      seller_id: selectedSellerId || undefined,
      name: finalNameAr,
      name_ar: finalNameAr,
      name_en: finalNameEn,
      brand: required.brand || DEFAULT_VALUES.brand,
      price: parseFloat(required.price) || 0, // FIX: default to 0 if empty (backend accepts ge=0)
      quantity: parseInt(required.quantity) || 0, // FIX: default to 0 if empty
      currency: 'EGP', // Default currency
      product_type: required.product_type,
      amazon_product_type: aiData?.amazon_product_type || undefined,
      condition: required.condition,
      fulfillment_channel: 'MFN', // ثابت - الشحن على البائع
      ean: required.id_type === 'EAN' && !required.has_product_identifier ? required.ean : '',
      upc: required.id_type === 'UPC' && !required.has_product_identifier ? required.ean : '',
      has_product_identifier: required.has_product_identifier,
      description: finalDescAr,
      description_ar: finalDescAr,
      description_en: finalDescEn,
      bullet_points: required.bullet_points.filter(bp => bp.trim().length > 0),
      manufacturer: required.manufacturer || DEFAULT_VALUES.brand,
      model_number: required.model_number || required.name_en.trim(),
      model_name: required.model_name || required.name_ar.trim(), // [NEW]
      country_of_origin: required.country_of_origin,
      browse_node_id: required.browse_node_id,
      material: optional.material,
      number_of_items: parseInt(optional.unit_count) || 1, // Default to 1 if empty
      unit_count: { value: parseFloat(required.unit_count) || 1, type: required.unit_count_type },
      included_components: required.included_components || required.name_en.trim(),
      target_audience: optional.target_audience,
      compare_price: optional.compare_price ? parseFloat(optional.compare_price) : undefined,
      cost: optional.cost ? parseFloat(optional.cost) : undefined,
      sale_price: optional.sale_price ? parseFloat(optional.sale_price) : undefined,
      sale_start_date: optional.sale_start_date || undefined,
      sale_end_date: optional.sale_end_date || undefined,
      handling_time: parseInt(optional.handling_time) || 0,
      package_quantity: parseInt(optional.package_quantity) || 1,
      weight: parseFloat(required.item_weight) || undefined,
      dimensions: {
        length: parseFloat(required.package_length) || 0,
        width: parseFloat(required.package_width) || 0,
        height: parseFloat(required.package_height) || 0,
        unit: 'centimeters',
      },
      keywords: optional.keywords,
      images: allImages,
      // Technical Specifications (Electrical)
      voltage: optional.voltage,
      wattage: optional.wattage,
      operating_frequency: optional.operating_frequency,
      power_plug_type: optional.power_plug_type,
    }
  }

  // ==================== Submit Handlers ====================
  const handleSave = async (isDraft = false) => {
    if (!isDraft) {
      const { valid, errors } = validate()
      if (!valid) {
        toast.error(errors.join('\n'))
        return
      }
    } else {
      // Minimal validation for draft: at least a name
      if (!required.name_ar.trim() && !required.name_en.trim()) {
        toast.error('⚠️ لازم تكتب اسم المنتج على الأقل عشان تحفظه كمسودة')
        return
      }
    }

    setSubmitting(true)
    try {
      // Use images from state (GitHub URLs if uploaded, otherwise local paths)
      const imageUrls = [mainImageUrl, ...extraImageUrls].filter(Boolean)

      // ⚠️ IMPORTANT: Use the user's explicit listingCopies value
      // - If AI generated 3 products AND user didn't change listingCopies → actualCopies = 3
      // - If user manually changed listingCopies to 1 → actualCopies = 1 (respects user choice)
      const actualCopies = listingCopies

      const payloads = []
      for (let i = 0; i < actualCopies; i++) {
        payloads.push(buildPayload(i, imageUrls, isDraft))
      }

      // EDIT MODE: Update existing product
      if (isEditMode && editProduct?.id) {
        const updatePayload = { ...payloads[0], id: undefined } // Remove id field

        // Check if seller changed
        const sellerChanged = editProduct.seller_id && editProduct.seller_id !== selectedSellerId
        if (sellerChanged) {
          const oldSeller = sellers.find(s => s.id === editProduct.seller_id)
          const newSeller = sellers.find(s => s.id === selectedSellerId)
          toast.info(`🔄 جاري نقل المنتج من "${oldSeller?.display_name || 'التاجر القديم'}" إلى "${newSeller?.display_name || 'التاجر الجديد'}"`)
        }

        await productsApi.update(editProduct.id, updatePayload)
        toast.success('✅ تم تحديث المنتج بنجاح!')
        navigate('/products')
        return
      }

      // CREATE MODE: Create new product(s)
      if (actualCopies === 1) {
        await createMutation.mutateAsync(payloads[0] as any)
        toast.success('✅ تم حفظ المنتج!')
      } else {
        toast.loading(`جاري إنشاء ${actualCopies} منتج...`)
        let successCount = 0
        const failedProducts: Array<{ index: number; error: string }> = []

        for (let i = 0; i < payloads.length; i++) {
          try {
            await createMutation.mutateAsync(payloads[i] as any)
            successCount++
          } catch (err: any) {
            // FIX: Properly extract error message from FastAPI 422 response
            let errorMsg = 'خطأ غير معروف'
            const responseDetail = err?.response?.data?.detail

            if (Array.isArray(responseDetail)) {
              // FastAPI validation errors (422) — each item: {type, loc, msg, input, ctx}
              errorMsg = responseDetail.map((e: any) => {
                const field = Array.isArray(e.loc) ? e.loc.join('.') : String(e.loc || '')
                const msg = String(e.msg || e.message || '')
                return `${field}: ${msg}`
              }).join('\n')
            } else if (typeof responseDetail === 'string') {
              errorMsg = responseDetail
            } else if (responseDetail && typeof responseDetail === 'object') {
              // Object detail — stringify it safely
              errorMsg = String(JSON.stringify(responseDetail, null, 2))
            } else if (typeof err?.message === 'string') {
              errorMsg = err.message
            }

            // SAFETY: Ensure errorMsg is always a string (not object/array)
            const safeErrorMsg = typeof errorMsg === 'string' ? errorMsg : String(errorMsg)
            failedProducts.push({ index: i + 1, error: safeErrorMsg })
          }
        }

        toast.dismiss()

        if (successCount > 0) {
          toast.success(`✅ تم إنشاء ${successCount} من ${actualCopies} منتج`)
        }

        if (failedProducts.length > 0) {
          const errorDetails = failedProducts.map(f => `المنتج ${f.index}: ${f.error}`).join('\n')
          toast.error(`❌ فشل ${failedProducts.length} منتج:\n${errorDetails}`, { duration: 12000 })
        }

        if (successCount === 0) {
          toast.error('فشل إنشاء أي منتج - تحقق من البيانات', { duration: 10000 })
        }
      }

      navigate('/products')
    } catch (error: any) {
      // FIX: Proper error message extraction for 422 validation errors
      let errorMsg = 'حدث خطأ غير معروف'
      const detail = error?.response?.data?.detail

      if (Array.isArray(detail)) {
        // FastAPI validation errors (422)
        errorMsg = detail.map((err: any) => {
          const field = Array.isArray(err.loc) ? err.loc.join('.') : String(err.loc || '')
          const msg = String(err.msg || err.message || '')
          return `${field}: ${msg}`
        }).join('\n')
      } else if (typeof detail === 'string') {
        errorMsg = detail
      } else if (typeof detail === 'object' && detail !== null) {
        errorMsg = JSON.stringify(detail, null, 2)
      } else if (error?.response?.data?.message) {
        errorMsg = String(error.response.data.message)
      } else if (typeof error?.message === 'string') {
        errorMsg = error.message
      }

      // SAFETY: Ensure errorMsg is always a string
      const safeMsg = typeof errorMsg === 'string' ? errorMsg : String(errorMsg)
      toast.error('فشل الحفظ: ' + safeMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitToAmazon = async () => {
    const { valid, errors } = validate()
    if (!valid) {
      toast.error(errors.join('\n'))
      return
    }

    // MANDATORY: Check if images are on CDN (Cloudinary or GitHub)
    const allImageUrls = [mainImageUrl, ...extraImageUrls].filter(Boolean)
    const hasImages = allImageUrls.length > 0
    const allOnCDN = hasImages && allImageUrls.every(
      url => url.startsWith('https://') && (
        url.includes('raw.githubusercontent.com') ||
        url.includes('res.cloudinary.com')
      )
    )

    if (hasImages && !allOnCDN) {
      toast.error('❌ لازم ترفع الصور على GitHub/Cloudinary الأول — اضغط "📤 حفظ على GitHub"')
      return
    }

    setSubmitting(true)
    try {
      const actualCopies = listingCopies
      const payloads = []
      for (let i = 0; i < actualCopies; i++) {
        payloads.push(buildPayload(i, allImageUrls))
      }

      let successCount = 0
      const failedProducts: Array<{ index: number; error: string }> = []
      
      if (actualCopies > 1) {
        toast.loading(`جاري حفظ وإرسال ${actualCopies} منتج لأمازون...`)
      }

      for (let i = 0; i < payloads.length; i++) {
        try {
          // Save to DB with GitHub URLs
          const product = await createMutation.mutateAsync(payloads[i] as any)
          const productId = product.id || product.data?.id

          // Submit to Amazon via SP-API
          await productsApi.submitToAmazon(productId)
          successCount++
        } catch (error: any) {
          let errorMsg = error?.response?.data?.detail
            || error?.response?.data?.message
            || (typeof error?.message === 'string' ? error.message : 'خطأ غير معروف')
          if (Array.isArray(errorMsg)) {
            errorMsg = errorMsg.map((e: any) => String(e.msg || e.message || '')).join('\n')
          }
          failedProducts.push({ index: i + 1, error: typeof errorMsg === 'string' ? errorMsg : String(errorMsg) })
        }
      }

      toast.dismiss()

      if (successCount > 0) {
        toast.success(`✅ تم إرسال ${successCount} منتج لـ Amazon بنجاح!`)
      }
      
      if (failedProducts.length > 0) {
        const errorDetails = failedProducts.map(f => `رقم ${f.index}: ${f.error}`).join('\n')
        toast.error(`❌ فشل ${failedProducts.length} منتج:\n${errorDetails}`, { duration: 15000 })
      }

      navigate('/listings')
    } catch (error: any) {
      toast.dismiss()
      toast.error('حدث خطأ فادح غير متوقع')
    } finally {
      setSubmitting(false)
    }
  }

  const handlePreview = () => {
    const { valid, errors } = validate()
    if (!valid) {
      toast.error(errors.join('\n'))
      return
    }

    // Check if images are uploaded to a CDN (Cloudinary or GitHub)
    const allImageUrls = [mainImageUrl, ...extraImageUrls].filter(Boolean)
    const hasImages = allImageUrls.length > 0
    const allOnCDN = hasImages && allImageUrls.every(
      url => url.startsWith('https://') && (
        url.includes('raw.githubusercontent.com') ||
        url.includes('res.cloudinary.com')
      )
    )

    const p = buildPayload(0, allImageUrls)
    const summary = {
      'اسم المنتج (عربي)': p.name_ar,
      'اسم المنتج (English)': p.name_en,
      'الباركود': p.ean || p.upc || 'معفي',
      'السعر': `${p.price} EGP`,
      'الكمية': p.quantity,
      'البراند': p.brand,
      'نوع المنتج': p.product_type,
      'الحالة': p.condition,
      'قناة الشحن': p.fulfillment_channel,
      'الصور': p.images.length,
    }

    toast(t => (
      <div className="space-y-2 max-h-60 overflow-auto">
        <h4 className="font-bold text-lg">معاينة البيانات</h4>
        {Object.entries(summary).map(([k, v]) => (
          <div key={k} className="flex justify-between text-sm">
            <span className="text-text-muted">{k}:</span>
            <span className="font-mono">{String(v)}</span>
          </div>
        ))}
      </div>
    ), { duration: 10000 })
  }

  // ==================== Render Page 0: مساعد الذكاء الاصطناعي ====================
  const renderPage0 = (
    <div className="space-y-8">
      {/* AI Assistant Panel */}
      <div className="max-w-3xl mx-auto">
        <AIAssistantPanel
          onProductsGenerated={handleAiProductsGenerated}
          onCopiesChange={setListingCopies}
        />
      </div>

      <div className="max-w-3xl mx-auto">
        {/* Manual Entry Button */}
        <div className="text-center pt-4">
          <NeonButton variant="primary" styleType="outline" size="lg" onClick={() => setPage(1)}>
            ← إدخال البيانات يدوياً بدون مساعدة
          </NeonButton>
        </div>
      </div>
    </div>
  )

  // ==================== Render Page 1: الحقول الإجبارية ====================
  const renderPage1 = (
    <div className="space-y-6">
      {/* AI Product Variant Selector (moved from here, but keep if user comes back) */}
      {aiProducts.length > 1 && (
        <div className="rounded-xl neon-card neon-card--accent neon-card--blue p-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-neon-blue" />
            <h4 className="font-medium text-text-primary">المنتجات المولّدة بالذكاء الاصطناعي — غيّر الاختيار</h4>
          </div>
          <div className="flex gap-2 flex-wrap">
            {aiProducts.map((product, i) => (
              <button
                key={i}
                onClick={() => {
                  setSelectedAiProduct(i)
                  fillFormFromAi(product)
                  toast.success(`تم اختيار المنتج ${i + 1}`)
                }}
                className={`px-3 py-2 rounded-xl text-sm transition-colors ${selectedAiProduct === i
                  ? 'bg-amazon-orange text-white shadow-lg'
                  : 'bg-bg-elevated text-text-secondary border border-border-subtle hover:border-amazon-orange/50'
                  }`}
              >
                المنتج {i + 1}: {product.name_ar.slice(0, 30)}{product.name_ar.length > 30 ? '...' : ''}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* الهوية الأساسية */}
      <div className="p-4 neon-card neon-card--accent neon-card--blue">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <Tag className="w-5 h-5" /> الهوية الأساسية
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="اسم السلعة (عربي)" required hint="الاسم بالعربي — يظهر على صفحة المنتج" isAiGenerated={selectedAiProduct !== null}>
            <TextInput
              value={required.name_ar}
              onChange={v => setRequired(prev => ({ ...prev, name_ar: v }))}
              placeholder="مثال: خلاط كهربائي 500 واط"
            />
          </Field>
          <Field label="اسم السلعة (English)" required hint="الاسم بالإنجليزي — مطلوب لـ Amazon" isAiGenerated={selectedAiProduct !== null}>
            <TextInput
              value={required.name_en}
              onChange={v => setRequired(prev => ({ ...prev, name_en: v }))}
              placeholder="Example: Electric Hand Mixer 500W"
            />
          </Field>
        </div>

        <Field label="نوع المنتج" required hint="اختر الفئة المناسبة — الفئات المتاحة تتغير حسب النوع" isAiGenerated={selectedAiProduct !== null}>
          <SelectInput
            value={required.product_type}
            onChange={v => {
              const newNodes = BROWSE_NODES_BY_TYPE[v] || []
              setRequired(prev => ({
                ...prev,
                product_type: v,
                browse_node_id: newNodes[0]?.value || prev.browse_node_id
              }))
            }}
            options={PRODUCT_TYPE_CATEGORIES as any}
          />
        </Field>

        <Field label="الباركود" required={!required.has_product_identifier} hint="EAN (13 رقم) أو UPC (12 رقم) — إجباري من Amazon للتعرف على المنتج" isAiGenerated={selectedAiProduct !== null}>
          {/* GTIN Exemption Checkbox */}
          <label className="flex items-center gap-2 mb-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={required.has_product_identifier}
              onChange={e => setRequired(prev => ({ ...prev, has_product_identifier: e.target.checked }))}
              className="w-4 h-4 rounded accent-blue-500"
            />
            <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
              ✅ هذا المنتج لا يحتوي على رقم منتج (معفى من الباركود)
            </span>
          </label>

          <div className={`transition-opacity ${required.has_product_identifier ? 'opacity-50 pointer-events-none' : ''}`}>
            <div className="mb-2">
              <RadioGroup
                name="id_type"
                options={ID_TYPES.filter(t => ['EAN', 'UPC'].includes(t.value)) as any}
                value={required.id_type}
                onChange={v => setRequired(prev => ({ ...prev, id_type: v }))}
              />
            </div>
            <TextInput
              value={required.ean}
              onChange={v => setRequired(prev => ({ ...prev, ean: v.replace(/\D/g, '').slice(0, required.id_type === 'UPC' ? 12 : 13) }))}
              placeholder={required.id_type === 'UPC' ? 'أدخل 12 رقم' : 'أدخل 13 رقم'}
              type="text"
            />
          </div>
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Field label="🔒 البراند" required hint="العلامة التجارية">
            <TextInput
              value={required.brand}
              onChange={v => setRequired(prev => ({ ...prev, brand: v }))}
              placeholder="Generic"
            />
          </Field>
          <Field label="رقم الموديل" required hint="Model Number">
            <TextInput
              value={required.model_number}
              onChange={v => setRequired(prev => ({ ...prev, model_number: v }))}
              placeholder={required.name_en || 'SKU'}
            />
          </Field>
          <Field label="اسم الموديل" required hint="Model Name (إجباري من أمازون)">
            <TextInput
              value={required.model_name}
              onChange={v => setRequired(prev => ({ ...prev, model_name: v }))}
              placeholder="مثال: Mac-Pro-2024"
            />
          </Field>
          <Field label="🔒 المصنع" required hint="Manufacturer">
            <TextInput
              value={required.manufacturer}
              onChange={v => setRequired(prev => ({ ...prev, manufacturer: v }))}
              placeholder="Generic"
            />
          </Field>
        </div>

        <Field label="🔒 بلد المنشأ" required hint="البلد اللي اتصنع فيها المنتج — ⚠️ حقل ثابت (AI مش بيغيره)">
          <SelectInput
            value={required.country_of_origin}
            onChange={v => setRequired(prev => ({ ...prev, country_of_origin: v }))}
            options={COUNTRIES as any}
          />
        </Field>
      </div>

      {/* الوصف والتفاصيل */}
      <div className="p-4 neon-card neon-card--accent neon-card--green">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5" /> الوصف والتفاصيل
        </h3>

        <Field label="الوصف (عربي)" required hint="وصف تفصيلي شامل - 3 سطور على الأقل يشرح مميزات المنتج واستخداماته" isAiGenerated={selectedAiProduct !== null}>
          <textarea
            value={required.description_ar}
            onChange={e => setRequired(prev => ({ ...prev, description_ar: e.target.value }))}
            placeholder="مثال: هذا الخلاط كهربائي بقوة 500 واط يأتي مع 5 سرعات مختلفة لتناسب جميع احتياجاتك في المطبخ. مصنوع من مواد عالية الجودة تضمن له المتانة والاستخدام الطويل. مثالي لخلط العجين، تحضير العصائر، وفرم المكونات المختلفة بسهولة تامة."
            rows={4}
            className="neon-input neon-textarea resize-none"
          />
        </Field>

        <Field label="الوصف (English)" required hint="Comprehensive product description - at least 3 lines describing features and benefits" isAiGenerated={selectedAiProduct !== null}>
          <textarea
            value={required.description_en}
            onChange={e => setRequired(prev => ({ ...prev, description_en: e.target.value }))}
            placeholder="Example: This 500W electric hand mixer comes with 5 different speed settings to handle all your kitchen needs. Made from premium quality materials that ensure durability and long-lasting performance. Perfect for mixing dough, preparing smoothies, and chopping ingredients with ease."
            rows={4}
            className="neon-input neon-textarea resize-none"
          />
        </Field>

        <Field label="مميزات المنتج الرئيسية (Bullet Points)" hint="💡 يُنصح بكتابة 5 نقاط كاملة — كل نقطة جملة مفيدة (إجباري لأمازون)" isAiGenerated={selectedAiProduct !== null}>
          <div className="space-y-3">
            {required.bullet_points.map((bp, i) => (
              <div key={i} className="flex gap-2">
                <span className="flex-shrink-0 w-8 h-10 flex items-center justify-center bg-amazon-orange/20 text-amazon-orange text-sm font-bold rounded-xl">
                  {i + 1}
                </span>
                <input
                  type="text"
                  value={bp}
                  onChange={e => {
                    const newBp = [...required.bullet_points]
                    newBp[i] = e.target.value
                    setRequired(prev => ({ ...prev, bullet_points: newBp }))
                  }}
                  placeholder={`النقطة البيعية ${i + 1} - اكتب جملة كاملة تشرح ميزة مهمة...`}
                  className="neon-input flex-1"
                />
              </div>
            ))}
          </div>
        </Field>

        <Field label="الفئة (Browse Node)" required hint={`الفئات المتاحة لـ ${PRODUCT_TYPE_CATEGORIES.find(c => c.value === required.product_type)?.label || 'المنتج'}`}>
          <SelectInput
            value={required.browse_node_id}
            onChange={v => setRequired(prev => ({ ...prev, browse_node_id: v }))}
            options={(BROWSE_NODES_BY_TYPE[required.product_type] || BROWSE_NODES) as any}
          />
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="المكونات المضمنة (Included Components)" required hint="مثال: 1x خلاط، 1x دليل الاستخدام (إجباري)">
            <TextInput
              value={required.included_components}
              onChange={v => setRequired(prev => ({ ...prev, included_components: v }))}
              placeholder={required.name_en || 'مثال: 1x المنتج'}
            />
          </Field>
          <Field label="إحصاء الوحدات (Unit Count)" required>
            <NumberInput
              value={required.unit_count}
              onChange={v => setRequired(prev => ({ ...prev, unit_count: v }))}
              placeholder="1"
              min="1"
            />
          </Field>
        </div>

        <Field label="نوع إحصاء الوحدات (Unit Count Type)" required>
          <SelectInput
            value={required.unit_count_type}
            onChange={v => setRequired(prev => ({ ...prev, unit_count_type: v }))}
            options={UNIT_TYPES as any}
          />
        </Field>
      </div>

      {/* التسعير والكمية */}
      <div className="p-4 neon-card neon-card--accent neon-card--orange">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <DollarSign className="w-5 h-5" /> التسعير والكمية
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="السعر (EGP)" required>
            <div className="relative">
              <NumberInput
                value={required.price}
                onChange={v => setRequired(prev => ({ ...prev, price: v }))}
                placeholder="0.00"
                min="0.01"
                step="0.01"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">ج.م</span>
            </div>
          </Field>
          <Field label="الكمية" required>
            <NumberInput
              value={required.quantity}
              onChange={v => setRequired(prev => ({ ...prev, quantity: v.replace(/\D/g, '') }))}
              placeholder="0"
              min="0"
            />
          </Field>
        </div>
      </div>

      {/* الشحن والأبعاد */}
      <div className="p-4 neon-card neon-card--accent neon-card--pink">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <Truck className="w-5 h-5" /> الشحن والأبعاد
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="حالة المنتج" required>
            <SelectInput
              value={required.condition}
              onChange={v => setRequired(prev => ({ ...prev, condition: v }))}
              options={CONDITIONS as any}
            />
          </Field>
          {/* قناة الشحن ثابتة - MFN (الشحن على البائع) */}
          <Field label="قناة الشحن" hint="ثابت: الشحن على البائع (MFN)">
            <div className="neon-input bg-bg-tertiary opacity-75 cursor-not-allowed select-none">
              📦 الشحن على البائع (MFN)
            </div>
            <input type="hidden" value="MFN" />
          </Field>
        </div>

        <div className="mt-4">
          <h4 className="text-sm font-semibold text-text-secondary mb-2">أبعاد الباكج (سم) *</h4>
          <div className="grid grid-cols-3 gap-3">
            <Field label="الطول">
              <NumberInput
                value={required.package_length}
                onChange={v => setRequired(prev => ({ ...prev, package_length: v }))}
                placeholder="25"
                min="1"
                step="0.1"
              />
            </Field>
            <Field label="العرض">
              <NumberInput
                value={required.package_width}
                onChange={v => setRequired(prev => ({ ...prev, package_width: v }))}
                placeholder="10"
                min="1"
                step="0.1"
              />
            </Field>
            <Field label="الارتفاع">
              <NumberInput
                value={required.package_height}
                onChange={v => setRequired(prev => ({ ...prev, package_height: v }))}
                placeholder="15"
                min="1"
                step="0.1"
              />
            </Field>
          </div>
        </div>

        <div className="mt-4">
          <h4 className="text-sm font-semibold text-text-secondary mb-2">الأوزان (كجم) *</h4>
          <div className="grid grid-cols-2 gap-3">
            <Field label="وزن المنتج">
              <NumberInput
                value={required.item_weight}
                onChange={v => setRequired(prev => ({ ...prev, item_weight: v }))}
                placeholder="0.5"
                min="0.1"
                step="0.1"
              />
            </Field>
            <Field label="وزن الباكج">
              <NumberInput
                value={required.package_weight}
                onChange={v => setRequired(prev => ({ ...prev, package_weight: v }))}
                placeholder="0.7"
                min="0.1"
                step="0.1"
              />
            </Field>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <Field label="عدد الصناديق" required>
            <NumberInput
              value={required.number_of_boxes}
              onChange={v => setRequired(prev => ({ ...prev, number_of_boxes: v }))}
              placeholder="1"
              min="1"
            />
          </Field>
        </div>
      </div>

      <NeonButton variant="primary" fullWidth onClick={() => setPage(2)}>
        التالي: الحقول الاختيارية ←
      </NeonButton>
    </div>
  )

  // ==================== Render Page 2: الحقول الاختيارية ====================
  const renderPage2 = (
    <div className="space-y-6">
      {/* الكلمات المفتاحية */}
      <div className="neon-card p-4">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <Tag className="w-5 h-5" /> الكلمات المفتاحية
        </h3>

        <Field label="الكلمات المفتاحية" hint="أضف حتى 15 كلمة - اكتب واضغط Enter">
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={optional.keywordInput}
              onChange={e => setOptional(prev => ({ ...prev, keywordInput: e.target.value }))}
              onKeyDown={e => {
                if (e.key === 'Enter' && optional.keywordInput.trim()) {
                  e.preventDefault()
                  if (optional.keywords.length < 15) {
                    setOptional(prev => ({
                      ...prev,
                      keywords: [...prev.keywords, prev.keywordInput.trim()],
                      keywordInput: '',
                    }))
                  }
                }
              }}
              placeholder="اكتب كلمة واضغط Enter..."
              className="neon-input flex-1"
            />
          </div>
          {optional.keywords.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {optional.keywords.map((kw, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-neon-blue/10 text-neon-blue rounded-xl text-sm flex items-center gap-1"
                >
                  {kw}
                  <button
                    onClick={() => setOptional(prev => ({
                      ...prev,
                      keywords: prev.keywords.filter((_, idx) => idx !== i),
                    }))}
                    className="hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </Field>
      </div>

      {/* تفاصيل إضافية */}
      <div className="neon-card p-4">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <Package className="w-5 h-5" /> تفاصيل إضافية
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="المادة المصنوع منها" hint="مثال: بلاستيك، ستانلس ستيل">
            <TextInput
              value={optional.material}
              onChange={v => setOptional(prev => ({ ...prev, material: v }))}
              placeholder="المادة..."
            />
          </Field>
          <Field label="الفئة المستهدفة" hint="مثال: Adults, Kids">
            <TextInput
              value={optional.target_audience}
              onChange={v => setOptional(prev => ({ ...prev, target_audience: v }))}
              placeholder="الفئة المستهدفة..."
            />
          </Field>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <Field label="أيام التجهيز" hint="عدد أيام التحضير للشحن">
            <NumberInput
              value={optional.handling_time}
              onChange={v => setOptional(prev => ({ ...prev, handling_time: v }))}
              placeholder="1"
              min="0"
            />
          </Field>
          <Field label="عدد القطع بالباكج">
            <NumberInput
              value={optional.package_quantity}
              onChange={v => setOptional(prev => ({ ...prev, package_quantity: v }))}
              placeholder="1"
              min="1"
            />
          </Field>
        </div>
      </div>
      
      {/* المواصفات الفنية (كهرباء) */}
      <div className="neon-card p-4 neon-card--accent neon-card--blue">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" /> المواصفات الفنية (للمنتجات الكهربائية)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="الفولت (Voltage)" hint="مثال: 220">
            <TextInput
              value={optional.voltage}
              onChange={v => setOptional(prev => ({ ...prev, voltage: v }))}
              placeholder="220"
            />
          </Field>
          <Field label="الواط (Wattage)" hint="مثال: 1500">
            <TextInput
              value={optional.wattage}
              onChange={v => setOptional(prev => ({ ...prev, wattage: v }))}
              placeholder="1500"
            />
          </Field>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <Field label="تردد الجهد (Frequency)" hint="مثال: 50 أو 60">
            <TextInput
              value={optional.operating_frequency}
              onChange={v => setOptional(prev => ({ ...prev, operating_frequency: v }))}
              placeholder="50"
            />
          </Field>
          <Field label="نوع القابس (Plug Type)" hint="مثال: Type C, Type G">
            <SelectInput
              value={optional.power_plug_type}
              onChange={v => setOptional(prev => ({ ...prev, power_plug_type: v }))}
              options={[
                { value: '', label: 'اختر نوع القابس...' },
                { value: 'type_c_2pin', label: 'Type C (دبوسين - أغلب مصر)' },
                { value: 'type_g_3pin', label: 'Type G (3 دبابيس - إنجليزي)' },
                { value: 'type_a_2pin', label: 'Type A (دبوسين مسطح - أمريكي)' },
                { value: 'not_applicable', label: 'غير متوفر / لا يحتاج' },
              ]}
            />
          </Field>
        </div>
      </div>

      {/* التسعير الإضافي */}
      <div className="neon-card p-4">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <DollarSign className="w-5 h-5" /> تسعير إضافي
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="سعر قبل الخصم" hint="السعر الأصلي قبل الخصم">
            <div className="relative">
              <NumberInput
                value={optional.compare_price}
                onChange={v => setOptional(prev => ({ ...prev, compare_price: v }))}
                placeholder="0.00"
                min="0.01"
                step="0.01"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">ج.م</span>
            </div>
          </Field>
          <Field label="التكلفة" hint="تكلفة الشراء">
            <div className="relative">
              <NumberInput
                value={optional.cost}
                onChange={v => setOptional(prev => ({ ...prev, cost: v }))}
                placeholder="0.00"
                min="0"
                step="0.01"
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">ج.م</span>
            </div>
          </Field>
        </div>

        <div className="mt-4 p-3 neon-card neon-card--accent neon-card--yellow">
          <h4 className="text-sm font-semibold text-text-primary mb-3">تخفيض (اختياري)</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Field label="سعر التخفيض">
              <NumberInput
                value={optional.sale_price}
                onChange={v => setOptional(prev => ({ ...prev, sale_price: v }))}
                placeholder="0.00"
                min="0.01"
                step="0.01"
              />
            </Field>
            <Field label="من تاريخ">
              <input
                type="date"
                value={optional.sale_start_date}
                onChange={e => setOptional(prev => ({ ...prev, sale_start_date: e.target.value }))}
                className="neon-input"
              />
            </Field>
            <Field label="إلى تاريخ">
              <input
                type="date"
                value={optional.sale_end_date}
                onChange={e => setOptional(prev => ({ ...prev, sale_end_date: e.target.value }))}
                className="neon-input"
              />
            </Field>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => setPage(1)}
          className="neon-btn neon-btn--primary neon-btn--sm"
        >
          → السابق
        </button>
        <button
          onClick={() => setPage(3)}
          className="flex-1 neon-btn neon-btn--primary font-bold"
        >
          التالي: الصور والإرسال ←
        </button>
      </div>
    </div>
  )

  // ==================== Render Page 3: الصور والإرسال ====================
  const renderPage3 = (
    <div className="space-y-6">
      {/* الصورة الرئيسية */}
      <div className="neon-card p-4">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <ImageIcon className="w-5 h-5" /> الصورة الرئيسية
        </h3>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleMainImageUpload}
          className="hidden"
        />

        {mainImagePreview || mainImageUrl ? (
          <div className="relative">
            <img
              src={mainImagePreview || mainImageUrl}
              alt="Main product"
              className="w-full h-64 object-contain bg-bg-tertiary rounded-lg"
            />
            <button
              onClick={() => {
                setMainImageUrl('')
                setMainImagePreview('')
              }}
              className="absolute top-2 right-2 p-2 bg-neon-red text-white rounded-full hover:bg-neon-red/80 transition-all shadow-lg z-10"
              title="إزالة الصورة"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingImages}
            className="neon-dropzone"
          >
            {uploadingImages ? (
              <Loader2 className="w-8 h-8 animate-spin text-amazon-orange" />
            ) : (
              <>
                <Upload className="w-8 h-8 text-text-muted" />
                <div className="text-center">
                  <p className="text-sm font-medium text-text-secondary">اضغط لاختيار صورة</p>
                  <p className="text-xs text-text-muted">1000×1000 بكسل على الأقل</p>
                </div>
              </>
            )}
          </button>
        )}
      </div>

      {/* صور إضافية */}
      <div className="neon-card p-4">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <ImageIcon className="w-5 h-5" /> صور إضافية ({extraImageUrls.length}/8)
        </h3>

        <input
          ref={extraFileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleExtraImageUpload}
          className="hidden"
        />

        <div className="grid grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => {
            const hasImage = i < extraImagePreviews.length || i < extraImageUrls.length
            const preview = extraImagePreviews[i]
            const url = extraImageUrls[i]

            return (
              <div key={i} className="relative aspect-square">
                {hasImage ? (
                  <>
                    <img
                      src={preview || url}
                      alt={`Extra ${i + 1}`}
                      className="w-full h-full object-cover rounded-lg"
                    />
                    <button
                      onClick={() => removeExtraImage(i)}
                      className="absolute top-1 right-1 p-1 bg-neon-red text-white rounded-full hover:bg-neon-red/80 transition-all shadow-md z-10"
                      title="إزالة الصورة"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => extraFileInputRef.current?.click()}
                    disabled={uploadingImages}
                    className="w-full h-full border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg flex items-center justify-center hover:border-blue-500 transition-colors"
                  >
                    <Upload className="w-6 h-6 text-text-muted" />
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* عدد الإعلانات */}
      <div className="neon-card p-4">
        <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
          <Package className="w-5 h-5" /> 🔢 عدد العروض / الإعلانات
        </h3>

        <Field label="عدد النسخ المراد إنشاؤها" hint={`🔗 هذا الرقم يساوي عدد العروض = عدد الإعلانات = ${aiProducts.length > 0 ? aiProducts.length + ' (من AI)' : '1'}`}>
          <NumberInput
            value={String(listingCopies)}
            onChange={v => {
              const newVal = Math.min(50, Math.max(1, parseInt(v) || 1))
              setListingCopies(newVal)
              // Warn if mismatch with AI products
              if (aiProducts.length > 0 && newVal !== aiProducts.length) {
                toast.error(`⚠️ عدد النسخ (${newVal}) مش يساوي عدد منتجات AI (${aiProducts.length})`)
              }
            }}
            placeholder="1"
            min="1"
          />
        </Field>

        {/* Match indicator */}
        {aiProducts.length > 0 && (
          <div className={`mt-3 p-2 rounded-xl text-sm flex items-center gap-2 ${listingCopies === aiProducts.length
            ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20'
            : 'bg-neon-red/10 text-neon-red border border-neon-red/20'
            }`}>
            {listingCopies === aiProducts.length ? (
              <>✅ متطابق: {listingCopies} نسخة = {aiProducts.length} منتج AI</>
            ) : (
              <>⚠️ غير متطابق: {listingCopies} نسخة ≠ {aiProducts.length} منتج AI</>
            )}
          </div>
        )}
      </div>

      {/* 📤 حفظ الصور على GitHub */}
      <div className="neon-card p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
              <Globe className="w-5 h-5 text-neon-cyan" /> حفظ الصور على GitHub
            </h3>
            <p className="text-sm text-text-secondary mt-1">
              الصور لازم تترفع على GitHub عشان Amazon يقدر يشوفها
            </p>
          </div>
          <NeonButton
            variant="info"
            size="sm"
            onClick={handleUploadToGitHub}
            isLoading={uploadingToGitHub}
            disabled={uploadingToGitHub || (!mainImagePreview && extraImagePreviews.length === 0)}
          >
            <Upload className="w-4 h-4" />
            {uploadingToGitHub ? 'جاري الرفع...' : '📤 حفظ على GitHub'}
          </NeonButton>
        </div>
        {/* Check if images are on CDN (Cloudinary or GitHub) */}
        {mainImageUrl && (mainImageUrl.includes('raw.githubusercontent.com') || mainImageUrl.includes('res.cloudinary.com')) && (
          <div className="mt-3 p-2 rounded-xl text-sm bg-neon-green/10 text-neon-green border border-neon-green/20">
            ✅ الصور محفوظة على CDN وجاهزة للإرسال
          </div>
        )}
        {mainImagePreview && !mainImageUrl.includes('raw.githubusercontent.com') && !mainImageUrl.includes('res.cloudinary.com') && (
          <div className="mt-3 p-2 rounded-xl text-sm bg-neon-yellow/10 text-neon-yellow border border-neon-yellow/20">
            ⚠️ الصور محفوظة محلياً بس — لازم ترفع على GitHub قبل الإرسال لـ Amazon
          </div>
        )}
      </div>

      {/* الأزرار */}
      <div className="flex flex-col gap-3">
        <NeonButton variant="warning" fullWidth onClick={handlePreview}>
          <Eye className="w-5 h-5" /> معاينة البيانات
        </NeonButton>

        {/* Helper: check if images are on CDN */}
        {(() => {
          const allUrls = [mainImageUrl, ...extraImageUrls].filter(Boolean)
          const hasImages = allUrls.length > 0
          const allOnCDN = hasImages && allUrls.every(
            url => url.startsWith('https://') && (
              url.includes('raw.githubusercontent.com') ||
              url.includes('res.cloudinary.com')
            )
          )
          const hasMainImage = !!mainImageUrl
          return (
            <>
              <NeonButton
                variant="info"
                styleType="outline"
                fullWidth
                isLoading={submitting}
                onClick={() => handleSave(true)}
              >
                <Save className="w-5 h-5" /> حفظ مؤقت (مسودة)
              </NeonButton>

              <NeonButton
                variant="success"
                fullWidth
                isLoading={submitting}
                onClick={() => handleSave(false)}
                disabled={!hasMainImage || (hasImages && !allOnCDN)}
              >
                <Save className="w-5 h-5" /> حفظ في المخزون
              </NeonButton>

              <NeonButton
                variant="amazon"
                fullWidth
                isLoading={submitting}
                onClick={handleSubmitToAmazon}
                disabled={!hasMainImage || (hasImages && !allOnCDN)}
              >
                <Globe className="w-5 h-5" /> حفظ وإرسال لـ Amazon
              </NeonButton>

              {/* Warning message if buttons are disabled */}
              {!hasMainImage && (
                <div className="p-3 rounded-xl text-sm bg-neon-red/10 text-neon-red border border-neon-red/20 text-center font-bold">
                  ⚠️ الصورة الرئيسية مطلوبة — يرجى رفع الصورة بالأعلى
                </div>
              )}
              {hasMainImage && !allOnCDN && (
                <div className="p-3 rounded-xl text-sm bg-neon-yellow/10 text-neon-yellow border border-neon-yellow/20 text-center">
                  ⚠️ لازم ترفع الصور على GitHub/Cloudinary الأول — اضغط "📤 حفظ على GitHub" بالأعلى
                </div>
              )}
              {!hasImages && (
                <div className="p-3 rounded-xl text-sm bg-neon-yellow/10 text-neon-yellow border border-neon-yellow/20 text-center">
                  ⚠️ لازم ترفع صور المنتج الأول
                </div>
              )}
            </>
          )
        })()}
      </div>

      <button
        onClick={() => setPage(2)}
        className="neon-btn neon-btn--primary neon-btn--sm w-full"
      >
        → السابق
      </button>
    </div>
  )

  // ==================== Main Render ====================
  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">
              {isEditMode ? 'تعديل المنتج' : 'إضافة منتج جديد'}
            </h1>
            <p className="text-text-secondary mt-1">
              {isEditMode ? 'قم بتعديل البيانات المطلوبة' : 'أكمل البيانات لإضافة منتج جديد'}
            </p>
          </div>
          {/* Task 5: SEO Improvement Button (Edit Mode Only) */}
          {isEditMode && (
            <button
              onClick={handleImproveWithAI}
              disabled={improving}
              className="neon-btn neon-btn--primary neon-btn--sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {improving ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> جاري التحسين...</>
              ) : (
                <><Sparkles className="w-4 h-4" /> تحسين بالذكاء الاصطناعي</>
              )}
            </button>
          )}
        </div>
      </div>

      <StepIndicator currentPage={page} onNavigate={setPage} />

      {/* Seller Selector - ظاهر دائماً */}
      {sellers.length > 0 && (
        <div className="mb-4 p-3 neon-card neon-card--accent neon-card--blue">
          <label className="block text-sm font-medium text-text-primary mb-2 flex items-center gap-2">
            <Store className="w-4 h-4" />
            {isEditMode ? 'التاجر الحالي (يمكن تغييره)' : 'اختر الحساب / المتجر'}
          </label>
          <select
            value={selectedSellerId}
            onChange={e => {
              setSelectedSellerId(e.target.value)
              const seller = sellers.find(s => s.id === e.target.value)
              toast.success(`تم اختيار: ${seller?.display_name || seller?.amazon_seller_id || 'التاجر'}`)
            }}
            className="neon-input neon-select"
          >
            {sellers.map(seller => (
              <option key={seller.id} value={seller.id}>
                {seller.display_name || seller.amazon_seller_id || seller.id}
                {seller.is_connected ? ' ✅' : ' ❌'}
              </option>
            ))}
          </select>
          <p className="text-xs text-text-muted mt-1">
            {isEditMode
              ? `⚠️ تغيير التاجر هينقل المنتج من "${sellers.find(s => s.id === editProduct?.seller_id)?.display_name || 'غير محدد'}" إلى "${sellers.find(s => s.id === selectedSellerId)?.display_name || 'غير محدد'}"`
              : `سيتم إنشاء المنتج تحت حساب: ${sellers.find(s => s.id === selectedSellerId)?.display_name || 'غير محدد'}`
            }
          </p>
        </div>
      )}

      <div className="space-y-6">
        {page === 0 && renderPage0}
        {page === 1 && renderPage1}
        {page === 2 && renderPage2}
        {page === 3 && renderPage3}
      </div>
    </div>
  )
}