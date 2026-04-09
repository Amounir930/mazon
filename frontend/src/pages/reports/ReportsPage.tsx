import { Download, FileText } from 'lucide-react'

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">التقارير</h1>
        <p className="text-gray-600 mt-1">تصدير ومتابعة نتائج الرفع</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <FileText className="w-10 h-10 text-amazon-orange mb-4" />
          <h3 className="text-lg font-semibold text-gray-800">تقرير CSV</h3>
          <p className="text-sm text-gray-600 mt-2">تصدير جميع النتائج بتنسيق Excel</p>
          <button className="mt-4 flex items-center gap-2 text-amazon-orange font-medium hover:underline">
            <Download className="w-4 h-4" />
            تصدير
          </button>
        </div>
      </div>
    </div>
  )
}
