import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Package, DollarSign, Image, Settings, Layers, Save } from 'lucide-react'
import toast from 'react-hot-toast'

const tabs = [
  { id: 'basic', label: 'المعلومات الأساسية', icon: Package },
  { id: 'pricing', label: 'التسعير والمخزون', icon: DollarSign },
  { id: 'media', label: 'الصور والوسائط', icon: Image },
  { id: 'advanced', label: 'الخصائص المتقدمة', icon: Settings },
  { id: 'multi', label: 'الإعلانات المتعددة', icon: Layers },
]

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('basic')

  const handleSubmit = () => {
    toast.success('تم حفظ المنتج بنجاح')
    navigate('/products')
  }

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">إضافة منتج جديد</h1>
          <p className="text-gray-600 mt-1">أدخل بيانات المنتج لرفعه على أمازون</p>
        </div>
        <button
          onClick={handleSubmit}
          className="flex items-center gap-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold px-6 py-3 rounded-lg transition-colors"
        >
          <Save className="w-5 h-5" />
          حفظ المنتج
        </button>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === id
                  ? 'text-amazon-orange border-b-2 border-amazon-orange'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'basic' && <BasicInfoTab />}
          {activeTab === 'pricing' && <PricingTab />}
          {activeTab === 'media' && <MediaTab />}
          {activeTab === 'advanced' && <AdvancedTab />}
          {activeTab === 'multi' && <MultiListingTab />}
        </div>

        {/* Navigation */}
        <div className="flex justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={() => {
              const idx = tabs.findIndex((t) => t.id === activeTab)
              if (idx < tabs.length - 1) setActiveTab(tabs[idx + 1].id)
            }}
            className="flex items-center gap-2 text-amazon-orange font-medium hover:underline"
          >
            التبويب التالي
            <ArrowRight className="w-4 h-4 rotate-180" />
          </button>
        </div>
      </div>
    </div>
  )
}

function BasicInfoTab() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">SKU *</label>
          <input type="text" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="SKU-001" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">اسم المنتج *</label>
          <input type="text" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="اسم المنتج" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">الوصف</label>
        <textarea rows={4} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="وصف المنتج..." />
      </div>
    </div>
  )
}

function PricingTab() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">السعر *</label>
          <input type="number" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="0.00" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">الكمية</label>
          <input type="number" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="0" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">الوزن (كجم)</label>
          <input type="number" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="0.0" />
        </div>
      </div>
    </div>
  )
}

function MediaTab() {
  return (
    <div className="space-y-4">
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-amazon-orange transition-colors cursor-pointer">
        <Image className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">اسحب الصور هنا أو انقر للاختيار</p>
        <p className="text-sm text-gray-500 mt-2">حتى 8 صور (PNG, JPG)</p>
      </div>
    </div>
  )
}

function AdvancedTab() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">اللون</label>
          <input type="text" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">الحجم</label>
          <input type="text" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" />
        </div>
      </div>
    </div>
  )
}

function MultiListingTab() {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">عدد الإعلانات</label>
        <input type="number" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amazon-orange" placeholder="1" defaultValue={1} />
      </div>
      <p className="text-sm text-gray-600">يمكنك إنشاء عدة إعلانات لنفس المنتج مع تغييرات طفيفة في العنوان والسعر</p>
    </div>
  )
}
