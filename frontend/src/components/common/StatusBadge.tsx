interface StatusBadgeProps {
  status: string
}

const statusConfig: Record<string, { label: string; className: string; dotColor: string }> = {
  draft: { label: 'مسودة', className: 'bg-bg-elevated/50 text-text-secondary border border-border-subtle', dotColor: 'bg-text-muted' },
  incomplete: { label: 'ناقص بيانات', className: 'bg-neon-yellow/10 text-neon-yellow border border-neon-yellow/20', dotColor: 'bg-neon-yellow' },
  queued: { label: 'في الطابور', className: 'bg-neon-orange/10 text-neon-orange border border-neon-orange/20', dotColor: 'bg-neon-orange' },
  processing: { label: 'قيد المعالجة', className: 'bg-neon-blue/10 text-neon-blue border border-neon-blue/20', dotColor: 'bg-neon-blue' },
  submitted: { label: 'تم الإرسال', className: 'bg-neon-purple/10 text-neon-purple border border-neon-purple/20', dotColor: 'bg-neon-purple' },
  published: { label: 'منشور', className: 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20', dotColor: 'bg-neon-cyan' },
  success: { label: 'نجح', className: 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20', dotColor: 'bg-neon-cyan' },
  failed: { label: 'فشل', className: 'bg-neon-red/10 text-neon-red border border-neon-red/20', dotColor: 'bg-neon-red' },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, className: 'bg-bg-elevated/50 text-text-secondary border border-border-subtle', dotColor: 'bg-text-muted' }

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${config.className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor}`}></span>
      {config.label}
    </span>
  )
}
