export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">الإعدادات</h1>
        <p className="text-gray-600 mt-1">إعدادات الحساب والنظام</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">معلومات الحساب</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">البريد الإلكتروني</label>
              <input type="email" className="w-full px-4 py-3 border border-gray-300 rounded-lg" defaultValue="demo@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Seller ID</label>
              <input type="text" className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50" defaultValue="demo-seller" readOnly />
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-gray-200">
          <button className="bg-amazon-orange hover:bg-amazon-light text-amazon-dark font-semibold px-6 py-3 rounded-lg transition-colors">
            حفظ التغييرات
          </button>
        </div>
      </div>
    </div>
  )
}
