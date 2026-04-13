/**
 * Product Create Page - Phase 2 Rebuild
 * 
 * 3 Pages Architecture:
 * Page 1: الحقول الإجبارية (29 حقل مطلوب من Amazon)
 * Page 2: الحقول الاختيارية
 * Page 3: الصور + عدد الإعلانات + أزرار الإرسال
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Package, DollarSign, Image as ImageIcon, Save, Loader2,
  AlertTriangle, CheckCircle, Upload, X, FileSpreadsheet, Eye,
  Truck, ShoppingCart, Tag, Globe
} from 'lucide-react'
import { useCreateProduct } from '@/api/hooks'
import { productsApi, imagesApi } from '@/api/endpoints'
import {
  PRODUCT_TYPES, BROWSE_NODES, CONDITIONS, FULFILLMENT_CHANNELS,
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
    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
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
    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
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
    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
  >
    {options.map(opt => (
      <option key={opt.value} value={opt.value}>{opt.label}</option>
    ))}
  </select>
)

const Field = ({
  label, children, required: isRequired, hint,
}: {
  label: string
  children: React.ReactNode
  required?: boolean
  hint?: string
}) => (
  <div className="space-y-1">
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
      {label}
      {isRequired && <span className="text-red-500 mr-1">*</span>}
    </label>
    {children}
    {hint && <p className="text-xs text-gray-500 dark:text-gray-400">{hint}</p>}
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
          className="w-4 h-4"
        />
        <span className="text-sm text-gray-700 dark:text-gray-300">{opt.label}</span>
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
  <div className="flex items-center justify-center gap-2 mb-6">
    {[
      { n: 1, label: 'الحقول الإجبارية', icon: Tag },
      { n: 2, label: 'الحقول الاختيارية', icon: ShoppingCart },
      { n: 3, label: 'الصور والإرسال', icon: ImageIcon },
    ].map(step => {
      const Icon = step.icon
      return (
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

  const editProduct = (location.state as any)?.editProduct as any
  const isEditMode = !!editProduct

  const [page, setPage] = useState(1)
  const [submitting, setSubmitting] = useState(false)

  // ==================== PAGE 1: الحقول الإجبارية ====================
  const [required, setRequired] = useState({
    // Tab 1: الهوية الأساسية
    name_ar: '',
    name_en: '',
    product_type: DEFAULT_VALUES.product_type,
    id_type: DEFAULT_VALUES.id_type as string,
    ean: '',
    brand: DEFAULT_VALUES.brand,
    model_number: '',
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

    // Tab 4: الشحن والأبعاد
    condition: DEFAULT_VALUES.condition,
    fulfillment_channel: DEFAULT_VALUES.fulfillment_channel,
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
  })

  // ==================== PAGE 3: الصور والإرسال ====================
  const [mainImageUrl, setMainImageUrl] = useState<string>('')
  const [mainImagePreview, setMainImagePreview] = useState<string>('')
  const [extraImageUrls, setExtraImageUrls] = useState<string[]>([])
  const [extraImagePreviews, setExtraImagePreviews] = useState<string[]>([])
  const [uploadingImages, setUploadingImages] = useState(false)
  const [listingCopies, setListingCopies] = useState(1)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const extraFileInputRef = useRef<HTMLInputElement>(null)

  // ==================== Edit Mode: Populate fields ====================
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
      })

      const images = editProduct.images || []
      if (images.length > 0) {
        setMainImageUrl(images[0])
        setExtraImageUrls(images.slice(1, 9))
      }
    }
  }, [editProduct])

  // ==================== Validation ====================
  const validate = (): { valid: boolean; errors: string[] } => {
    const errors: string[] = []

    // Page 1 - Required fields
    if (required.name_ar.trim().length < VALIDATION_RULES.name_ar.min)
      errors.push('اسم المنتج بالعربي لازم 3 أحرف على الأقل')
    if (required.name_en.trim().length < VALIDATION_RULES.name_en.min)
      errors.push('اسم المنتج بالإنجليزي لازم 3 أحرف على الأقل')
    if (required.id_type !== 'EXEMPT') {
      const idLen = required.id_type === 'UPC' ? 12 : 13
      if (required.ean.length !== idLen)
        errors.push(`الباركود لازم يكون ${idLen} رقم`)
    }
    if (!required.brand || required.brand.trim().length < 1)
      errors.push('البراند مطلوب')
    if (!required.manufacturer || required.manufacturer.trim().length < 1)
      errors.push('المصنع مطلوب')
    if (required.model_number.trim().length < 1)
      errors.push('رقم الموديل مطلوب')
    if (required.description_ar.trim().length < VALIDATION_RULES.description_ar.min)
      errors.push('الوصف بالعربي لازم 5 أحرف على الأقل')
    if (required.description_en.trim().length < VALIDATION_RULES.description_en.min)
      errors.push('الوصف بالإنجليزي لازم 5 أحرف على الأقل')
    const validBullets = required.bullet_points.filter(bp => bp.trim().length > 0)
    if (validBullets.length === 0)
      errors.push('لازم تكتب نقطة بيعية واحدة على الأقل')
    if (!required.price || parseFloat(required.price) <= 0)
      errors.push('السعر لازم يكون أكبر من صفر')
    if (!mainImageUrl && !isEditMode)
      errors.push('لازم ترفع صورة رئيسية')

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
      toast.warning(`فيه ${validFiles.length - remainingSlots} صورة مش هتترفع - مفيش أماكن فاضية كافية`)
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
  const buildPayload = (variantIndex = 0) => {
    const allImages = [mainImageUrl, ...extraImageUrls].filter(Boolean)
    const variantSuffix = variantIndex > 0 ? ` - Variant ${variantIndex + 1}` : ''

    return {
      sku: isEditMode ? editProduct.sku : `AUTO-${Date.now()}-${variantIndex}`,
      name: `${required.name_en.trim()}${variantSuffix}`,
      name_ar: `${required.name_ar.trim()}${variantSuffix}`,
      name_en: `${required.name_en.trim()}${variantSuffix}`,
      brand: required.brand || DEFAULT_VALUES.brand,
      price: parseFloat(required.price),
      quantity: parseInt(required.quantity),
      product_type: required.product_type,
      condition: required.condition,
      fulfillment_channel: required.fulfillment_channel,
      ean: required.id_type === 'EAN' ? required.ean : '',
      upc: required.id_type === 'UPC' ? required.ean : '',
      description: required.description_en.trim(),
      description_ar: required.description_ar.trim(),
      bullet_points: required.bullet_points.filter(bp => bp.trim().length > 0),
      manufacturer: required.manufacturer || DEFAULT_VALUES.brand,
      model_number: required.model_number || required.name_en.trim(),
      country_of_origin: required.country_of_origin,
      browse_node_id: required.browse_node_id,
      material: optional.material,
      number_of_items: parseInt(optional.unit_count),
      unit_count: { value: parseFloat(required.unit_count), type: required.unit_count_type },
      included_components: required.included_components || required.name_en.trim(),
      target_audience: optional.target_audience,
      compare_price: optional.compare_price ? parseFloat(optional.compare_price) : undefined,
      cost: optional.cost ? parseFloat(optional.cost) : undefined,
      sale_price: optional.sale_price ? parseFloat(optional.sale_price) : undefined,
      sale_start_date: optional.sale_start_date || undefined,
      sale_end_date: optional.sale_end_date || undefined,
      handling_time: parseInt(optional.handling_time),
      package_quantity: parseInt(optional.package_quantity),
      weight: parseFloat(required.item_weight),
      dimensions: {
        length: parseFloat(required.package_length),
        width: parseFloat(required.package_width),
        height: parseFloat(required.package_height),
        unit: 'centimeters',
      },
      keywords: optional.keywords,
      images: allImages,
    }
  }

  // ==================== Submit Handlers ====================
  const handleSave = async () => {
    const { valid, errors } = validate()
    if (!valid) {
      toast.error(errors.join('\n'))
      return
    }

    setSubmitting(true)
    try {
      const payloads = []
      for (let i = 0; i < listingCopies; i++) {
        payloads.push(buildPayload(i))
      }

      // EDIT MODE: Update existing product
      if (isEditMode && editProduct?.id) {
        const updatePayload = { ...payloads[0], id: undefined } // Remove id field
        await productsApi.update(editProduct.id, updatePayload)
        toast.success('✅ تم تحديث المنتج بنجاح!')
        navigate('/products')
        return
      }

      // CREATE MODE: Create new product(s)
      if (listingCopies === 1) {
        await createMutation.mutateAsync(payloads[0] as any)
        toast.success('✅ تم حفظ المنتج!')
      } else {
        toast.loading(`جاري إنشاء ${listingCopies} منتج...`)
        let successCount = 0
        for (let i = 0; i < payloads.length; i++) {
          try {
            await createMutation.mutateAsync(payloads[i] as any)
            successCount++
          } catch {
            // silently fail for individual items
          }
        }
        toast.dismiss()
        toast.success(`✅ تم إنشاء ${successCount} منتج!`)
      }

      navigate('/products')
    } catch (error: any) {
      // FIX: Proper error message extraction
      const errorMsg = error?.response?.data?.detail
        || error?.response?.data?.message
        || (typeof error?.message === 'string' ? error.message : 'حدث خطأ غير معروف')
      toast.error('فشل الحفظ: ' + errorMsg)
      console.error('Save error:', error)
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

    setSubmitting(true)
    try {
      // Step 1: Save to DB first
      const payload = buildPayload()
      const response = await createMutation.mutateAsync(payload as any)
      const productId = response.data.id

      // Step 2: Submit to Amazon via SP-API
      await productsApi.submitToAmazon(productId)

      toast.info('⏳ تم الاستلام — جاري المعالجة لدى أمازون')
      navigate('/listings')
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail
        || error?.response?.data?.message
        || (typeof error?.message === 'string' ? error.message : 'حدث خطأ غير معروف')
      toast.error('فشل الإرسال: ' + errorMsg)
      console.error('Submit error:', error)
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

    const p = buildPayload()
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
            <span className="text-gray-400">{k}:</span>
            <span className="font-mono">{String(v)}</span>
          </div>
        ))}
      </div>
    ), { duration: 10000 })
  }

  // ==================== Render Page 1: الحقول الإجبارية ====================
  const renderPage1 = (
    <div className="space-y-6">
      {/* الهوية الأساسية */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h3 className="text-lg font-bold text-blue-700 dark:text-blue-400 mb-4 flex items-center gap-2">
          <Tag className="w-5 h-5" /> الهوية الأساسية
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="اسم المنتج (عربي)" required>
            <TextInput
              value={required.name_ar}
              onChange={v => setRequired(prev => ({ ...prev, name_ar: v }))}
              placeholder="مثال: خلاط كهربائي 500 واط"
            />
          </Field>
          <Field label="اسم المنتج (English)" required>
            <TextInput
              value={required.name_en}
              onChange={v => setRequired(prev => ({ ...prev, name_en: v }))}
              placeholder="Example: Electric Hand Mixer 500W"
            />
          </Field>
        </div>

        <Field label="نوع المنتج" required>
          <SelectInput
            value={required.product_type}
            onChange={v => setRequired(prev => ({ ...prev, product_type: v }))}
            options={PRODUCT_TYPES as any}
          />
        </Field>

        <Field label="الباركود" required>
          <div className="mb-2">
            <RadioGroup
              name="id_type"
              options={ID_TYPES.filter(t => ['EAN', 'UPC', 'EXEMPT'].includes(t.value)) as any}
              value={required.id_type}
              onChange={v => setRequired(prev => ({ ...prev, id_type: v }))}
            />
          </div>
          {required.id_type !== 'EXEMPT' && (
            <TextInput
              value={required.ean}
              onChange={v => setRequired(prev => ({ ...prev, ean: v.replace(/\D/g, '').slice(0, required.id_type === 'UPC' ? 12 : 13) }))}
              placeholder={required.id_type === 'UPC' ? '12 رقم' : '13 رقم'}
              type="text"
            />
          )}
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Field label="البراند" required>
            <TextInput
              value={required.brand}
              onChange={v => setRequired(prev => ({ ...prev, brand: v }))}
              placeholder="Generic"
            />
          </Field>
          <Field label="الموديل" required>
            <TextInput
              value={required.model_number}
              onChange={v => setRequired(prev => ({ ...prev, model_number: v }))}
              placeholder={required.name_en || 'SKU'}
            />
          </Field>
          <Field label="المصنع" required>
            <TextInput
              value={required.manufacturer}
              onChange={v => setRequired(prev => ({ ...prev, manufacturer: v }))}
              placeholder="Generic"
            />
          </Field>
        </div>

        <Field label="بلد المنشأ" required>
          <SelectInput
            value={required.country_of_origin}
            onChange={v => setRequired(prev => ({ ...prev, country_of_origin: v }))}
            options={COUNTRIES as any}
          />
        </Field>
      </div>

      {/* الوصف والتفاصيل */}
      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
        <h3 className="text-lg font-bold text-green-700 dark:text-green-400 mb-4 flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5" /> الوصف والتفاصيل
        </h3>

        <Field label="الوصف (عربي)" required>
          <textarea
            value={required.description_ar}
            onChange={e => setRequired(prev => ({ ...prev, description_ar: e.target.value }))}
            placeholder="وصف تفصيلي للمنتج بالعربية..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </Field>

        <Field label="الوصف (English)" required>
          <textarea
            value={required.description_en}
            onChange={e => setRequired(prev => ({ ...prev, description_en: e.target.value }))}
            placeholder="Detailed product description in English..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </Field>

        <Field label="النقاط البيعية (5 نقاط)" required>
          <div className="space-y-2">
            {required.bullet_points.map((bp, i) => (
              <div key={i} className="flex gap-2">
                <span className="flex-shrink-0 w-6 h-8 flex items-center justify-center bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm font-bold rounded">
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
                  placeholder={`نقطة بيعية ${i + 1}...`}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}
          </div>
        </Field>

        <Field label="الفئة (Browse Node)" required>
          <SelectInput
            value={required.browse_node_id}
            onChange={v => setRequired(prev => ({ ...prev, browse_node_id: v }))}
            options={BROWSE_NODES as any}
          />
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="المكونات المرفقة" required>
            <TextInput
              value={required.included_components}
              onChange={v => setRequired(prev => ({ ...prev, included_components: v }))}
              placeholder={required.name_en || '1x المنتج'}
            />
          </Field>
          <Field label="عدد الوحدات" required>
            <NumberInput
              value={required.unit_count}
              onChange={v => setRequired(prev => ({ ...prev, unit_count: v }))}
              placeholder="1"
              min="1"
            />
          </Field>
        </div>

        <Field label="نوع الوحدة" required>
          <SelectInput
            value={required.unit_count_type}
            onChange={v => setRequired(prev => ({ ...prev, unit_count_type: v }))}
            options={UNIT_TYPES as any}
          />
        </Field>
      </div>

      {/* التسعير والكمية */}
      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
        <h3 className="text-lg font-bold text-amber-700 dark:text-amber-400 mb-4 flex items-center gap-2">
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
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">ج.م</span>
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
      <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
        <h3 className="text-lg font-bold text-purple-700 dark:text-purple-400 mb-4 flex items-center gap-2">
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
          <Field label="قناة الشحن" required>
            <RadioGroup
              name="fulfillment"
              options={FULFILLMENT_CHANNELS as any}
              value={required.fulfillment_channel}
              onChange={v => setRequired(prev => ({ ...prev, fulfillment_channel: v }))}
            />
          </Field>
        </div>

        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">أبعاد الباكج (سم) *</h4>
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
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">الأوزان (كجم) *</h4>
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

      <button
        onClick={() => setPage(2)}
        className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 font-bold"
      >
        التالي: الحقول الاختيارية ←
      </button>
    </div>
  )

  // ==================== Render Page 2: الحقول الاختيارية ====================
  const renderPage2 = (
    <div className="space-y-6">
      {/* الكلمات المفتاحية */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
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
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          {optional.keywords.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {optional.keywords.map((kw, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full text-sm flex items-center gap-1"
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
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
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

      {/* التسعير الإضافي */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
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
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">ج.م</span>
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
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">ج.م</span>
            </div>
          </Field>
        </div>

        <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <h4 className="text-sm font-semibold text-amber-700 dark:text-amber-400 mb-3">تخفيض (اختياري)</h4>
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
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
            </Field>
            <Field label="إلى تاريخ">
              <input
                type="date"
                value={optional.sale_end_date}
                onChange={e => setOptional(prev => ({ ...prev, sale_end_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              />
            </Field>
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => setPage(1)}
          className="px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          → السابق
        </button>
        <button
          onClick={() => setPage(3)}
          className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 font-bold"
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
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
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
              className="w-full h-64 object-contain bg-gray-100 dark:bg-gray-900 rounded-lg"
            />
            <button
              onClick={() => {
                setMainImageUrl('')
                setMainImagePreview('')
              }}
              className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadingImages}
            className="w-full h-48 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg flex flex-col items-center justify-center gap-3 hover:border-blue-500 transition-colors"
          >
            {uploadingImages ? (
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            ) : (
              <>
                <Upload className="w-8 h-8 text-gray-400" />
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">اضغط لاختيار صورة</p>
                  <p className="text-xs text-gray-500">1000×1000 بكسل على الأقل</p>
                </div>
              </>
            )}
          </button>
        )}
      </div>

      {/* صور إضافية */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
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
                      className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
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
                    <Upload className="w-6 h-6 text-gray-400" />
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* عدد الإعلانات */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
          <Package className="w-5 h-5" /> عدد الإعلانات
        </h3>

        <Field label="عدد النسخ المراد إنشاؤها" hint="1-50 نسخة">
          <NumberInput
            value={String(listingCopies)}
            onChange={v => setListingCopies(Math.min(50, Math.max(1, parseInt(v) || 1)))}
            placeholder="1"
            min="1"
          />
        </Field>
      </div>

      {/* الأزرار */}
      <div className="flex flex-col gap-3">
        <button
          onClick={handlePreview}
          className="w-full px-6 py-3 bg-amber-500 text-white rounded-lg hover:bg-amber-600 flex items-center justify-center gap-2 font-bold"
        >
          <Eye className="w-5 h-5" /> معاينة البيانات
        </button>

        <button
          onClick={handleSave}
          disabled={submitting}
          className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2 font-bold"
        >
          {submitting ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> جاري الحفظ...</>
          ) : (
            <><Save className="w-5 h-5" /> حفظ في المخزون</>
          )}
        </button>

        <button
          onClick={handleSubmitToAmazon}
          disabled={submitting}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 font-bold"
        >
          {submitting ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> جاري الإرسال...</>
          ) : (
            <><Globe className="w-5 h-5" /> حفظ وإرسال لـ Amazon</>
          )}
        </button>
      </div>

      <button
        onClick={() => setPage(2)}
        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
      >
        → السابق
      </button>
    </div>
  )

  // ==================== Main Render ====================
  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {isEditMode ? 'تعديل المنتج' : 'إضافة منتج جديد'}
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          {isEditMode ? 'قم بتعديل البيانات المطلوبة' : 'أكمل البيانات لإضافة منتج جديد'}
        </p>
      </div>

      <StepIndicator currentPage={page} onNavigate={setPage} />

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        {page === 1 && renderPage1}
        {page === 2 && renderPage2}
        {page === 3 && renderPage3}
      </div>
    </div>
  )
}