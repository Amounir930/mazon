import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowRight, Package, DollarSign, Image, Settings, Layers, Save, Loader2, Globe } from 'lucide-react'
import { useCreateProduct, useUpdateProduct, useSubmitListing } from '@/api/hooks'
import { MediaUploader } from '@/components/common/MediaUploader'
import toast from 'react-hot-toast'

const tabs = [
  { id: 'basic', label: 'المعلومات الأساسية', icon: Package },
  { id: 'pricing', label: 'التسعير والمخزون', icon: DollarSign },
  { id: 'media', label: 'الصور والوسائط', icon: Image },
  { id: 'advanced', label: 'الخصائص المتقدمة', icon: Settings },
  { id: 'multi', label: 'رفع متعدد', icon: Layers },
]

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const createMutation = useCreateProduct()
  const updateMutation = useUpdateProduct()
  const submitListingMutation = useSubmitListing()

  const editMode = location.state?.editMode || false
  const editProduct = location.state?.editProduct || null

  const [activeTab, setActiveTab] = useState('basic')
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    name_ar: '',
    name_en: '',
    category: '',
    brand: '',
    price: 0,
    quantity: 0,
    description: '',
    description_ar: '',
    description_en: '',
    bullet_points: [] as string[],
    bullet_points_ar: [] as string[],
    bullet_points_en: [] as string[],
    keywords: [] as string[],
    weight: 0,
    images: [] as string[],
    attributes: {} as Record<string, any>,
    listing_copies: 1,
  })

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
        quantity: Number(editProduct.quantity) || 0,
        description: editProduct.description || '',
        description_ar: editProduct.description_ar || '',
        description_en: editProduct.description_en || '',
        bullet_points: editProduct.bullet_points || [],
        bullet_points_ar: editProduct.bullet_points_ar || [],
        bullet_points_en: editProduct.bullet_points_en || [],
        keywords: editProduct.keywords || [],
        weight: Number(editProduct.weight) || 0,
        images: editProduct.images || [],
        attributes: editProduct.attributes || {},
        listing_copies: 1,
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
        quantity: Number(formData.quantity),
        weight: Number(formData.weight),
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
            sku: `${payload.sku}-${i.toString().padStart(2, '0')}`,
            name: `${payload.name} (نسخة ${i})`,
          }
          const newProduct = await createMutation.mutateAsync(multiPayload)
          await submitListingMutation.mutateAsync(newProduct.id)
          await new Promise(resolve => setTimeout(resolve, 200))
        }
        toast.success(`تم إنشاء ${copies} منتج وإضافتها لقائمة الرفع!`)
      } else {
        product = await createMutation.mutateAsync(payload)
        await submitListingMutation.mutateAsync(product.id)
        toast.success('تم إنشاء المنتج بنجاح!')
      }

      navigate('/products')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'فشل في حفظ البيانات')
    }
  }

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            {editMode ? 'تعديل المنتج' : 'إضافة منتج جديد'}
            <span className="text-xs bg-amazon-orange/20 text-amazon-orange px-2 py-1 rounded">Bilingual Enabled</span>
          </h1>
          <p className="text-gray-400 mt-1">
            {editMode ? `تعديل SKU: ${editProduct.sku}` : 'أدخل بيانات المنتج بالعربية والإنجليزية للرفع العالمي'}
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1a1a2e] p-6 rounded-xl border border-gray-800">
          <label className="block text-sm font-medium text-gray-400 mb-3">السعر (EGP) *</label>
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