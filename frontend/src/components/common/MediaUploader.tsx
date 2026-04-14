import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Image as ImageIcon, X, Loader2 } from 'lucide-react'

interface MediaUploaderProps {
  images: string[]
  onChange: (images: string[]) => void
}

export function MediaUploader({ images, onChange }: MediaUploaderProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      const reader = new FileReader()
      reader.onload = () => {
        const base64 = reader.result as string
        onChange([...images, base64])
      }
      reader.readAsDataURL(file)
    })
  }, [images, onChange])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
    maxFiles: 8
  })

  const removeImage = (index: number) => {
    const newImages = [...images]
    newImages.splice(index, 1)
    onChange(newImages)
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`neon-dropzone ${isDragActive ? 'border-amazon-orange bg-amazon-orange/5' : ''}`}
      >
        <input {...getInputProps()} />
        <ImageIcon className="w-12 h-12 neon-dropzone__icon" />
        <p className="text-text-secondary">
          {isDragActive ? 'اترك الصور هنا' : 'اسحب الصور هنا أو انقر للاختيار'}
        </p>
        <p className="text-sm text-text-muted">حتى 8 صور (PNG, JPG, WebP)</p>
      </div>

      {images.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-6">
          {images.map((img, index) => (
            <div key={index} className="relative group aspect-square rounded-xl overflow-hidden border border-border-subtle hover:border-border-medium transition-colors">
              <img src={img} alt={`Upload ${index}`} className="w-full h-full object-cover" />
              <button
                onClick={(e) => { e.stopPropagation(); removeImage(index) }}
                className="absolute top-2 right-2 p-1.5 bg-neon-red/90 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-neon-red"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
