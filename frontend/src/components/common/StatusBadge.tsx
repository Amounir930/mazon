interface StatusBadgeProps {
  status: string
}

const statusConfig: Record<string, { label: string; className: string }> = {
  draft: { label: 'مسودة', className: 'bg-gray-100 text-gray-700' },
  queued: { label: 'في الطابور', className: 'bg-yellow-100 text-yellow-700' },
  processing: { label: 'قيد المعالجة', className: 'bg-blue-100 text-blue-700' },
  submitted: { label: 'تم الإرسال', className: 'bg-purple-100 text-purple-700' },
  published: { label: 'منشور', className: 'bg-green-100 text-green-700' },
  success: { label: 'نجح', className: 'bg-green-100 text-green-700' },
  failed: { label: 'فشل', className: 'bg-red-100 text-red-700' },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, className: 'bg-gray-100 text-gray-700' }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
