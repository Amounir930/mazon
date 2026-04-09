export default function ListingQueuePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">طابور الرفع</h1>
          <p className="text-gray-600 mt-1">متابعة حالة رفع المنتجات لأمازون</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold rounded-lg transition-colors">
            رفع الكل
          </button>
          <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            تحديث
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
        <p className="text-gray-500">الطابور فارغ</p>
        <p className="text-sm text-gray-400 mt-2">أضف منتجات من صفحة المنتجات لبدء الرفع الآلي</p>
      </div>
    </div>
  )
}
