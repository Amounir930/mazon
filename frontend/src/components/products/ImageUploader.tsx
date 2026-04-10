import { useState, useCallback, useRef } from 'react'
import { Image as ImageIcon, X, Star, GripVertical } from 'lucide-react'
import toast from 'react-hot-toast'

interface ImageUploaderProps {
  images: string[]
  onChange: (images: string[]) => void
  maxImages?: number
}

export function ImageUploader({ images, onChange, maxImages = 8 }: ImageUploaderProps) {
  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): boolean => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png']
    const maxSize = 5 * 1024 * 1024 // 5MB

    if (!validTypes.includes(file.type)) {
      toast.error('يُسمح فقط بملفات PNG و JPG')
      return false
    }

    if (file.size > maxSize) {
      toast.error('حجم الصورة يجب أن يكون أقل من 5 ميجابايت')
      return false
    }

    return true
  }

  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files)
    const remainingSlots = maxImages - images.length

    if (remainingSlots <= 0) {
      toast.error(`الحد الأقصى ${maxImages} صور`)
      return
    }

    const filesToProcess = fileArray.slice(0, remainingSlots)
    const newImages: string[] = []

    let processed = 0
    filesToProcess.forEach((file) => {
      if (!validateFile(file)) return

      const reader = new FileReader()
      reader.onload = () => {
        const base64 = reader.result as string
        newImages.push(base64)
        processed++

        if (processed === filesToProcess.length) {
          onChange([...images, ...newImages])
          toast.success(`تم إضافة ${newImages.length} صورة بنجاح`)
        }
      }
      reader.readAsDataURL(file)
    })
  }, [images, onChange, maxImages])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files)
      e.target.value = '' // Reset input
    }
  }

  const removeImage = (index: number) => {
    const newImages = [...images]
    newImages.splice(index, 1)
    onChange(newImages)
  }

  const handleDragStart = (index: number) => {
    setDragIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (dragIndex === null || dragIndex === index) return

    const newImages = [...images]
    const draggedItem = newImages[dragIndex]
    newImages.splice(dragIndex, 1)
    newImages.splice(index, 0, draggedItem)

    onChange(newImages)
    setDragIndex(index)
  }

  const handleDragEnd = () => {
    setDragIndex(null)
  }

  const mainImage = images[0] || null
  const subImages = images.slice(1)

  return (
    <div className="space-y-6">
      {/* Main Image */}
      <div className="bg-[#1a1a2e] p-4 rounded-lg border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Star className="w-5 h-5 text-amazon-orange" />
          <span className="text-white font-semibold">الصورة الرئيسية</span>
          <span className="text-xs text-gray-500">(الصورة الأولى تلقائياً)</span>
        </div>

        {mainImage ? (
          <div className="relative group aspect-video max-w-md mx-auto">
            <img
              src={mainImage}
              alt="Main product image"
              className="w-full h-full object-cover rounded-lg border-2 border-amazon-orange"
            />
            <button
              onClick={() => removeImage(0)}
              className="absolute top-2 right-2 p-2 bg-red-500 hover:bg-red-600 text-white rounded-full transition-all opacity-0 group-hover:opacity-100"
              title="إزالة الصورة الرئيسية"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="aspect-video max-w-md mx-auto border-2 border-dashed border-gray-700 hover:border-amazon-orange rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors bg-[#0a0a0f]"
          >
            <ImageIcon className="w-12 h-12 text-gray-600 mb-2" />
            <p className="text-gray-400 text-sm">انقر لاختيار الصورة الرئيسية</p>
          </div>
        )}
      </div>

      {/* Sub Images Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-gray-400" />
            <span className="text-white font-semibold">الصور الفرعية</span>
            <span className="text-xs text-gray-500">({subImages.length}/{maxImages - 1})</span>
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={images.length >= maxImages}
            className="px-4 py-2 bg-amazon-orange hover:bg-amazon-light text-amazon-dark text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            + إضافة صور
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {subImages.map((img, index) => (
            <div
              key={index}
              draggable
              onDragStart={() => handleDragStart(index + 1)}
              onDragOver={(e) => handleDragOver(e, index + 1)}
              onDragEnd={handleDragEnd}
              className={`relative group aspect-square rounded-lg overflow-hidden border-2 transition-all cursor-move ${
                dragIndex === index + 1
                  ? 'border-amazon-orange scale-105'
                  : 'border-gray-800 hover:border-gray-600'
              }`}
            >
              <img
                src={img}
                alt={`Sub image ${index + 1}`}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeImage(index + 1)
                  }}
                  className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors"
                  title="إزالة"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="absolute top-1 left-1 p-1 bg-gray-900/80 rounded text-xs text-white flex items-center gap-1">
                <GripVertical className="w-3 h-3" />
                {index + 2}
              </div>
            </div>
          ))}

          {/* Add more slots */}
          {Array.from({ length: maxImages - 1 - subImages.length }).map((_, idx) => (
            <div
              key={`empty-${idx}`}
              onClick={() => fileInputRef.current?.click()}
              className="aspect-square border-2 border-dashed border-gray-700 hover:border-amazon-orange rounded-lg flex flex-col items-center justify-center cursor-pointer transition-colors bg-[#0a0a0f]"
            >
              <ImageIcon className="w-8 h-8 text-gray-600 mb-2" />
              <p className="text-xs text-gray-500">+ إضافة</p>
            </div>
          ))}
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/jpg,image/png"
        multiple
        onChange={handleFileInput}
        className="hidden"
      />

      {images.length > 0 && (
        <div className="text-xs text-gray-500 text-center">
          إجمالي الصور: {images.length} | الصورة الأولى هي الرئيسية | اسحب الصور لإعادة الترتيب
        </div>
      )}
    </div>
  )
}
