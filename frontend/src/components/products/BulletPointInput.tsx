import { useState } from 'react'
import { Plus, X, Check } from 'lucide-react'
import toast from 'react-hot-toast'

interface BulletPointInputProps {
  bulletPoints: string[]
  onChange: (bullets: string[]) => void
  maxPoints?: number
  placeholder?: string
  label?: string
}

export function BulletPointInput({
  bulletPoints,
  onChange,
  maxPoints = 5,
  placeholder = '',
  label = 'مميزات المنتج'
}: BulletPointInputProps) {
  const [newBullet, setNewBullet] = useState('')

  const addBullet = () => {
    const trimmed = newBullet.trim()
    if (!trimmed) { toast.error('يرجى إدخال نص الميزة'); return }
    if (bulletPoints.length >= maxPoints) { toast.error(`الحد الأقصى ${maxPoints} نقاط`); return }
    onChange([...bulletPoints, trimmed])
    setNewBullet('')
    toast.success('تم إضافة الميزة بنجاح')
  }

  const removeBullet = (index: number) => {
    const newBullets = [...bulletPoints]
    newBullets.splice(index, 1)
    onChange(newBullets)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') { e.preventDefault(); addBullet() }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Check className="w-5 h-5 text-amazon-orange" />
          <span className="text-text-primary font-semibold">{label}</span>
          <span className="text-xs text-text-muted">({bulletPoints.length}/{maxPoints})</span>
        </div>
      </div>

      {/* Input area */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newBullet}
          onChange={(e) => setNewBullet(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={placeholder || 'أضف ميزة جديدة...'}
          className="neon-input flex-1"
          disabled={bulletPoints.length >= maxPoints}
        />
        <button
          onClick={addBullet}
          disabled={bulletPoints.length >= maxPoints || !newBullet.trim()}
          className="neon-btn neon-btn--amazon disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-5 h-5" /> إضافة
        </button>
      </div>

      {/* Bullet points list */}
      {bulletPoints.length > 0 && (
        <ul className="space-y-3">
          {bulletPoints.map((bullet, index) => (
            <li
              key={index}
              className="bg-bg-elevated/50 p-4 rounded-xl border border-border-subtle flex items-start gap-3 group hover:border-border-medium transition-colors"
            >
              <div className="flex-shrink-0 w-6 h-6 bg-amazon-orange/20 text-amazon-orange rounded-full flex items-center justify-center text-sm font-bold">
                {index + 1}
              </div>
              <p className="flex-1 text-text-primary text-sm leading-relaxed">{bullet}</p>
              <button
                onClick={() => removeBullet(index)}
                className="flex-shrink-0 p-1 text-text-muted hover:text-neon-red hover:bg-neon-red/10 rounded transition-colors opacity-0 group-hover:opacity-100"
                title="إزالة"
              >
                <X className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {bulletPoints.length === 0 && (
        <div className="text-center py-8 text-text-muted text-sm">
          لم يتم إضافة أي ميزات بعد. استخدم الحقل أعلاه لإضافة أول ميزة.
        </div>
      )}

      <div className="text-xs text-text-muted text-center">
        الحد الأقصى: {maxPoints} نقاط | يُنصح بكتابة ميزات واضحة ومختصرة
      </div>
    </div>
  )
}
