import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowRight, Package, DollarSign, Image, Settings, Layers, Save, Loader2, Globe, Truck, Tag, Ruler } from 'lucide-react'
import { useCreateProduct, useUpdateProduct, useSubmitListing, useSellerInfo } from '@/api/hooks'
import { MediaUploader } from '@/components/common/MediaUploader'
import toast from 'react-hot-toast'

const tabs = [
  { id: 'basic', label: 'المعلومات الأساسية', icon: Package },
  { id: 'pricing', label: 'التسعير والمخزون', icon: DollarSign },
  { id: 'media', label: 'الصور والوسائط', icon: Image },
  { id: 'advanced', label: 'الخصائص المتقدمة', icon: Settings },
  { id: 'amazon', label: 'تفاصيل Amazon', icon: Truck },
  { id: 'multi', label: 'رفع متعدد', icon: Layers },
]

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const createMutation = useCreateProduct()
  const updateMutation = useUpdateProduct()
  const submitListingMutation = useSubmitListing()
  const { data: sellerInfo, isLoading: sellerLoading } = useSellerInfo()

  // All hooks MUST be before any conditional return
  const [activeTab, setActiveTab] = useState('basic')
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    name_ar: '',
    name_en: '',
    category: '',
    brand: '',
    price: 0,
    compare_price: 0,
    currency: 'EGP',
    quantity: 0,
    sale_price: 0,
    sale_start_date: '',
    sale_end_date: '',
    min_price: 0,
    max_price: 0,
    description: '',
    description_ar: '',
    description_en: '',
    bullet_points: [] as string[],
    bullet_points_ar: [] as string[],
    bullet_points_en: [] as string[],
    keywords: [] as string[],
    weight: 0,
    dimensions: { length: 0, width: 0, height: 0 } as { length: number; width: number; height: number },
    images: [] as string[],
    attributes: {} as Record<string, any>,
    listing_copies: 1,
    // Amazon-specific fields
    upc: '',
    ean: '',
    condition: 'New',
    fulfillment_channel: 'MFN',
    handling_time: 0,
    product_type: '',
    manufacturer: '',
    model_number: '',
    country_of_origin: '',
    package_quantity: 1,
    browse_node_id: '',
    // Variations
    is_parent: false,
    parent_sku: '',
    variation_theme: '',  // e.g., "Size", "Color", "Size/Color"
  })

  const editMode = location.state?.editMode || false
  const editProduct = location.state?.editProduct || null

  useEffect(() => {
    if (editMode && editProduct) {
      setFormData({
        sku: editProduct.sku || '',
        name: editProduct.name || '',
        name_ar: editProduct.name_ar || '',
        name_en: editProduct.name_en || '',
        category: editProduct.category || '',
        brand: editProduct.brand || '',
        price: Number(editProduct.price) || 0,
        compare_price: Number(editProduct.compare_price) || 0,
        currency: editProduct.currency || 'EGP',
        quantity: Number(editProduct.quantity) || 0,
        sale_price: Number(editProduct.sale_price) || 0,
        sale_start_date: editProduct.sale_start_date || '',
        sale_end_date: editProduct.sale_end_date || '',
        min_price: Number(editProduct.min_price) || 0,
        max_price: Number(editProduct.max_price) || 0,
        description: editProduct.description || '',
        description_ar: editProduct.description_ar || '',
        description_en: editProduct.description_en || '',
        bullet_points: editProduct.bullet_points || [],
        bullet_points_ar: editProduct.bullet_points_ar || [],
        bullet_points_en: editProduct.bullet_points_en || [],
        keywords: editProduct.keywords || [],
        weight: Number(editProduct.weight) || 0,
        dimensions: editProduct.dimensions || { length: 0, width: 0, height: 0 },
        images: editProduct.images || [],
        attributes: editProduct.attributes || {},
        listing_copies: 1,
        // Amazon-specific fields
        upc: editProduct.upc || '',
        ean: editProduct.ean || '',
        condition: editProduct.condition || 'New',
        fulfillment_channel: editProduct.fulfillment_channel || 'MFN',
        handling_time: Number(editProduct.handling_time) || 0,
        product_type: editProduct.product_type || '',
        manufacturer: editProduct.manufacturer || '',
        model_number: editProduct.model_number || '',
        country_of_origin: editProduct.country_of_origin || '',
        package_quantity: Number(editProduct.package_quantity) || 1,
        browse_node_id: editProduct.browse_node_id || '',
        // Variations
        is_parent: editProduct.is_parent || false,
        parent_sku: editProduct.parent_sku || '',
        variation_theme: editProduct.variation_theme || '',
      })
    }
  }, [editMode, editProduct])

  const loading = createMutation.isPending || updateMutation.isPending || submitListingMutation.isPending

  const sanitizeInput = (str: string): string => {
    return str.replace(/<[^>]*>/g, '')
  }

  const handleSubmit = async () => {
    if (!formData.sku || !formData.name || !formData.price) {
      toast.error('يرجى ملء الحقول المطلوبة (SKU، الاسم، السعر)')
      return
    }

    if (!formData.images || formData.images.length === 0) {
      toast.error('يرجى إضافة صورة رئيسية واحدة على الأقل')
      return
    }

    try {
      const payload = {
        ...formData,
        name: sanitizeInput(formData.name),
        name_ar: sanitizeInput(formData.name_ar),
        name_en: sanitizeInput(formData.name_en),
        description: sanitizeInput(formData.description),
        description_ar: sanitizeInput(formData.description_ar),
        description_en: sanitizeInput(formData.description_en),
        price: Number(formData.price),
        compare_price: Number(formData.compare_price) || null,
        quantity: Number(formData.quantity),
        weight: Number(formData.weight),
        sale_price: Number(formData.sale_price) || null,
        sale_start_date: formData.sale_start_date || null,
        sale_end_date: formData.sale_end_date || null,
        min_price: Number(formData.min_price) || null,
        max_price: Number(formData.max_price) || null,
        // Variations
        is_parent: formData.is_parent || false,
        parent_sku: formData.parent_sku || null,
        variation_theme: formData.variation_theme || null,
        dimensions: {
          length: Number(formData.dimensions?.length) || 0,
          width: Number(formData.dimensions?.width) || 0,
          height: Number(formData.dimensions?.height) || 0,
        },
      }

      let product;
      if (editMode && editProduct) {
        product = await updateMutation.mutateAsync({ id: editProduct.id, data: payload })
        toast.success('تم تحديث المنتج بنجاح!')
        navigate('/products')
        return
      }

      const copies = Number(formData.listing_copies) || 1

      if (copies > 1) {
        for (let i = 1; i <= copies; i++) {
          const multiPayload = {
            ...payload,
            seller_id: sellerInfo?.id,
            sku: `${payload.sku}-${i.toString().padStart(2, '0')}`,
            name: `${payload.name} (نسخة ${i})`,
          }
          const newProduct = await createMutation.mutateAsync(multiPayload)
          await submitListingMutation.mutateAsync(newProduct.id)
          await new Promise(resolve => setTimeout(resolve, 200))
        }
        toast.success(`تم إنشاء ${copies} منتج وإضافتها لقائمة الرفع!`)
      } else {
        const payloadWithSellerId = {
          ...payload,
          seller_id: sellerInfo?.id,
        }
        product = await createMutation.mutateAsync(payloadWithSellerId)
        await submitListingMutation.mutateAsync(product.id)
        toast.success('تم إنشاء المنتج بنجاح!')
      }

      navigate('/products')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل في حفظ البيانات')
    }
  }

  // Loading state
  if (sellerLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-amazon-orange animate-spin" />
      </div>
    )
  }

  // No seller connected - show message inline (not early return to preserve hooks)
  const sellerNotConnected = !sellerLoading && !sellerInfo?.id

  return sellerNotConnected ? (
    <div className="flex flex-col items-center justify-center h-96" dir="rtl">
      <h2 className="text-xl font-bold text-white mb-4">لا يوجد بائع متصل</h2>
      <p className="text-gray-400 mb-4">يرجى الاتصال بـ Amazon أولاً من صفحة الإعدادات</p>
      <button
        onClick={() => navigate('/settings')}
        className="px-6 py-3 bg-amazon-orange text-white rounded-lg hover:bg-orange-600 transition"
      >
        الذهاب للإعدادات
      </button>
    </div>
  ) : (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            {editMode ? 'تعديل المنتج' : 'إضافة منتج جديد'}
            <span className="text-xs bg-amazon-orange/20 text-amazon-orange px-2 py-1 rounded">Bilingual Enabled</span>
          </h1>
          <p className="text-gray-400 mt-1">
            {editMode ? `تعديل SKU: ${editProduct?.sku}` : 'أدخل بيانات المنتج بالعربية والإنجليزية للرفع العالمي'}
          </p>
        </div>
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="flex items-center gap-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold px-6 py-3 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              جاري التنفيذ...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              {editMode ? 'تحديث وحفظ' : 'حفظ ونشر'}
            </>
          )}
        </button>
      </div>

      <div className="bg-[#12121a] rounded-xl border border-gray-800/50 overflow-hidden shadow-2xl">
        <div className="flex border-b border-gray-800/50 overflow-x-auto bg-[#1a1a2e]/50">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium whitespace-nowrap transition-all ${activeTab === id
                ? 'text-amazon-orange border-b-2 border-amazon-orange bg-[#1a1a2e]'
                : 'text-gray-500 hover:text-white hover:bg-[#1a1a2e]'
                }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        <div className="p-8">
          {activeTab === 'basic' && <BasicInfoTab formData={formData} setFormData={setFormData} />}
          {activeTab === 'pricing' && <PricingTab formData={formData} setFormData={setFormData} />}
          {activeTab === 'media' && <MediaTab formData={formData} setFormData={setFormData} />}
          {activeTab === 'advanced' && <AdvancedTab formData={formData} setFormData={setFormData} />}
          {activeTab === 'amazon' && <AmazonDetailsTab formData={formData} setFormData={setFormData} />}
          {activeTab === 'multi' && <MultiListingTab formData={formData} setFormData={setFormData} />}
        </div>

        <div className="flex justify-between px-8 py-4 bg-[#1a1a2e]/50 border-t border-gray-800/50">
          <button
            onClick={() => {
              const idx = tabs.findIndex((t) => t.id === activeTab)
              if (idx < tabs.length - 1) setActiveTab(tabs[idx + 1].id)
            }}
            className="flex items-center gap-2 text-amazon-orange font-medium hover:underline text-sm"
          >
            الانتقال للقسم التالي
            <ArrowRight className="w-4 h-4 rotate-180" />
          </button>
        </div>
      </div>
    </div>
  )
}

function BasicInfoTab({ formData, setFormData }: { formData: any, setFormData: any }) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">SKU (Stock Keeping Unit) *</label>
        <input
          type="text"
          value={formData.sku}
          onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
          className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none transition-all"
          placeholder="مثل: LAPTOP-COREI7-001"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-gray-800 pt-6">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
            <Globe className="w-4 h-4 text-blue-400" /> الاسم (العربية) *
          </label>
          <input
            type="text"
            value={formData.name_ar}
            onChange={(e) => setFormData({ ...formData, name_ar: e.target.value, name: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="اسم المنتج بالعربية"
            dir="rtl"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
            <Globe className="w-4 h-4 text-red-400" /> Title (English) *
          </label>
          <input
            type="text"
            value={formData.name_en}
            onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-red-500 outline-none"
            placeholder="Product name in English"
            dir="ltr"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">الوصف (العربية)</label>
          <textarea
            rows={5}
            value={formData.description_ar}
            onChange={(e) => setFormData({ ...formData, description_ar: e.target.value, description: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="وصف تفصيلي بالعربية..."
            dir="rtl"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Description (English)</label>
          <textarea
            rows={5}
            value={formData.description_en}
            onChange={(e) => setFormData({ ...formData, description_en: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-red-500 outline-none"
            placeholder="Detailed description in English..."
            dir="ltr"
          />
        </div>
      </div>
    </div>
  )
}

function PricingTab({ formData, setFormData }: { formData: any, setFormData: any }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">العملة</label>
          <select
            value={formData.currency}
            onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
          >
            <option value="EGP">EGP - جنيه مصري</option>
            <option value="USD">USD - دولار أمريكي</option>
            <option value="EUR">EUR - يورو</option>
            <option value="GBP">GBP - جنيه إسترليني</option>
            <option value="SAR">SAR - ريال سعودي</option>
            <option value="AED">AED - درهم إماراتي</option>
          </select>
        </div>
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">السعر ({formData.currency}) *</label>
          <div className="relative">
            <DollarSign className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-amazon-orange" />
            <input
              type="number"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              className="w-full pr-10 pl-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white text-xl font-bold focus:ring-2 focus:ring-amazon-orange outline-none"
              placeholder="0.00"
            />
          </div>
        </div>
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">الكمية المتوفرة</label>
          <input
            type="number"
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white text-xl font-bold focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="0"
          />
        </div>
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">الوزن الكلي (كجم)</label>
          <input
            type="number"
            value={formData.weight}
            onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white text-xl font-bold focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="0.0"
          />
        </div>
      </div>

      {/* Sale Pricing Section */}
      <div className="border-t border-gray-800 pt-6 mt-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <Tag className="w-4 h-4 text-green-400" /> سعر التخفيض (Sale Price)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">السعر الأصلي ({formData.currency})</label>
            <input
              type="number"
              value={formData.compare_price || ''}
              onChange={(e) => setFormData({ ...formData, compare_price: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-gray-500 outline-none"
              placeholder="0.00"
            />
            <p className="text-xs text-gray-500 mt-2">السعر قبل الخصم (اختياري)</p>
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">الحد الأدنى للسعر</label>
            <input
              type="number"
              value={formData.min_price || ''}
              onChange={(e) => setFormData({ ...formData, min_price: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-yellow-500 outline-none"
              placeholder="0.00"
            />
            <p className="text-xs text-gray-500 mt-2">أقل سعر مقبول (حماية من الخطأ)</p>
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">الحد الأقصى للسعر</label>
            <input
              type="number"
              value={formData.max_price || ''}
              onChange={(e) => setFormData({ ...formData, max_price: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-yellow-500 outline-none"
              placeholder="0.00"
            />
            <p className="text-xs text-gray-500 mt-2">أعلى سعر مسموح</p>
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
              <Tag className="w-4 h-4 text-green-400" /> سعر التخفيض ({formData.currency})
            </label>
            <input
              type="number"
              value={formData.sale_price || ''}
              onChange={(e) => setFormData({ ...formData, sale_price: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-green-700 rounded-lg text-white focus:ring-2 focus:ring-green-500 outline-none"
              placeholder="0.00"
            />
            <p className="text-xs text-green-500 mt-2">سعر العرض المؤقت</p>
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">بداية التخفيض</label>
            <input
              type="datetime-local"
              value={formData.sale_start_date || ''}
              onChange={(e) => setFormData({ ...formData, sale_start_date: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">نهاية التخفيض</label>
            <input
              type="datetime-local"
              value={formData.sale_end_date || ''}
              onChange={(e) => setFormData({ ...formData, sale_end_date: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>
        </div>
      </div>

      {/* Dimensions Section */}
      <div className="border-t border-gray-800 pt-6 mt-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <Ruler className="w-4 h-4 text-blue-400" /> أبعاد المنتج (سم)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">الطول (CM)</label>
            <input
              type="number"
              min={0}
              value={formData.dimensions?.length || 0}
              onChange={(e) => setFormData({
                ...formData,
                dimensions: { ...formData.dimensions, length: Number(e.target.value) }
              })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
              placeholder="0.0"
            />
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">العرض (CM)</label>
            <input
              type="number"
              min={0}
              value={formData.dimensions?.width || 0}
              onChange={(e) => setFormData({
                ...formData,
                dimensions: { ...formData.dimensions, width: Number(e.target.value) }
              })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
              placeholder="0.0"
            />
          </div>
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">الارتفاع (CM)</label>
            <input
              type="number"
              min={0}
              value={formData.dimensions?.height || 0}
              onChange={(e) => setFormData({
                ...formData,
                dimensions: { ...formData.dimensions, height: Number(e.target.value) }
              })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
              placeholder="0.0"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function MediaTab({ formData, setFormData }: { formData: any, setFormData: any }) {
  return (
    <div className="space-y-4">
      <MediaUploader
        images={formData.images}
        onChange={(imgs) => setFormData({ ...formData, images: imgs })}
      />
    </div>
  )
}

function AdvancedTab({ formData, setFormData }: { formData: any, setFormData: any }) {
  const [newBulletAr, setNewBulletAr] = useState('')
  const [newBulletEn, setNewBulletEn] = useState('')

  const addBullet = () => {
    if (newBulletAr.trim() || newBulletEn.trim()) {
      setFormData({
        ...formData,
        bullet_points_ar: [...formData.bullet_points_ar, newBulletAr.trim()],
        bullet_points_en: [...formData.bullet_points_en, newBulletEn.trim()],
        bullet_points: [...formData.bullet_points, newBulletAr.trim()]
      })
      setNewBulletAr('')
      setNewBulletEn('')
    }
  }

  const removeBullet = (index: number) => {
    const newBar = [...formData.bullet_points_ar]
    const newBen = [...formData.bullet_points_en]
    newBar.splice(index, 1)
    newBen.splice(index, 1)
    setFormData({ ...formData, bullet_points_ar: newBar, bullet_points_en: newBen })
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">مميزات المنتج (العربية)</label>
          <input
            type="text"
            value={newBulletAr}
            onChange={(e) => setNewBulletAr(e.target.value)}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange transition-all"
            placeholder="أضف ميزة بالعربية..."
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Features (English)</label>
          <input
            type="text"
            value={newBulletEn}
            onChange={(e) => setNewBulletEn(e.target.value)}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange transition-all"
            placeholder="Add feature in English..."
          />
        </div>
      </div>
      <button
        onClick={addBullet}
        className="w-full py-3 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-amazon-orange transition-all"
      >
        + إضافة نقطة ميزة (Bullet Point)
      </button>

      <ul className="space-y-4">
        {formData.bullet_points_ar.map((bullet: string, i: number) => (
          <li key={i} className="bg-[#1a1a2e] p-4 rounded-xl border border-gray-800 flex flex-col gap-2 relative group">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <p className="text-white text-sm" dir="rtl">● {bullet}</p>
                <p className="text-gray-500 text-xs mt-1" dir="ltr">● {formData.bullet_points_en[i]}</p>
              </div>
              <button onClick={() => removeBullet(i)} className="text-red-500 hover:text-red-400 p-2">X</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AmazonDetailsTab({ formData, setFormData }: { formData: any, setFormData: any }) {
  return (
    <div className="space-y-8">
      {/* UPC/EAN - GTIN Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Tag className="w-4 h-4 text-amazon-orange" /> UPC (12 digits)
          </label>
          <input
            type="text"
            value={formData.upc || ''}
            onChange={(e) => setFormData({ ...formData, upc: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="مثال: 012345678905"
            maxLength={12}
          />
          <p className="text-xs text-gray-500 mt-2">UPC: 12 رقم (مطلوب لمعظم فئات Amazon)</p>
        </div>

        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Tag className="w-4 h-4 text-blue-400" /> EAN (13 digits)
          </label>
          <input
            type="text"
            value={formData.ean || ''}
            onChange={(e) => setFormData({ ...formData, ean: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="مثال: 5901234123457"
            maxLength={13}
          />
          <p className="text-xs text-gray-500 mt-2">EAN: 13 رقم (بديل UPC خارج أمريكا)</p>
        </div>
      </div>

      {/* Condition & Fulfillment */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Tag className="w-4 h-4 text-amazon-orange" /> حالة المنتج (Condition) *
          </label>
          <select
            value={formData.condition}
            onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
          >
            <option value="New">New - جديد</option>
            <option value="UsedLikeNew">Used Like New - مستعمل كالجديد</option>
            <option value="UsedVeryGood">Used Very Good - مستعمل جيد جداً</option>
            <option value="UsedGood">Used Good - مستعمل جيد</option>
            <option value="UsedAcceptable">Used Acceptable - مستعمل مقبول</option>
            <option value="Refurbished">Refurbished - مجدد</option>
          </select>
          <p className="text-xs text-gray-500 mt-2">Amazon يتطلب Condition لكل عرض</p>
        </div>

        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
            <Truck className="w-4 h-4 text-blue-400" /> قناة الشحن (Fulfillment) *
          </label>
          <select
            value={formData.fulfillment_channel}
            onChange={(e) => setFormData({ ...formData, fulfillment_channel: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="MFN">MFN - شحن البائع (Seller Fulfilled)</option>
            <option value="AFN">FBA - شحن أمازون (Fulfillment by Amazon)</option>
          </select>
          <p className="text-xs text-gray-500 mt-2">MFN = أنت بتشحن، FBA = أمازون بتشحّن</p>
        </div>
      </div>

      {/* Product Type & Handling Time */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">نوع المنتج (Product Type)</label>
          <input
            type="text"
            value={formData.product_type}
            onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="مثال: PRODUCT, APPAREL"
          />
          <p className="text-xs text-gray-500 mt-2">مطلوب في Product Template</p>
        </div>

        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">وقت التجهيز (Handling Time)</label>
          <input
            type="number"
            min={0}
            max={30}
            value={formData.handling_time}
            onChange={(e) => setFormData({ ...formData, handling_time: Number(e.target.value) })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="0"
          />
          <p className="text-xs text-gray-500 mt-2">أيام التجهيز قبل الشحن</p>
        </div>

        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">عدد العبوات (Package Qty)</label>
          <input
            type="number"
            min={1}
            value={formData.package_quantity}
            onChange={(e) => setFormData({ ...formData, package_quantity: Number(e.target.value) })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="1"
          />
          <p className="text-xs text-gray-500 mt-2">عدد الوحدات في العبوة</p>
        </div>
      </div>

      {/* Manufacturer, Model, Country */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">الشركة المصنّعة (Manufacturer)</label>
          <input
            type="text"
            value={formData.manufacturer}
            onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="اسم الشركة المصنّعة"
          />
        </div>

        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">رقم الموديل (Model Number)</label>
          <input
            type="text"
            value={formData.model_number}
            onChange={(e) => setFormData({ ...formData, model_number: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="مثال: XYZ-1234"
          />
        </div>

        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">بلد المنشأ (Country of Origin)</label>
          <input
            type="text"
            value={formData.country_of_origin}
            onChange={(e) => setFormData({ ...formData, country_of_origin: e.target.value })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-amazon-orange outline-none"
            placeholder="مثال: CN, US, EG"
          />
          <p className="text-xs text-gray-500 mt-2">رمز البلد (ISO 3166-1 alpha-2)</p>
        </div>
      </div>

      {/* Browse Node */}
      <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
        <label className="block text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
          <Globe className="w-4 h-4 text-purple-400" /> Browse Node ID (فئة Amazon)
        </label>
        <input
          type="text"
          value={formData.browse_node_id || ''}
          onChange={(e) => setFormData({ ...formData, browse_node_id: e.target.value })}
          className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500 outline-none"
          placeholder="مثال: 611818051 (إلكترونيات - مصر)"
        />
        <p className="text-xs text-gray-500 mt-2">يساعد Amazon يكتشف منتج أسرع في الفئة الصحيحة</p>
      </div>

      {/* Variations Section */}
      <div className="border-t border-gray-800 pt-6 mt-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <Layers className="w-4 h-4 text-orange-400" /> تنويعات المنتج (Variations)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
            <label className="block text-sm font-medium text-gray-400 mb-3">هل هذا منتج أب؟ (Parent Product)</label>
            <select
              value={formData.is_parent ? 'true' : 'false'}
              onChange={(e) => setFormData({ ...formData, is_parent: e.target.value === 'true' })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none"
            >
              <option value="false">لا - منتج عادي</option>
              <option value="true">نعم - منتج أب (يحتوي على تنويعات)</option>
            </select>
          </div>

          {formData.is_parent && (
            <>
              <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
                <label className="block text-sm font-medium text-gray-400 mb-3">نوع التنويع (Variation Theme)</label>
                <select
                  value={formData.variation_theme}
                  onChange={(e) => setFormData({ ...formData, variation_theme: e.target.value })}
                  className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none"
                >
                  <option value="">اختر نوع التنويع</option>
                  <option value="Size">المقاس (Size)</option>
                  <option value="Color">اللون (Color)</option>
                  <option value="Size/Color">المقاس واللون (Size/Color)</option>
                  <option value="Style">النمط (Style)</option>
                </select>
                <p className="text-xs text-gray-500 mt-2">الصفات اللي هتختلف بين المنتجات</p>
              </div>

              <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
                <label className="block text-sm font-medium text-gray-400 mb-3">SKU الأب (Parent SKU)</label>
                <input
                  type="text"
                  value={formData.parent_sku}
                  onChange={(e) => setFormData({ ...formData, parent_sku: e.target.value })}
                  className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-orange-500 outline-none"
                  placeholder="PARENT-SKU-001"
                />
                <p className="text-xs text-gray-500 mt-2">SKU فريد للمنتج الأب</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-900/20 border border-blue-500/30 p-4 rounded-xl">
        <h4 className="text-blue-400 font-semibold mb-2 flex items-center gap-2">
          <Globe className="w-4 h-4" /> لماذا هذه الحقول مهمة؟
        </h4>
        <ul className="text-sm text-gray-300 space-y-1">
          <li>✅ <strong>Condition</strong> — مطلوب من Amazon لكل عرض</li>
          <li>✅ <strong>Fulfillment Channel</strong> — يحدد مين بيشحن (أنت ولا أمازون)</li>
          <li>✅ <strong>Product Type</strong> — مطلوب في Amazon Product Template</li>
          <li>✅ <strong>Handling Time</strong> — يؤثر على تجربة العميل</li>
          <li>✅ <strong>Manufacturer / Model / Country</strong> — مطلوب في Compliance</li>
          <li>✅ <strong>Browse Node ID</strong> — يحسن اكتشاف المنتج في Amazon</li>
          <li>✅ <strong>Variations</strong> — يتيح إنشاء منتجات متعددة بصفات مختلفة</li>
        </ul>
      </div>
    </div>
  )
}

function MultiListingTab({ formData, setFormData }: { formData: any, setFormData: any }) {
  return (
    <div className="space-y-6">
      <div className="bg-amazon-orange/5 border border-amazon-orange/20 p-6 rounded-xl">
        <div className="flex items-center gap-3 mb-4">
          <Layers className="w-6 h-6 text-amazon-orange" />
          <h3 className="text-white font-bold text-lg">نظام النشر المتعدد (Multi-Listing)</h3>
        </div>
        <p className="text-gray-400 text-sm mb-6 leading-relaxed">
          هذه الخاصية تتيح لك إنشاء نسخ متعددة من المنتج تلقائياً.
          كل نسخة ستحصل على SKU فريد وسيتم إضافتها لقائمة الرفع.
        </p>

        <div className="max-w-xs">
          <label className="block text-sm font-medium text-gray-400 mb-2">عدد النسخ المطلوبة</label>
          <input
            type="number"
            min={1}
            max={50}
            value={formData.listing_copies}
            onChange={(e) => setFormData({ ...formData, listing_copies: Number(e.target.value) })}
            className="w-full px-4 py-3 bg-[#0a0a0f] border border-gray-800 rounded-lg text-white font-bold text-center focus:ring-2 focus:ring-amazon-orange outline-none"
          />
          <p className="text-xs text-amazon-orange mt-2">سيتم إنشاء {formData.listing_copies} منتجات مستقلة.</p>
        </div>
      </div>
    </div>
  )
}